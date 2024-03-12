
"""
    Name: 
        JRC_IACS_QA_v1
    Author: 
        Fernando Fahl
    Date:
         March 7, 2024
    Version: 
        1.0
    Description: 
        Tool to select inspection samples for the quality assessments (QA) of the Area Monitoring System (AMS) and GeoSpatial Application (GSA) 
    Usage: 
        python JRC_IACS_QA_v1
        Modify the file parameters.yaml accondingly
    Dependencies: 
        see file requirements.txt
"""


import os, time

from tqdm import tqdm
from datetime import datetime

import libs.data as ctr

def update_pbars(dt, bk, parcel_id, holding_id, ranking, intervention_id=None, bar='total'):

    try:
        if bar == 'total':     
            percentagem_holding_total_ = round(bk.n_holdings_selected / dt.n_holdings_unique_full * 100, 1)
            description_total = (f" ... {'TOTAL':<20} :: {'parcel ' + parcel_id:30.28} :: {'holding ' + holding_id:32} :: {'rank: ' + str(ranking):12} :: {'n_hol ' + str(bk.n_holdings_selected) + '/' + str(dt.n_holdings_unique_full):17} {'(' + str(percentagem_holding_total_) + '%)':8}" ) # 
            bk.update_total_pbars(description_total)
        else:
            total_holdings_         = dt.get_n_holdings_from_intervention(intervention_id)
            n_holdings_             = bk.get_n_holdings_from_intervention(intervention_id)
            percentagem_holding_    = round(n_holdings_ / total_holdings_ * 100, 1)

            description_intervention = (f" ... {'intervention: ' + str(intervention_id):20} :: {'parcel ' + parcel_id:30.28} :: {'holding ' + holding_id:32} :: {'rank: ' + str(ranking):12} :: {'n_hol ' + str(n_holdings_) + '/' + str(total_holdings_):17} {'(' + str(percentagem_holding_) + '%)':8}" ) # 
            bk.update_intervention_pbars(intervention_id, description_intervention)
    except:
        print (f" ... {'intervention_id ' + str(intervention_id):25} {'parcel ' + parcel_id:28} :: {'holding ' + holding_id:32} :: {'rank: ' + str(ranking):12} " ) # 
        pass

def bucket_control(bk):

    # _______________ Bucket control
    bk.check_bucket_status()  

    if bk.bucket_complete is True:
        bk.log(f" ... Bucket Full - end of the process", level='warning') 
        return True
    else:
        return False


def add_parcel_to_bucket(dt, bk, holding_id, intervention_id, parcel_id, intervention_target, covered, ranking, counter=[0]):
           
    # _____________ Skip the parcel if it has been already added to the bucket
    if bk.get_parcel_in_bucket(intervention_id, parcel_id):
        return False        
   
    # _____________ Update bucket
    else:           
        counter[0] +=1

        bk.add_parcel_to_bucket(intervention_id, parcel_id,  holding_id, covered, ranking, intervention_target, counter[0], dt.data_source) 
        bk.update_buckets(intervention_id, parcel_id, holding_id)
   
        # _____________ Update progress bars
        update_pbars(dt, bk, parcel_id, holding_id, ranking, intervention_id, bar='intervention_id')
  

def loop_03_intervention(dt, bk, holding_id, intervention_ids, parcel_id_master, parcel_id_hl, covered_master, ranking_master, counter=[0]):

    interventions_completed_ = bk.get_interventions_completed() 
    intervention_remaning_   = [i for i in intervention_ids if i not in interventions_completed_ ]


    for intervention_id_ in intervention_remaning_:  
  
        # _______________ Get data
        intervention_target_     = dt.intervention_targets.get(intervention_id_)
        n_parcels_intervention_  = bk.get_n_parcels_from_intervention(intervention_id_) 
        holding_status_          = bk.get_bucket_holding_status(intervention_id_, holding_id)
        intervention_ids_master_ = dt.get_intervention_ids_from_parcel(holding_id=holding_id, parcel_id=parcel_id_master)

        # _______________ Bucket control
        bk.check_bucket_status()                      
        if bk.bucket_complete is True:
            return
 
        # _______________ Modify the intervention status if the target limit has been reached
        if n_parcels_intervention_ >= intervention_target_:                 
            bk.change_bucket_intervention_status(intervention_id_, completed=True)
            continue  

        # _______________ Add parcel to the bucket if holding is not completed (parcel from holding selection)
        if holding_status_ is not True :

            covered_  = dt.get_df_column_value(holding_id, parcel_id_hl, column='covered')
            ranking_  = dt.get_df_column_value(holding_id, parcel_id_hl, column='ranking')                        
    
            add_parcel_to_bucket(dt, bk, holding_id, intervention_id_, parcel_id_hl, intervention_target_, covered_, ranking_)

            continue
         
        # _______________ Add parcel parcel directly to the bucket  (parcel from loop 1)
        elif holding_status_ is True and intervention_id_ in intervention_ids_master_:    
            add_parcel_to_bucket(dt, bk, holding_id, intervention_id_, parcel_id_master, intervention_target_, covered_master, ranking_master) 
        else:
            pass


