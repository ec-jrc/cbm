import time
import pandas as pd
import numpy as np
import psycopg2 as ps
from tqdm.auto import tqdm
from numpy import nan 

import logging
import logging.handlers

from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Tuple, Union, Optional, ClassVar

import libs.utils as utl
import libs.db_queries as sql

import warnings
warnings.filterwarnings('ignore')


class Base():

    params:dict          = utl.load_yaml('parameters.yaml') 
    countries            = params.get('countries') 
    constraints:dict     = params.get('constraints')

    # Parameters
    intervention_target_status      = constraints.get('intervention_target').get('active')
    intervention_target_max         = constraints.get('intervention_target').get('max')

    holding_target_status           = constraints.get('holding_target').get('active')
    holding_target_max              = constraints.get('holding_target').get('max')

    holding_percentage_status       = constraints.get('holding_percentage').get('active')
    holding_percentage_value        = constraints.get('holding_percentage').get('max')

    image_coverage_status           = constraints.get('image_coverage').get('active')

    temp_files                      = params.get('output').get('temporary')


    def __init__(self, country):  

        self.country = country  
    
        self.set_paths() 
        self.set_output_files()
        # self.set_log()

    def get_country(self):
        return self.country

    def set_paths(self):

        path_       = self.params.get('output').get('path')
        cwd_        = Path(__file__).parent.parent.absolute()

        # relative or absolute path
        if str(path_).startswith('./'):    
            self.output_folder = cwd_.joinpath(path_)
        else:
            self.output_folder = Path(path_)

        self.tmp_folder = cwd_.joinpath('tmp', self.country.upper())

        utl.create_folder(self.output_folder)
        utl.create_folder(self.tmp_folder)

    def set_output_files(self, file_format='csv'):        

        today_                       = datetime.today().strftime('%Y-%m-%d')   
        self.file_name_csv          = f"{self.country.upper()}_{self.params.get('output').get('suffix')}_{today_}.{file_format}"
        self.file_name_xls          = f"{self.country.upper()}_{self.params.get('output').get('suffix')}_{today_}.xlsx"
        self.file_name_intervention = f"{self.country.upper()}_{self.params.get('output').get('suffix')}_INTERVENTION_{today_}.{file_format}"
        self.file_name_holding      = f"{self.country.upper()}_{self.params.get('output').get('suffix')}_HOLDING_{today_}.{file_format}"
        self.file_name_status       = f"{self.country.upper()}_{self.params.get('output').get('suffix')}_STATUS_{today_}.{file_format}"
        self.file_name_parcel       = f"{self.country.upper()}_{self.params.get('output').get('suffix')}_PARCEL_{today_}.{file_format}"
   
        self.log_name               = f"{self.params.get('output').get('suffix')}_{today_}.log" #{self.country.upper()}_

        self.output_file_csv           = self.tmp_folder.joinpath(self.file_name_csv)
        self.output_file_xls           = self.output_folder.joinpath(self.file_name_xls)
        self.output_file_intervention  = self.tmp_folder.joinpath(self.file_name_intervention)
        self.output_file_holding       = self.tmp_folder.joinpath(self.file_name_holding) 
        self.output_file_status        = self.tmp_folder.joinpath(self.file_name_status)   
        self.output_file_parcel        = self.tmp_folder.joinpath(self.file_name_parcel)  

    def set_log(self):

        filename = f'./logs/{self.log_name}'
        logging.basicConfig(filename=filename,
                    filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

        self.logger = logging.getLogger(filename)
        self.logger.handlers = []
        self.logger.warning(f"Starting log for {self.country.upper()}")        


    def log(self, message, level='info'):

        if level == 'debug':
            self.logger.debug(message)  
        elif level == 'warning':
            self.logger.warning(message)  
        elif level == 'error':
            self.logger.error(message)  
        elif level == 'critical':
            self.logger.critical(message)  
        else:
            self.logger.info(message)

    def close_logs(self):

        handlers = self.logger.handlers[:]
        for handler in handlers:
            self.logger.removeHandler(handler)
            handler.close()

    def __str__(self):
        return  '\n' + '\n'.join((f'{key:<40}: {value}' for key, value in self.__dict__.items()))


class Data(Base):

    countries                       = Base.countries

    # database
    db:dict                         = Base.params.get('database')  
    db_connection:dict              = db.get('connection') 
    db_table_names:dict             = db.get('table_names') 
    db_column_names:dict            = db.get('column_names')      
    conn                            = utl.connect_db(db_connection) 

    # parameters
    intervention_target_status      = Base.intervention_target_status
    intervention_target_max         = Base.intervention_target_max

    holding_target_status           = Base.holding_target_status
    holding_target_max              = Base.holding_target_max

    holding_percentage_status       = Base.holding_percentage_status
    holding_percentage_value        = Base.holding_percentage_value

    image_coverage_status           = Base.image_coverage_status

    def __init__(self):


        # Dataset
        self._data                           = None
        self._data_source                    = 'full' # it can be full or partial
        self.n_rows                          = None

        # Holdings (farmer)
        self.n_holdings_unique_full          = None
        self.n_holdings_unique_filtered      = None
        self.n_holdings_unique_constrained   = None   
        self.n_holdings_allowed              = None

        # Parcels
        self.n_parcels_target                = None 
        self.n_parcels_unique_full           = None
        self.n_parcels_unique_filtered       = None
        self.n_parcels_unique_constrained    = None

        # Interventions (schema)
        self.intervention_targets            = dict()
        self.intervention_unique_full        = list()
        self.intervention_unique_not_null    = list()
        self.n_intervention_unique_full      = None 
        self.n_intervention_unique_not_null  = None 

    # ___________ Properties
    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, df):        
        self._data      = df
        self.n_rows     = df.shape[0]

    @property
    def data_source(self):
        return self._data_source

    @data_source.setter
    def data_source(self, status='full'):

        self._data_source = status

        if self._data_source == 'full':
            self.data = self.df_data_aggregated
        else:
            self.data = self.df_data_constrained     

    # ___________ Methods

    def initiate_country(self, country):
        
        super().__init__(country)
        self.holding_percentage_value  = self.constraints.get('holding_percentage').get('max')

    def load_db_data(self):

        # ___________ load data from DB
        df_data_full_       = sql.get_data_from_country(self.conn, self.country, self.db_column_names, self.db_table_names)
        df_targets_full     = sql.get_country_intervention_targets(self.conn, self.country, self.db_column_names, self.db_table_names)

        # ___________ remove targets = 0
        df_targets_not_null_ = df_targets_full[df_targets_full['target'] > 0]    

        # ___________ get intervention targets
        if self.intervention_target_status:
            max_value = self.intervention_target_max
            df_targets_not_null_['target'][df_targets_not_null_['target'] > max_value] = max_value 

        # ___________ get intervention ids (unique)
        intervention_targets_full_          = dict(zip(df_targets_full['intervention_id'], df_targets_full['target']))
        intervention_targets_not_null_      = dict(zip(df_targets_not_null_['intervention_id'], df_targets_not_null_['target']))

        self.df_targets                     = df_targets_not_null_

        self.intervention_targets           = dict(zip(self.df_targets['intervention_id'], self.df_targets['target']))
        self.intervention_unique_full       = list(intervention_targets_full_.keys())
        self.intervention_unique_not_null   = list(intervention_targets_not_null_.keys())

        # ___________ filter data by intervention ids (remove parcels with target == 0 )
        self.df_data_full = df_data_full_[df_data_full_['intervention_id'].isin(self.intervention_unique_not_null)] # remove internvention ids with target == 0 
        
        # ___________ filter coverage data (if active)
        if self.image_coverage_status:
            self.df_data_filtered = self.df_data_full[self.df_data_full['covered']] # remove internvention ids with target == 0
        else:
            self.df_data_filtered = self.df_data_full  

        # ___________ aggregate intervention ids as array (to remove duplicated entries)       
        self.df_data_filtered.sort_values(['ranking'], inplace=True)   
        self.df_data_aggregated = self.df_data_filtered.groupby(['holding_id','parcel_id', 'covered','ranking'],sort=False).agg({'intervention_id':lambda x: list(x)})

        self.df_data_aggregated.reset_index(inplace=True) # do not sort the data by ranking in this step as it will mess up the parcel order
        self.df_data_aggregated.set_index(['holding_id','parcel_id'], inplace=True) 

        # ___________ get the number of holdings per intervention
        df_ = self.df_data_full.copy()
        df_.reset_index(inplace=True)

        df_group_ = df_.groupby('intervention_id').agg({'holding_id': 'nunique'})
        df_group_.reset_index(inplace=True)        
        df_group_.rename(columns={'holding_id': 'n_holdings'}, inplace=True)
        df_group_.set_index(['intervention_id'], inplace=True)

        self.df_data_holdings_intervention = df_group_

        # ___________ do stats with the data
        self.set_stats_from_data() 

        # utl.save_csv(self.df_data_aggregated, 'TMP_MT_data_aggregated.csv')


    def set_stats_from_data(self):

        # Holdings 
        self.n_holdings_unique_full     = len(self.df_data_full.index.get_level_values('holding_id').unique().tolist()) 
        self.n_holdings_unique_filtered = len(self.df_data_filtered.index.get_level_values('holding_id').unique().tolist()) 

        # Parcels
        self.n_parcels_unique_full      = len(self.df_data_full.index.get_level_values('parcel_id').unique().tolist()) 
        self.n_parcels_unique_filtered  = len(self.df_data_filtered.index.get_level_values('parcel_id').unique().tolist())
        self.n_parcels_target           = sum(self.intervention_targets.values()) # number of parcels to be collected
                   
        # Interventions
        self.n_intervention_unique_full     = len(self.intervention_unique_full)  
        self.n_intervention_unique_not_null = len(self.intervention_unique_not_null)  
         
        # Holding constrained
        if self.holding_percentage_status:
            self.n_holdings_allowed     = int(round(self.n_holdings_unique_full * self.holding_percentage_value,0))
        else:
            self.n_holdings_allowed     = self.n_holdings_unique_full  

    def delete_dfs(self):

        del (self.df_data_full)        
        del (self.df_targets)
        del (self.df_data_filtered)
        del (self.df_data_aggregated)

    def get_df_column_value(self, holding_id, parcel_id, column):         
        return self.data.loc[(holding_id, parcel_id), column]   
    
    # ________________ Holdings
    def get_parcel_ids_from_holding(self, holding_id):

        df_ = self.data.copy()
        df_.reset_index(inplace=True)

        ids_ = df_[df_['holding_id'] == holding_id]['parcel_id'].unique().tolist()

        return ids_
   
    
    def select_df_from_holding_ids(self, holding_ids_selected, df_bucket): 

        index1_ = ['holding_id','parcel_id','intervention_id']
        index2_ = ['holding_id','parcel_id']

        # ____________ Get covered data
        df_data_filtered_ = self.df_data_filtered.copy()
        df_data_filtered_.reset_index(inplace=True)  

        # ____________ Get bucket data
        df_bucket_ = df_bucket.copy()
        df_bucket_.reset_index(inplace=True) 
        df_bucket_.set_index(index1_, inplace=True) 

        # ____________ Select data from covered based on a list of holding ids
        df_selected_ = df_data_filtered_.loc[df_data_filtered_['holding_id'].isin(holding_ids_selected)]
        df_selected_ = df_selected_.loc[df_selected_['intervention_id'].isin(self.intervention_unique_not_null)] 
        df_selected_.set_index(index1_, inplace=True) 

        # ____________ Remove data already added to the bucket
        df_drop_ = df_selected_.drop(df_bucket_.index) 
        df_drop_.reset_index(inplace=True) 

        # ____________ Aggregate the intervention ids
        df_data_aggregated_ = df_drop_.groupby(['holding_id','parcel_id', 'covered','ranking']).agg({'intervention_id':lambda x: list(x)})
        df_data_aggregated_.sort_values(['ranking'], inplace=True)
        df_data_aggregated_.reset_index(inplace=True) 
        df_data_aggregated_.set_index(index2_, inplace=True) 


        self.df_data_constrained = df_data_aggregated_

        self.n_holdings_unique_constrained = len(self.df_data_constrained.index.get_level_values('holding_id').unique().tolist()) 
        self.n_parcels_unique_constrained  = len(self.df_data_constrained.index.get_level_values('parcel_id').unique().tolist())
       
        # utl.save_csv(df_data_aggregated_, 'TMP_MT_data_aggregated.csv')

    # ________________ Intervention
    def get_intervention_ids_from_parcel(self, holding_id, parcel_id):

        try:
            return self.data.loc[(holding_id, parcel_id), 'intervention_id']   
        except:
            self.log (f'  error: holding_id {holding_id} parcel_id {parcel_id}')
            return None
    
    def get_n_holdings_from_intervention(self, intervention_id):
        return self.df_data_holdings_intervention.loc[intervention_id, 'n_holdings']