def loop_02_holdings(dt, bk, holding_id, parcel_id_master, covered_master, ranking_master, parcel_ids_from_holding):    

    for parcel_id_hl_ in parcel_ids_from_holding:

        # _______________ Bucket control
        if bucket_control(bk) is True:
            return
        
        # _______________ Get the intervention ids from parcel
        intervention_ids_   = dt.get_intervention_ids_from_parcel(holding_id=holding_id, parcel_id=parcel_id_hl_)

        # _______________ Loop through the intervention ids
        if intervention_ids_: 
            loop_03_intervention(dt, bk, holding_id, intervention_ids_, parcel_id_master, parcel_id_hl_, covered_master, ranking_master) 


def loop_01_parcels(dt, bk, counter=[0]):    


    for idx, row in dt.data.iterrows():

        holding_id_, parcel_id_master_       = idx  
        ranking_master_                      = int(row['ranking'])
        covered_master_                      = row['covered']
 
        # _______________ Bucket control
        if bucket_control(bk) is True:   
            return      

        # _______________ Get parcel ids from holding id
        parcel_ids_from_holding_ = dt.get_parcel_ids_from_holding(holding_id_)
        parcel_ids_from_bucket_  = bk.get_parcels_in_holding(holding_id_)
        parcel_ids_remaning_     = [i for i in parcel_ids_from_holding_ if i not in parcel_ids_from_bucket_ ]

        # _______________ Skip if the parcel ids are already on bucket
        if len(parcel_ids_remaning_) == 0:
            continue

        # _______________ Loop through the parcel ids of a given holding id
        loop_02_holdings(dt, bk, holding_id_, parcel_id_master_, covered_master_, ranking_master_, parcel_ids_from_holding_)

        # _______________ Percentagem control
        if bk.percentagem_limit is True and dt.data_source == 'full':
            return bk.percentagem_limit 
        
        # _______________ Save temporary files (for debugging)
        counter[0] +=1
        if bk.temp_files is True and counter[0] > 100:
            counter[0] = 0

        # _______________ Update total progress bar
        update_pbars(dt, bk, parcel_id_master_, holding_id_, ranking_master_, bar='total')


    else:
        return False


def main():
    
    os.system('cls||clear')

    # _________________ loop over all parcels
    for country in ctr.Data().countries:

        start_time    =  time.time() 
        
        try:
            del dt
            del bk
        except:
            pass

        print (f"\n____________________ Country: {country} ____________________\n") 

        # _______________ Load data from database
        dt = ctr.Data()
        dt.initiate_country(country)
        dt.load_db_data()
       

        # print (dt)
 
        # _______________ Create empty buckets
        bk = ctr.Bucket(country, dt.intervention_targets, dt.n_holdings_allowed)
        bk.create_buckets()     
        bk.set_log()      

        # _______________ Initialize progression bars
        bk.set_pbars(dt.intervention_targets, dt.n_parcels_target)

        # _______________ Analyse of full dataset
        while bk.percentagem_limit is False:  # change the dataframe based on holding percentage status  

            dt.data_source = 'full'
      
            message = f" ... {'Starting the analysis of full data':40} :: n_rows: {dt.n_rows:<5} :: n_parcels: {dt.n_parcels_unique_full:<5} :: n_holdings: {dt.n_holdings_unique_full:<5} :: n_interventions: {dt.n_intervention_unique_not_null:<5}"
            bk.log(message)

            # _______________ Loop 1 (parcel ids)
            status_ = loop_01_parcels(dt, bk)    
 
            # _______________ Bucket control
            if bucket_control(bk) is True:
                break      

        # _______________ Analyse of partial dataset: condition when the number of holdings has reached the percentagem limit
        else:

            # _______________ Slice the dataframe with the selected holding ids from previous section: output is a constrained dataset
            dt.select_df_from_holding_ids(bk.holding_ids_select, bk.bucket)
            dt.data_source = 'constrained'

            # _______________ Log
            message = f" ... {'Starting the analysis of partial data':40} :: n_rows: {dt.n_rows:<5} :: n_parcels: {dt.n_parcels_unique_constrained:<5} :: n_holdings: {dt.n_holdings_unique_constrained:<5} :: n_interventions: {dt.n_intervention_unique_not_null:<5}"                      
            bk.log(message)
     
            # _______________ Loop 1 (parcel ids)
            status_ = loop_01_parcels(dt, bk)              

            # _______________ Bucket control
            if bucket_control(bk) is True: 
                break   

            # _______________ Holdingd percentagem control
            if status_ is False:
                message = f" ... The holding_percentage at {dt.holding_percentage_value * 100}% does not produce enough results  "
                bk.log (message, level='warning')             

          
        # _______________ End of processing
        total_time_ = round((time.time() - start_time) / 60,2)             

        message = f" ... {'END: Total processing time = ' + str(total_time_) + ' min':40} "                       
        # :: n_rows: {bk.n_rows_bucket:<5} :: n_parcels: {bk.n_parcels_unique_bucket:<5} :: n_holdings: {bk.n_holdings_unique_bucket:<5} :: n_interventions: {bk.n_intervention_unique_bucket:<5}
        bk.log(message, level='info') 

        bk.close_process(dt, total_time_)





if __name__ == "__main__":
    main()