class Bucket(Base):

    # parameters
    intervention_target_status      = Base.intervention_target_status
    intervention_target_max         = Base.intervention_target_max

    holding_target_status           = Base.holding_target_status
    holding_target_max              = Base.holding_target_max

    holding_percentage_status       = Base.holding_percentage_status
    holding_percentage_value        = Base.holding_percentage_value

    image_coverage_status           = Base.image_coverage_status

    temp_files                      = Base.temp_files


    def __init__(self, country, intervention_targets, n_holdings_allowed):

        super().__init__(country)   

        self.intervention_targets           = intervention_targets
        # self.intervention_limit             = {id_: False for id_ in self.intervention_targets}

        self.n_holding_max                  = self.constraints.get('holding_target').get('max')
        self.n_holdings_allowed             = n_holdings_allowed

        self._percentagem_value             = 0
        self._percentagem_limit             = False               

        self.holding_ids_select             = list()
        self._n_holdings_selected           = len(self.holding_ids_select)

        self._bucket_complete               = False

        self.n_rows_bucket                  = None
        self.n_holdings_unique_bucket       = None
        self.n_parcels_unique_bucket        = None
        self.n_intervention_unique_bucket   = None


    # ________________ Properties

    @property
    def percentagem_limit(self):
        return self._percentagem_limit

    @percentagem_limit.setter
    def percentagem_limit(self, status):
        self._percentagem_limit = status

    @property
    def percentagem_value(self):        
        return self._percentagem_value

    @percentagem_value.setter
    def percentagem_value(self, value):
        self._percentagem_value = value

    # ______________
    @property
    def bucket_complete(self):
        return self._bucket_complete

    @bucket_complete.setter
    def bucket_complete(self, status):
        self._bucket_complete = status

    # ______________
    @property
    def n_holdings_selected(self):
        return self._n_holdings_selected

    @n_holdings_selected.setter
    def n_holdings_selected(self, value):
        self._n_holdings_selected = value

    # ________________ Bucket control

    def create_buckets(self):

        # main bucket
        index               = pd.MultiIndex.from_tuples([], names=['intervention_id','parcel_id'])
        columns_main        = ['holding_id', 'covered', 'ranking', 'n_intervention_parcels', 'n_holding_parcels', 'target', 'order', 'notes']
        self.bucket         = pd.DataFrame(columns=columns_main, index=index)           

        # holding bucket
        index_holding       = pd.MultiIndex.from_tuples([], names=['intervention_id','holding_id'])
        self.bucket_holding = pd.DataFrame(columns=['n_parcels', 'completed'], index=index_holding)
            
        # intervention bucket      
        self.bucket_intervention = pd.DataFrame(self.intervention_targets.items(), columns=['intervention_id','target']) 
        self.bucket_intervention.set_index('intervention_id', inplace = True)
        self.bucket_intervention['completed'] = False
        self.bucket_intervention['n_parcels'] = 0
        self.bucket_intervention['n_holdings'] = 0
        self.bucket_intervention['holding_ids'] = None
        self.bucket_intervention['completed'][self.bucket_intervention['target'] ==0 ] = True        

        if self.constraints.get('intervention_target').get('active'):
            self.bucket_intervention['target'][self.bucket_intervention['target'] > self.constraints.get('intervention_target').get('max')] = self.constraints.get('intervention_target').get('max')
 
    # ________________ Main bucket

    def add_parcel_to_bucket(self, intervention_id, parcel_id, holding_id, covered, ranking, target, order, note=None):

        self.bucket.loc[(intervention_id, parcel_id), 'holding_id'] = holding_id
        self.bucket.loc[(intervention_id, parcel_id), 'covered'] = covered
        self.bucket.loc[(intervention_id, parcel_id), 'ranking'] = ranking
        self.bucket.loc[(intervention_id, parcel_id), 'target'] = target
        self.bucket.loc[(intervention_id, parcel_id), 'order'] = order   
        self.bucket.loc[(intervention_id, parcel_id), 'notes'] = note   

    def update_bucket_counts(self, intervention_id, parcel_id, holding_id):

        self.bucket.loc[(intervention_id, parcel_id), 'n_intervention_parcels'] = self.get_n_parcels_from_intervention(intervention_id)
        self.bucket.loc[(intervention_id, parcel_id), 'n_holding_parcels']      = self.get_n_parcels_from_holding_and_intervention(intervention_id, holding_id)   

    def update_buckets(self, intervention_id, parcel_id, holding_id):

        self.update_bucket_holding(intervention_id, holding_id)                
        self.update_intervention_n_parcels(intervention_id,  self.intervention_targets[intervention_id])
        self.update_intervention_n_holdings(intervention_id, holding_id)
        self.update_bucket_counts(intervention_id, parcel_id, holding_id)
        self.update_holding_percentagem_status(holding_id)   

        # make sure all intervention status are set completed when reached the intervention target
        self.bucket_intervention.loc[self.bucket_intervention['n_parcels'] >= self.bucket_intervention['target'], 'completed'] = True


    def get_parcel_in_bucket(self, intervention_id, parcel_id):
        """ check if parcel is alreay in bucket """    

        if self.bucket.index.isin([(intervention_id, parcel_id)]).any(): # index exists
            return True
        else: # index does not exist
            return False
        
    def get_parcels_in_holding(self, holding_id):
        """ check if parcel is alreay in bucket """    

        return self.bucket.loc[self.bucket['holding_id'] == holding_id].index.get_level_values('parcel_id').tolist()

    def check_bucket_status(self):
        """ check if the bucked has been completed """

        if self.bucket_intervention['completed'].all():
            self.bucket_complete = True
        else:
            self.bucket_complete = False        

    # ________________ Holding bucket 
    def update_bucket_holding(self, intervention_id,  holding_id):

        if self.bucket_holding.index.isin([(intervention_id, holding_id)]).any(): # index exists
            self.bucket_holding.loc[(intervention_id, holding_id), 'n_parcels'] += 1
        else: # index does not exist
            self.bucket_holding.loc[(intervention_id, holding_id), 'n_parcels'] = 1

        # _____________ check if the holding has reached the allowed number 
        if self.get_n_parcels_from_holding_and_intervention(intervention_id,  holding_id)  >= self.n_holding_max:   
            self.change_bucket_holding_status(intervention_id, holding_id, completed=True) 
        else:
            self.change_bucket_holding_status(intervention_id, holding_id, completed=False) 

    def change_bucket_holding_status(self, intervention_id, holding_id, completed=True):
        self.bucket_holding.loc[(intervention_id, holding_id), 'completed'] = completed

    def get_n_parcels_from_holding_and_intervention(self, intervention_id, holding_id):

        if self.bucket_holding.index.isin([(intervention_id, holding_id)]).any(): # index exists
            return self.bucket_holding.loc[(intervention_id, holding_id), 'n_parcels']
        else:
            return -9999
        
    def check_interventions_by_holding(self, holding_id):

        df_ = self.bucket_holding.loc[(self.bucket_holding.index.get_level_values('holding_id') == holding_id) ]['completed']

        if df_.empty:
            return False
        else: 
            self.log(f" ... {df_.all()} {df_}", level='debug')
            return bool(df_.all())

    def update_holding_percentagem_status(self, holding_id):
        
        if len(self.holding_ids_select) < self.n_holdings_allowed:  
            self.percentagem_limit = False
            self.update_holding_selected_list(holding_id)
            self.n_holdings_selected = len(self.holding_ids_select)    
        else:
            self.percentagem_limit = True

        self.percentagem_value = int(round((self.n_holdings_selected / self.n_holdings_allowed * 100),0))

    def get_bucket_holding_status(self, intervention_id, holding_id): 

        if self.holding_target_status is False:
            return False
        else:
            if self.bucket_holding.index.isin([(intervention_id, holding_id)]).any(): # index exists    
                return self.bucket_holding.loc[(intervention_id, holding_id), 'completed']
        # else:
        #     return 0  

    def update_holding_selected_list(self, holding_id):  

        if holding_id not in self.holding_ids_select:
            self.holding_ids_select.append(holding_id)           

    # ________________ Intervention bucket

    def change_bucket_intervention_status(self, intervention_id, completed=True):
        self.bucket_intervention.loc[intervention_id, 'completed'] = completed



    def get_n_parcels_from_intervention(self, intervention_id):
        return self.bucket_intervention.loc[intervention_id, 'n_parcels']

    def get_n_holdings_from_intervention(self, intervention_id):
        return self.bucket_intervention.loc[intervention_id, 'n_holdings']
        
    def update_intervention_n_parcels(self, intervention_id, target):

        if self.bucket_intervention.index.isin([intervention_id]).any(): # index exists
            self.bucket_intervention.loc[(intervention_id), 'n_parcels'] += 1
        else: # index does not exist
            self.bucket_intervention.loc[(intervention_id), 'n_parcels'] = 1
            self.bucket_intervention.loc[(intervention_id), 'target'] = target  

    def update_intervention_n_holdings(self, intervention_id, holding_id):

        if self.bucket_intervention.index.isin([intervention_id]).any(): # index exists

            ids_ = self.bucket_intervention.loc[intervention_id, 'holding_ids']   

            if not ids_:
                ids_ = list([holding_id])
                self.bucket_intervention.loc[(intervention_id), 'holding_ids'] = ids_         
            else:                
                if holding_id not in ids_:
                    ids_.append(holding_id)      

            self.bucket_intervention.loc[(intervention_id), 'n_holdings'] = len(ids_)

    def get_interventions_completed(self):  
        return self.bucket_intervention.loc[self.bucket_intervention['completed']==True].index.tolist()

    # ________________ Progress bars   
            
    def set_pbars(self, intervention_targets, n_parcels_target):   

        bar_format='{desc:100} {percentage:3.0f}%|{bar:30}{r_bar}'

        self.pbars = dict()
        self.pbars[0] = tqdm(total=n_parcels_target, desc=f"TOTAL", position=0, bar_format=bar_format, colour='#6e2c00') # ascii=True, 

        sorted_ = dict(sorted(intervention_targets.items()))
        for i, intervention in enumerate(sorted_.items()):
            id_, target_ = intervention
            self.pbars[id_] = tqdm(total=target_, desc=f" ... Intervention: {id_}", position=i+1, bar_format=bar_format, leave=True, colour='#bdc3c7') 

    def update_intervention_pbars(self, intervention_id, description_intervention):

        self.pbars[intervention_id].set_description(description_intervention)
        self.pbars[intervention_id].update()
        self.pbars[0].update()
        self.pbars[intervention_id].refresh()

    def update_total_pbars(self, description_total):
        self.pbars[0].set_description(description_total)

    def close_pbars(self):

        try:
            for pbar_ in self.pbars.values():
                pbar_.close()
        except:
            pass

    # ________________ END of processing

    def delete_dfs(self):

        del (self.bucket)        
        del (self.bucket_holding)
        del (self.bucket_intervention)

    def export_bucket_csv(self):

        utl.save_csv(self.bucket, self.output_file_csv)
        utl.save_csv(self.bucket_intervention, self.output_file_intervention)
        utl.save_csv(self.bucket_holding, self.output_file_holding)

    def export_bucket_xls(self):

        df_ = self.bucket.copy()
        df_.reset_index(inplace=True)

        utl.create_new_xls(df_, self.output_file_xls , sheetname='data', index=False, overwrite=True)
        utl.add_sheet_to_xls(self.df_summary, self.output_file_xls, sheetname='summary', index=False)
        utl.add_sheet_to_xls(self.df_parameters, self.output_file_xls, sheetname='parameters', index=False)
        utl.add_sheet_to_xls(self.df_intervention_summary, self.output_file_xls, sheetname='interventions', index=True)

    def summarize_bucket(self, dt, total_time):

        self.n_rows_bucket                 = self.bucket.shape[0]

        self.n_holdings_unique_bucket      = len(self.bucket['holding_id'].unique().tolist()) 
        self.n_parcels_unique_bucket       = len(self.bucket.index.get_level_values('parcel_id').unique().tolist())
        self.n_intervention_unique_bucket  = len(self.bucket.index.get_level_values('intervention_id').unique().tolist()) 

        summary_ = {
     
            'unique holding ids': {
                'full dataset': dt.n_holdings_unique_full,
                'covered': dt.n_holdings_unique_filtered,
                # 'constrained': dt.n_holdings_unique_constrained,
                'bucket': self.n_holdings_unique_bucket,
                },
            'unique parcel ids': {
                'full dataset': dt.n_parcels_unique_full,
                'covered': dt.n_parcels_unique_filtered,
                # 'constrained': dt.n_parcels_unique_constrained,
                'bucket': self.n_parcels_unique_bucket,
                },
            'intervention ids': {
                'full dataset': dt.n_intervention_unique_full ,
                # 'filtered': dt.n_intervention_unique,
                # 'constrained': dt.n_intervention_unique,
                'target > 0': dt.n_intervention_unique_not_null ,
                'bucket': self.n_intervention_unique_bucket,
                }            
        }

        self.df_summary = pd.DataFrame.from_dict(summary_, orient='index')
        self.df_summary.reset_index(inplace=True)

        params_ = {
            'country': dt.country.upper(),
            'total processed time': f"{total_time} min",
            'intervention target active': self.intervention_target_status,
            'intervention target value': self.intervention_target_max,
            'holding target active': self.holding_target_status,
            'holding target value': self.holding_target_max,
            'holding percentage active': self.holding_percentage_status,
            'holding percentage value': f"{int(round(self.holding_percentage_value * 100, 0))} %",
            'image coverage active': self.image_coverage_status,  
        }

        self.df_parameters = pd.DataFrame({'parameter' : params_.keys() , 'value' : params_.values() })

        # __________________ summarize the intervention 
        df_int_  = self.bucket_intervention.copy()
          
        df_int_.drop(columns=['holding_ids', 'completed'], inplace=True)
        df_int_.sort_values('intervention_id', inplace=True)


        df_full_ = dt.df_data_holdings_intervention.copy()
        df_full_.reset_index(inplace=True)
        df_full_.rename(columns={'n_holdings': 'n_holdings_full'}, inplace=True)

        df_join_ = pd.merge(df_int_, df_full_, on='intervention_id', how='left')
        df_join_['%'] = round(df_join_['n_holdings'] / df_join_['n_holdings_full'] * 100,1)

  
        percentage_total_ = round(self.n_holdings_selected / dt.n_holdings_unique_full * 100,1)

        df_join_.loc[len(df_join_.index)] = ['ALL', 0, self.n_parcels_unique_bucket, self.n_holdings_selected, dt.n_holdings_unique_full, percentage_total_]
  
        self.df_intervention_summary = df_join_
        

    def close_process(self, dt, total_time):

        self.summarize_bucket(dt, total_time)
        self.export_bucket_csv()
        self.export_bucket_xls()
        self.close_pbars()

        dt.delete_dfs()
        self.delete_dfs() 

        # delete temporary folders
        if self.params.get('output').get('temporary') is False:
            utl.delete_folder(self.tmp_folder)

        self.close_logs()