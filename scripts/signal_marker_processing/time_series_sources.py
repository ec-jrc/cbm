#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Authors    : Daniele Borio, Fernando Urbano, Csaba WIRNHARDT
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import abc
import pandas as pd
import datetime
import numpy as np
import os
import gc
import psycopg2

import get_time_series as gts

"""
Summary :
    Classes for manipulating information related to time series.
    It allows one to load ad manipulate time series
"""

class base_time_series_source(metaclass = abc.ABCMeta) :
    """
    Summary :
        Abstract class defining the basic interfaces for all the derived
        classes. It defines a generic time series source
    """
    def __init__(self, signal_type : str) :
        """
        Summary :
            Object construtor.

        Arguments:
            signal_type - string defining the signal type associated to the
                          time_series_source

        Returns:
            Nothing.
        """
        self.type = signal_type

        self.components = None

    def get_signal_type(self) -> str :
        """
        Summary :
            Return the signal type (as a string) associated to a time series
            source.

        Arguments:
            None.

        Returns:
            The signal type.
        """
        return self.type

    @abc.abstractmethod
    def get_ts(self, fid : int, start_date : datetime.datetime, \
               stop_date : datetime.datetime) -> pd.DataFrame :
        """
        Summary :
            Return the time series associated to a specific fid (parcel
            identifier) for a given time range

        Arguments:
            fid - identifier of the parcel
            start_date - start date of the time series as datetime
            stop_date - stop date of the time series as datetime

        Returns:
            A pandas data frame
        """
        return

    def get_components(self) -> list :
        """
        Summary :
            Returns the components (list of strings) associated to the data
            frame returned by the time series source.

            Note that for specific time series souces, the returned list may
            be empty since components may determined only after the first call
            to the get_ts() function.

        Arguments :
            None.

        Returns:
            List of signal components.
        """

        if self.components is None :
            print("base_time_series_source - get_components(): Warning, empty"\
                  "component list. Try to make a call to get_ts() first")
            return [""]
        else :
            return self.components

class restful_s2_time_series_source(base_time_series_source) :
    """
    Summary :
        Time series source obtaining data using the restful API.
        Most of the operations performed in this class are based on the code
        from WIRNHARDT Csaba which is present in the "get_time_series.py" file.
    """
    def __init__(self, signal_type : str, connection_opt : dict, \
                 cloud_cat : list = [3,8,9,10,11]) :
        """
        Summary :
            Object constructor.

        Arguments:
            signal_type - string specifying the signal type
                          the string should be of the format bx_by_ndvi_...
                          used to specify which signals to retain

            connection_opt - dictionary with the options for connecting to the
                            Restful API

                            The dictionary has the following format:
                                {"ms" : , <- the member state
                                 "year" : , <- year of the data
                                 "api_user" : , <- username
                                 "api_pass" : , <- password
                                 "ptype" : <- type of database (m - mowing, g - grazing
                                                                or empty)
                                }

        Returns:
            Nothing.
        """
        super().__init__(signal_type)

        self.connection_opt = connection_opt

        self.cloud_cat = cloud_cat

        self.components = ['count', 'B02_mean', 'B02_std', 'cloud_pct', \
                           'B03_mean', 'B03_std', 'B04_mean', 'B04_std', \
                           'B05_mean', 'B05_std', 'B08_mean', 'B08_std', \
                           'B11_mean', 'B11_std', 'utm_number']

        return

    def get_ts(self, fid : int, start_date : datetime.datetime = datetime.datetime(2000,1,1), \
               stop_date : datetime.datetime = datetime.datetime(2000,1,1)) -> pd.DataFrame :
        """
        Summary :
            Return the time series associated to a specific fid (parcel
            identifier) for a given time range

        Arguments:
            fid - identifier of the parcel
            start_date - start date of the time series as datetime
            stop_date - stop date of the time series as datetime

        Returns:
            A pandas data frame

        Remark :
            If the start and the stop dates are not specified, all the available
            data are returned
        """

        # Call the restful API to get 'ALL' the related data
        _, ts, was_error = gts.get_extracted_data_from_restful( self.connection_opt["ms"],\
                             self.connection_opt["year"], fid,  self.connection_opt["api_user"],\
                             self.connection_opt["api_pass"],  "s2",\
                             self.connection_opt["ptype"])

        if was_error :
            return None

        # Now we need to recast the data
        ts_final = restful_s2_time_series_source.cast_data_frame(ts, self.cloud_cat)

        # Check if dates are set
        if (start_date != datetime.datetime(2000,1,1)) and \
           (stop_date != datetime.datetime(2000,1,1)) :

               dates = ts_final.index
               ind = (dates >= start_date) & (dates <= stop_date)
               ts_final = ts_final[ind]

        # Force garbage collection
        gc.collect()

        return ts_final

    @staticmethod
    def cast_data_frame( df, cloud_cat = [3,8,9,10,11] ) :
        """
        Summary :
            Function that re-organize the dataframe in a new dataframe indexed
            by respect to the different bands.
            This code is mainly based on the code of Csaba Wirnhardt.

        Arguments:
            df - input data frame to be reshape. The format provided by the
                restful API is assumed

        Returns:
            A new pandas data frame
        """
        # Remove duplicated values
        df.drop_duplicates(subset=['band','date_part','reference'], inplace = True)

        # First convert the epoch timestamp to a datetime
        df['date_part'] = df['date_part'].map(lambda e: datetime.datetime.fromtimestamp(e))
        df['cloud_pct'] = df['hist'].apply(lambda s: gts.get_cloudyness(s, cloud_cat)[1])

        # get the list of bands availables
        bands = np.unique(df['band'])

        df_final = None

        for band in bands :
            if df_final is None :
                df_final = df[df['band'] == band][['date_part','count','mean','std',\
                                                   'cloud_pct','reference']]
                df_final.rename(columns={'mean' : band + '_mean', \
                                         'std' : band + '_std'}, inplace=True)
            else :
                df_band = df[df['band'] == band][['mean', 'std', 'reference']].add_prefix(band + '_')
                df_band.rename(columns={band + '_reference' : 'reference'}, inplace=True)

                df_final = pd.merge(df_final, df_band, on = 'reference')


        # final check for removing duplicated values
        df_final.drop_duplicates(subset=['date_part'], inplace = True)
        df_final.set_index('date_part', inplace=True)

        df_final['utm_number'] = df_final['reference'].apply(lambda s: gts.get_utm_number_from_reference(s)).values
        df_final.drop('reference', inplace=True, axis=1)


        # Force garbage collection
        gc.collect()

        return df_final

class restful_s1_time_series_source(base_time_series_source) :
    """
    Summary :
        Time series source obtaining data using the restful API.
        Retrieve either BS or COH6 information
        Most of the operations performed in this class are based on the code
        from WIRNHARDT Csaba which is present in the "get_time_series.py" file.
    """
    def __init__(self, signal_type : str, connection_opt : dict, source_type = "c6") :
        """
        Summary :
            Object constructor.

        Arguments:
            signal_type - string specifying the signal type
                          the string should be of the format bx_by_ndvi_...
                          used to specify which signals to retain

            connection_opt - dictionary with the options for connecting to the
                            Restful API

                            The dictionary has the following format:
                                {"ms" : , <- the member state
                                 "year" : , <- year of the data
                                 "api_user" : , <- username
                                 "api_pass" : , <- password
                                 "ptype" : <- type of database (m - mowing, g - grazing
                                                                or empty)
                                }
            source_type - specifies if coherence ("c6") or back-scattering ("bs")
                          should be retrieved

        Returns:
            Nothing.
        """
        super().__init__(signal_type)

        self.connection_opt = connection_opt

        self.s1_type = source_type

        if source_type == "c6" :
            self.components = ['count', 'VHc_mean', 'VHc_std', 'orbit', 'VVc_mean', 'VVc_std']
        else :
            self.components = ['count', 'VHb_mean', 'VHb_std', 'orbit', 'VVb_mean', 'VVb_std']

        return

    def get_ts(self, fid : int, start_date : datetime.datetime = datetime.datetime(2000,1,1), \
               stop_date : datetime.datetime = datetime.datetime(2000,1,1)) -> pd.DataFrame :
        """
        Summary :
            Return the time series associated to a specific fid (parcel
            identifier) for a given time range

        Arguments:
            fid - identifier of the parcel
            start_date - start date of the time series as datetime
            stop_date - stop date of the time series as datetime

        Returns:
            A pandas data frame

        Remark :
            If the start and the stop dates are not specified, all the available
            data are returned
        """

        # Call the restful API to get 'ALL' the related data
        _, ts, was_error = gts.get_extracted_data_from_restful( self.connection_opt["ms"],\
                             self.connection_opt["year"], fid,  self.connection_opt["api_user"],\
                             self.connection_opt["api_pass"],  self.s1_type,\
                             self.connection_opt["ptype"])

        if was_error :
            return None

        # Now we need to recast the data
        ts_final = restful_s1_time_series_source.cast_data_frame(ts)

        # Check if dates are set
        if (start_date != datetime.datetime(2000,1,1)) and \
           (stop_date != datetime.datetime(2000,1,1)) :

               dates = ts_final.index
               ind = (dates >= start_date) & (dates <= stop_date)
               ts_final = ts_final[ind]

        # Force garbage collection
        gc.collect()

        return ts_final

    @staticmethod
    def cast_data_frame( df ) :
        """
        Summary :
            Function that re-organize the dataframe in a new dataframe indexed
            by respect to the different bands.
            This code is mainly based on the code of Csaba Wirnhardt.

        Arguments:
            df - input data frame to be reshape. The format provided by the
                restful API is assumed

        Returns:
            A new pandas data frame
        """
        # Remove duplicated values
        df.drop_duplicates(subset=['band','date_part','reference'], inplace = True)

        # First convert the epoch timestamp to a datetime
        if not np.issubdtype(df['date_part'].values.dtype, np.datetime64) :
            df['date_part'] = df['date_part'].map(lambda e: datetime.datetime.fromtimestamp(e))
            df['date_part'] = df['date_part'].apply(lambda s: s.date())
        # get the list of bands availables
        bands = np.unique(df['band'])

        df_final = None

        for band in bands :
            if df_final is None :
                df_final = df[df['band'] == band][['date_part','count','mean','std', 'orbit',\
                                                   'reference']]
                df_final.rename(columns={'mean' : band + '_mean', \
                                         'std' : band + '_std'}, inplace=True)
            else :
                df_band = df[df['band'] == band][['mean', 'std', 'reference']].add_prefix(band + '_')
                df_band.rename(columns={band + '_reference' : 'reference'}, inplace=True)

                df_final = pd.merge(df_final, df_band, on = 'reference')


        # final check for removing duplicated values
        df_final.drop_duplicates(subset=['date_part'], inplace = True)

        df_final.set_index('date_part', inplace=True)
        df_final.drop('reference', inplace=True, axis=1)

        # Force garbage collection
        gc.collect()

        return df_final


class csv_time_series_source(base_time_series_source) :
    """
    Summary :
        Time series source based on an external csv file
    """
    def __init__(self, signal_type : str, filename : str, fid_col : str = 'FID',\
                 date_ID : str = None) :
        """
        Summary :
            Object constructor.

        Arguments:
            signal_type - string specifying the signal type
            filename - string definying the path of the csv file used to initialize
                       the time series source
            fid_col - string indicating which column in the data frame should be used
                      to identify the FOI
            date_ID - specify the column with the date in the csv data frame

        Returns:
            Nothing.
        """

        # call the base class constructor
        super().__init__(signal_type)

        # check if the file is compressed
        if filename.split('.')[-1] == 'zip' :
            # load the csv file
            self.df = pd.read_csv(filename, compression='zip')
        else :
            # load the csv file
            self.df = pd.read_csv(filename)

        # record the column name with the FIDs
        self.fid_col = fid_col

        # look for the attribute with the date and rename it in a standard way
        if (date_ID is not None) and date_ID in self.df :
            self.df.rename(columns={date_ID:'Date'}, inplace = True)

        elif 'date' in self.df :
            self.df.rename(columns={'date':'Date'}, inplace = True)

        elif 'acq_date' in self.df :
            self.df.rename(columns={'acq_date':'Date'}, inplace = True)

        elif 'obsdate' in self.df :
            self.df.rename(columns={'obsdate':'Date'}, inplace = True)

        if 'Date' not in self.df :
            raise Exception("csv_time_series_source.__init__() : dates not found")

        self.components = list(self.df.columns)

    def get_ts(self, fid : int, start_date : datetime.datetime = datetime.datetime(2000,1,1), \
               stop_date : datetime.datetime = datetime.datetime(2000,1,1)) -> pd.DataFrame :
        """
        Summary :
            Return the time series associated to a specific fid (parcel
            identifier) for a given time range

        Arguments:
            fid - identifier of the parcel
            start_date - start date of the time series as datetime
            stop_date - stop date of the time series as datetime

        Returns:
            A pandas data frame

        Remark :
            If the start and the stop dates are not specified, all the available
            data are returned
        """

        # First isolate the elements related to the specific parcel (fid)
        # Make a copy to avoid 'touching' the originald data
        data = self.df[self.df[self.fid_col] == fid].copy()

        # convert the associated dates (strings) into datetime
        dates = pd.to_datetime(data['Date'].values)

        # Check if dates are set
        if (start_date != datetime.datetime(2000,1,1)) and \
           (stop_date != datetime.datetime(2000,1,1)) :

               ind = (dates >= start_date) & (dates <= stop_date)
               data = data[ind]
               dates = dates[ind]

        # If there are duplicated dates, keep only one date
        _, ind = np.unique(dates, return_index=True)
        data = data.iloc[ind]
        dates = dates[ind]

        # sort dataframe based on dates
        data['Date'] = dates
        data.sort_values(by=['Date'], inplace = True)
        data.set_index(['Date'], inplace=True)

        # Force garbage collection
        gc.collect()

        return data

class dir_csv_time_serie_source(base_time_series_source) :
    """
    Summary :
        Time series source based on several csv files stored inside directory
    """
    def __init__(self, signal_type : str, dirnames, fid_col : str, \
                 options : dict, date_ID : str = None ) :
        """
        Summary :
            Object constructor.

        Arguments:
            signal_type - string specifying the signal type
            dirnames - string or list definying the paths of the directory containing the
                      csv files used to initialize the time series source
            fid_col - string indicating which column in the data frame should be used
                      to identify the FOI
            options - dictionary with additional options.
            date_ID - specify the column with the date in the csv data frame

        Returns:
            Nothing.
        """

        # call the base class constructor
        super().__init__(signal_type)

        # There is only one path
        if isinstance(dirnames, str) :
            # first check if the directory with the csv files exists
            if not os.path.isdir(dirnames) :
                raise Exception("dir_csv_time_series_source - __init__() - %s is not a directory" % dirnames)

            # Now get the list of csv files inside the specified directory
            csv_files = [dirnames + '/' + f for f in os.listdir(dirnames) if f.endswith('.csv')]
        # there are several path names
        else :
            csv_files = []
            for dirname in dirnames :
                csv_files.extend([dirname + '/' + f for f in os.listdir(dirname) if f.endswith('.csv')])

        if len(csv_files) == 0 :
            raise Exception("dir_csv_time_series_source - __init__() - no csv files found" % dirname)

        if "suffixes_to_col" in options :
            new_cols = options["suffixes_to_col"]
        else :
            new_cols = None

        if "suffix_sep" in options :
            suffix_sep = options["suffix_sep"]
        else :
            suffix_sep = '_'

        if new_cols is not None :
            if "same_dates" in options :
                same_dates = options["same_dates"]
            else :
                raise Exception("dir_csv_time_series_source - it is necessary if the new columns have duplicated dates")

        # Now read the csv files and merged them in a single dataframe
        self.df = pd.read_csv(csv_files[0])

        if new_cols is not None :
            # determine the new column values from the suffix in the file name
            name = csv_files[0][:-4]
            name = name[name.rfind('/')+1:]
            col_values = name.split(suffix_sep)[-len(new_cols):]

            for index, new_col in enumerate(new_cols) :
                self.df[new_col] = col_values[index]

        if len(csv_files) > 1 :
            for file in csv_files[1:] :
                df = pd.read_csv(file)

                if new_cols is not None :
                    # determine the new column values from the suffix in the file name
                    name = file[:-4]
                    name = name[name.rfind('/')+1:]
                    col_values = name.split(suffix_sep)[-len(new_cols):]

                    for index, new_col in enumerate(new_cols) :
                        df[new_col] = col_values[index]

                self.df = pd.concat([self.df, df.copy()])

        # record the column name with the FIDs
        self.fid_col = fid_col

        # look for the attribute with the date and rename it in a standard way
        if (date_ID is not None) and date_ID in self.df :
            self.df.rename(columns={date_ID:'Date'}, inplace = True)

        elif 'date' in self.df :
            self.df.rename(columns={'date':'Date'}, inplace = True)

        elif 'acq_date' in self.df :
            self.df.rename(columns={'acq_date':'Date'}, inplace = True)

        elif 'obsdate' in self.df :
            self.df.rename(columns={'obsdate':'Date'}, inplace = True)

        if 'Date' not in self.df :
            raise Exception("csv_time_series_source.__init__() : dates not found")

        # reshape the database on the basis of the same date
        if new_cols is not None :
            for ii, col in enumerate(new_cols) :
                if same_dates[ii] :
                    # we need to reshape the database
                    unique_val = np.unique(self.df[col].values)

                    df1 = []
                    for jj, val in enumerate(unique_val) :
                        df = self.df[self.df[col] == val].copy()
                        df.drop(columns=[col], inplace=True)
                        df = df.add_suffix('_' + val)
                        df.rename(columns={'Date_'+val:'Date', self.fid_col+'_'+val : self.fid_col},\
                                  inplace=True)
                        if jj == 0 :
                            df1 = df.copy()
                        else :
                            # need to merge the two data bases
                            df1 = pd.merge(left=df, right=df1, left_on = ['Date', self.fid_col], right_on=['Date', self.fid_col])

                    self.df = df1

        # Force garbage collection
        gc.collect()

        self.components = list(self.df.columns)

    def get_ts(self, fid : int, start_date : datetime.datetime = datetime.datetime(2000,1,1), \
               stop_date : datetime.datetime = datetime.datetime(2000,1,1)) -> pd.DataFrame :
        """
        Summary :
            Return the time series associated to a specific fid (parcel
            identifier) for a given time range

        Arguments:
            fid - identifier of the parcel
            start_date - start date of the time series as datetime
            stop_date - stop date of the time series as datetime

        Returns:
            A pandas data frame

        Remark :
            If the start and the stop dates are not specified, all the available
            data are returned
        """

        # First isolate the elements related to the specific parcel (fid)
        # Make a copy to avoid 'touching' the originald data
        data = self.df[self.df[self.fid_col] == fid].copy()

        # convert the associated dates (strings) into datetime
        dates = pd.to_datetime(data['Date'].values)

        # Check if dates are set
        if (start_date != datetime.datetime(2000,1,1)) and \
           (stop_date != datetime.datetime(2000,1,1)) :

               ind = (dates >= start_date) & (dates <= stop_date)
               data = data[ind]
               dates = dates[ind]

        # If there are duplicated dates, keep only one date
        _, ind = np.unique(dates, return_index=True)
        data = data.iloc[ind]
        dates = dates[ind]

        # sort dataframe based on dates
        data['Date'] = dates
        data.sort_values(by=['Date'], inplace = True)
        data.set_index(['Date'], inplace=True)

        # Force garbage collection
        gc.collect()

        return data


class db_s2_time_series_source(base_time_series_source) :
    """
    Summary :
        Time series source obtaining data directly from the database for Sentinel-2 data.
        It combines info from multiple tables: signs, parcels, hist, image metadata.
        Data are provided by the database in the format required by the tool for subsequent analyses.
        No nedd for additional formatting operations.
        Multiple parcels are retrieved with a single call.
        All table names are parametrized to be flexible for future applications.
        Users can decide to retrieve completely cloud free images (cloud_free parameter) or get all and screen later using hist.
        Start time and end time are not applied to data retrieval but when the ts for a single parcel is requested (get_ts()).
        The potential advantages of this module are:
          1) possibility to retrieve data for multiple parcels in a single call
          2) possibility to define (any) specific user criteria in the SQL_condition parameter
          3) no processing is needed once data are loaded from the db
          4) better overall performance (to be tested)
    """
    def __init__(self, signal_type : str, host : str, port : str, dbname : str, user : str, password : str, db_schema : str, fid_col : str, parcels_table : str, sigs_table : str, hists_table : str, sentinel_metadata_table : str, start_time : datetime.datetime, end_time : datetime.datetime, sql_additional_conditions : str, cloud_free: str) :
        """
        Summary :
            Object constructor.

        Arguments:
            SIGNAL PARAMETER
            signal_type - string specifying the signal type

            DB ACCESS PARAMETERS:
            host - IP address of the database server
            port - port of the database (usually, 5432)
            dbname - name of the database where parcels are stored
            user - database user (with access privilege to the parcel table)
            password - database password

            TABLE PARAMETERS
            db_schema - name of the schema where the parcel/hist/signs layers are stored (in Outreach it is the code of the member state/paying agency)
            fid_col - column of the table where the unique identifier of the parcel is stored in the parcel table
            parcels_table - name of the table that stores parcels in the db (part of the standard name of the parcel layer: "db_schema"."parcels_table")
            sigs_table - name of the table that stores signs (Sentinel stats per image/parcel) in the db ("db_schema"."sigs_table")
            hists_table - name of the table that stores information on quality flags in the db ("db_schema"."hists_table")
            sentinel_metadata_table - name of the table that stores metadata of Sentinel images in the db (assumed to be stored in the "public" schema)

            PARAMETERS FOR TS EXTRACTION
            start_time - start date/time of the signs time series that will be used when the parcel is analysed
            end_time - end date/time of the signs time series that will be used when the parcel is analysed

            QUERY PARAMETERS
            sql_additional_conditions - string with SQL with the additional conditions that restrict the returned rows (this parameter can be empty)
            cloud_free - True or False, if true only images completely cloud free are returned (hist is included so it is possible to subselect later on)
        Notes:
            The parameters related to table names could be reduced to 1 (and the code simplified/generalized a lot) if a view is created in the DB.
            Using views, db_s2_time_series_source db_c6_time_series_source and db_bs_time_series_source can be easily reduced to 1 (db_time_series_source)
            sql_additional_conditions does not require WHERE at the beginning of the string; it can include any condition on any of the tables involved.
            start_time/end time are not applied to the data extraction from the db, but to the extraction of ts for an individual parcel (get_ts()).
            Conditions on the time range of data extraction can be set in the sql_additional_conditions parameters.

        Possible improvements:
            Another parameter can be added to check a list of SLC flags and calculate cloud percentage that can be included in the column list
            To be checked if start_time/end_time are useful or such conditions can be set when data are processed in the subsequent modules.

        Returns:
            Nothing.
        """

        super().__init__(signal_type)

        # Variable that stores the SQL to be executed on the DB and that is initialize when the object is created
        self.sql_select = self.sql_statement(db_schema, fid_col, parcels_table, sigs_table, hists_table , sentinel_metadata_table, sql_additional_conditions, cloud_free)
        # Variable that stores the complete ts retrieved from the DB and that is initialize when the object is created
        self.ts_db = self.get_ts_db(host, port, dbname, user, password, self.sql_select)
        # Variable that stores the list of components retrieved from the dataframe imported from the db
        self.components = list(self.ts_db.columns)

    def sql_statement(self, db_schema : str, fid_col : str, parcels_table : str, sigs_table : str, hists_table : str, sentinel_metadata_table : str, sql_additional_conditions : str, cloud_free : str) -> str :
        """
        Summary :
             This function creates the SQL string to be executed based on the parameters set by the user
             If cloud_free option is true, then an additional condition is set to exclude all the standard hist flags related to clouds
             There is no check on the correct syntax of the sql_additional_conditions string, it is passed to the db as it is
             Data are formatted according to the requests of the subsequent modules (bands by column and not by row)
             Function that call get_extracted_data_from_db to extract the ts data from the db and store in a dataframe
        """

        parcels = db_schema + "." + parcels_table
        sigs = db_schema + "." + sigs_table
        hists = db_schema + "." + hists_table
        sentinel_metadata = "public." + sentinel_metadata_table
        if(sql_additional_conditions != ""):
          sql_additional_conditions = " and " + sql_additional_conditions
        if(str(cloud_free).lower() == "true"):
          sql_additional_conditions = " and (not hist::jsonb?|array['3','8','9','10','11'])" + sql_additional_conditions

        # The query use FILTER() to group by using only records with a specific value in the band column
        # The GROUP BY and FILTER transform the structure of the table with bands in columns instead of rows
        # DISTINC ON is used to pick one single row for the same parcel/obstime (to avoid duplication for parcels in two UTM zones)
        # The first one is taken but other criteria could be used
        # NDVI mean and stdev are calculated with standard formula
        # Hist is transformed from json to text to be included in the GROUP BY clause (but content is the same)
        # Inclusion of Hist data slow down the query a lot: to improve performance, a materialized view can be used
        sql_select = """
        SELECT
         DISTINCT ON (""" + sigs + """.pid, obstime)
          """ + sigs + """.pid as db_id,
          """ + parcels + """.""" + fid_col + """ as parcel_id,
          """ + sigs + """.obsid,
          obstime,
          max(count)::integer as count_10m,
          min(count)::integer as count_20m,
          max(mean) filter(where band = 'B02') b02_mean,
          max(std) filter(where band = 'B02') b02_std,
          max(mean) filter(where band = 'B03') b03_mean,
          max(std) filter(where band = 'B03') b03_std,
          max(mean) filter(where band = 'B04') b04_mean,
          max(std) filter(where band = 'B04') b04_std,
          max(mean) filter(where band = 'B05') b05_mean,
          max(std) filter(where band = 'B05') b05_std,
          max(mean) filter(where band = 'B08') b08_mean,
          max(std) filter(where band = 'B08') b08_std,
          max(mean) filter(where band = 'B11') b011_mean,
          max(std) filter(where band = 'B11') b011_std,
          (((max(mean) filter(where band = 'B08')) - (max(mean) filter(where band = 'B04'))) / ((max(mean) filter(where band = 'B08')) + (max(mean) filter(where band = 'B04'))))::numeric(6,5)::double precision AS ndvi_mean,
          2 * ((((((max(mean) filter(where band = 'B04')) * (max(std) filter(where band = 'B08')))::double precision ^ 2) + (((max(mean) filter(where band = 'B08')) * (max(std) filter(where band = 'B04')))::double precision ^ 2)) ^ 0.5) / (((max(mean) filter(where band = 'B04')) + (max(mean) filter(where band = 'B08')))::double precision ^ 2))::numeric(6,5)::double precision AS ndvi_std,
          hist::text
        FROM
          """ + sigs + ", " + parcels + " , " + hists + ", " + sentinel_metadata + """
        WHERE
          card = 's2' and
          """ + parcels + """.ogc_fid = """ + sigs + """.pid and
          """ + sigs + """.obsid =  """ + sentinel_metadata + """.id and
          """ + sigs + """.pid = """ + hists + """.pid and
          """ + sigs + """.obsid = """ + hists + """.obsid
          """ + sql_additional_conditions + """
        GROUP BY
          """ + sigs + """.pid,
          """ + sigs + """.obsid,
          """ + parcels + """.""" + fid_col + """,
          obstime,
          hist::text
        ORDER BY
          """ + sigs + """.pid, obstime;"""

        # The following condition is removed from the query
        # The full TS is loaded then it is limited when the parcel is analysed (get_ts)
        # The ts retrieveal can be constrained with condition on obstime in the sql_additional_conditions parameter
        # obstime BETWEEN '""" + start_time + "' and '" + end_time + """' AND

        return sql_select

    def get_ts_db(self, host : str, port : str, dbname : str, user : str, password : str, sql_select : str) -> pd.DataFrame :
        """
        Summary :
             Function that call get_extracted_data_from_db to extract the ts data from the db and store in a dataframe
             It uses the connection parameters and the string with the SQL query
        """

        ts_db = gts.get_extracted_data_from_db(host, port, dbname, user, password, sql_select)

        # Force garbage collection
        gc.collect()

        return ts_db


    def get_ts(self, fid : str, start_date : datetime.datetime = None, end_date : datetime.datetime = None) -> pd.DataFrame :
        """
        Summary :
            Return the time series associated a single user-defined parcel with given time range contraints
            It subsets the complete TS retrieved from the db

        Arguments:
            fid - identifier of the parcel
            start_date - start date of the time series as datetime
            stop_date - stop date of the time series as datetime

        Notes:
            I apply here the conditions set in the option file. Here the fid is the user defined parcel id column.
            To be checked if limiting the time range here is the most appropriate place and if conditions in option files must be used here.

        Returns:
            A pandas data frame
        """
        # Two lines of code removed because it works even without an explicit formatting of the date
        # start_date = pd.to_datetime(start_date).to_pydatetime()
        # end_date = pd.to_datetime(end_date).to_pydatetime()

        if start_date is not None and end_date is not None:
            ts_final = self.ts_db.query('parcel_id == "' + str(fid) + '" and obstime >= "' + start_date + '" and obstime <= "' + end_date + '"')
        else:
            ts_final = self.ts_db.query('parcel_id == "' + str(fid) + '"')

        # Force garbage collection
        gc.collect()

        return ts_final

    def get_ts_full(self) -> pd.DataFrame :
        """
        Summary :
            Get the complete time series as specificed in the SQL statement defined by the option files and store in a data frame
            This can be called to have the whole set (get_ts() is used to retrieve one single parcel)
        Returns:
            A pandas data frame
        """
        # It stores the dataframe initialized in the self.ts_db into a data frame called ts_final
        ts_final = self.ts_db

        # Force garbage collection
        gc.collect()

        return ts_final

class db_c6_time_series_source(base_time_series_source) :
    """
    Summary :
        See summary in db_s2_time_series_source
    """
    def __init__(self, signal_type : str, host : str, port : str, dbname : str, user : str, password : str, db_schema : str, fid_col : str, parcels_table : str, sigs_table : str, sentinel_metadata_table : str, start_time : datetime.datetime, end_time : datetime.datetime, sql_additional_conditions : str) :
        """
        Summary :
            See summary in db_s2_time_series_source

        Arguments:
            See rguments in db_s2_time_series_source. In this case there is no neeed for the parameters related to SLC as Senintel 1 data is not affected.

        Returns:
            Nothing.
        """
        super().__init__(signal_type)

        # Variable that stores the SQL to be executed on the DB and that is initialize when the object is created
        self.sql_select = self.sql_statement(db_schema, fid_col, parcels_table, sigs_table, sentinel_metadata_table, sql_additional_conditions)
        # Variable that stores the complete ts retrieved from the DB and that is initialize when the object is created
        self.ts_db = self.get_ts_db(host, port, dbname, user, password, self.sql_select)
        # Variable that stores the list of components retrieved from the dataframe imported from the db
        self.components = list(self.ts_db.columns)
        #self.connection_opt = connection_opt

    def sql_statement(self, db_schema : str, fid_col : str, parcels_table : str, sigs_table : str, sentinel_metadata_table : str, sql_additional_conditions : str) -> str :

        parcels = db_schema + "." + parcels_table
        sigs = db_schema + "." + sigs_table
        sentinel_metadata = "public." + sentinel_metadata_table
        if(sql_additional_conditions != ""):
          sql_additional_conditions = " and " + sql_additional_conditions

        # The query use FILTER() to group by using only records with a specific value in the band column
        # The GROUP BY and FILTER transform the structure of the table with bands in columns instead of rows
        # DISTINC ON is used to pick one row for the same parcel/obstime [here date instead of daytime] (to avoid duplication for parcels in two UTM zones)
        # The first one is taken but other criteria could be used
        # NDVI mean and stdev are calculated with standard formula
        # Hist is transformed from json to text to be included in the GROUP BY clause (but content is the same)
        # Inclusion of Hist data slow down the query a lot: to improve performance, a materialized view can be used

        sql_select = """
        SELECT
         DISTINCT ON (""" + sigs + """.pid, obstime::date)
          """ + sigs + """.pid as db_id,
          """ + parcels + """.""" + fid_col + """ as parcel_id,
          """ + sigs + """.obsid,
          obstime,
          max(count)::integer as count,
          max(mean) filter(where band = 'VHc') VHc_mean,
          max(std) filter(where band = 'VHc') VHc_std,
          case when obstime::time < '12:00' then 'D' else 'A' end orbit,
          max(mean) filter(where band = 'VVc') VVc_mean,
          max(std) filter(where band = 'VVc') VVc_std
        FROM
          """ + sigs + ", " + parcels + " , " + sentinel_metadata + """
        WHERE
          card = 'c6' and
          """ + parcels + """.ogc_fid = """ + sigs + """.pid and
          """ + sigs + """.obsid =  """ + sentinel_metadata + """.id
          """ + sql_additional_conditions + """
        GROUP BY
          """ + sigs + """.pid,
          """ + sigs + """.obsid,
          """ + parcels + """.""" + fid_col + """,
          obstime
          ORDER BY
          """ + sigs + """.pid, obstime::date;"""

        return sql_select

    def get_ts_db(self, host : str, port : str, dbname : str, user : str, password : str, sql_select : str) -> pd.DataFrame :
        """
        Summary :
             Function that call get_extracted_data_from_db to extract the ts data from the db and store in a dataframe
             It uses the connection parameters and the string with the SQL query
        """

        # Connect with the database to get 'ALL' the related data
        ts_db = gts.get_extracted_data_from_db(host, port, dbname, user, password, sql_select)

        # Force garbage collection
        gc.collect()

        return ts_db


    def get_ts(self, fid : str, start_date : datetime.datetime = None, end_date : datetime.datetime = None) -> pd.DataFrame :
        """
        Summary :
            Return the time series associated to the set pg parcels defined in the conditions for a given time range

        Arguments:
            fid - identifier of the parcel
            start_date - start date of the time series as datetime
            stop_date - stop date of the time series as datetime

        Returns:
            A pandas data frame
        """

        # Here selection on dates makes little sense as i already selected it when i imported from the database
        # Maybe I should remove the condition on the query and keep it here?

        if start_date is not None and end_date is not None:
            ts_final = self.ts_db.query('parcel_id == "' + str(fid) + '" and obstime >= "' + start_date + '" and obstime <= "' + end_date + '"')
        else:
            ts_final = self.ts_db.query('parcel_id == "' + str(fid) + '"')

        # Force garbage collection
        gc.collect()

        return ts_final

    def get_ts_full(self) -> pd.DataFrame :
        """
        Summary :
            Get the complete time series as specificed in the SQL statement defined by the option files and store in a data frame
            This can be called to have the whole set (get_ts() is used to retrieve one single parcel)
        Returns:
            A pandas data frame
        """

        ts_final = self.ts_db

        # Force garbage collection
        gc.collect()

        return ts_final

class db_bs_time_series_source(base_time_series_source) :
    """
    Summary :
         See summary in db_s2_time_series_source
    """
    def __init__(self, signal_type : str, host : str, port : str, dbname : str, user : str, password : str, db_schema : str, fid_col : str, parcels_table : str, sigs_table : str, sentinel_metadata_table : str, start_time : datetime.datetime, end_time : datetime.datetime, sql_additional_conditions : str) :
        """
        Summary :
            See summary in db_s2_time_series_source

        Arguments:
            See rguments in db_s2_time_series_source. In this case there is no neeed for the parameters related to SLC as Senintel 1 data is not affected.

        Returns:
            Nothing.
        """
        super().__init__(signal_type)

        # Variable that stores the SQL to be executed on the DB and that is initialize when the object is created
        self.sql_select = self.sql_statement(db_schema, fid_col, parcels_table, sigs_table, sentinel_metadata_table, sql_additional_conditions)
        # Variable that stores the complete ts retrieved from the DB and that is initialize when the object is created
        self.ts_db = self.get_ts_db(host, port, dbname, user, password, self.sql_select)
        # Variable that stores the list of components retrieved from the dataframe imported from the db
        self.components = list(self.ts_db.columns)
        #self.connection_opt = connection_opt

    def sql_statement(self, db_schema : str, fid_col : str, parcels_table : str, sigs_table : str, sentinel_metadata_table : str, sql_additional_conditions : str) -> str :

        parcels = db_schema + "." + parcels_table
        sigs = db_schema + "." + sigs_table
        sentinel_metadata = "public." + sentinel_metadata_table
        if(sql_additional_conditions != ""):
          sql_additional_conditions = " and " + sql_additional_conditions

        # The query use FILTER() to group by using only records with a specific value in the band column
        # The GROUP BY and FILTER transform the structure of the table with bands in columns instead of rows
        # DISTINC ON is used to pick one row for the same parcel/obstime [here date instead of daytime] (to avoid duplication for parcels in two UTM zones)
        # The first one is taken but other criteria could be used
        # NDVI mean and stdev are calculated with standard formula
        # Hist is transformed from json to text to be included in the GROUP BY clause (but content is the same)
        # Inclusion of Hist data slow down the query a lot: to improve performance, a materialized view can be used
        # Log transformation is applied to VHb and VVb

        sql_select = """
        SELECT
         DISTINCT ON (""" + sigs + """.pid, obstime::date)
          """ + sigs + """.pid as db_id,
          """ + parcels + """.""" + fid_col + """ as parcel_id,
          """ + sigs + """.obsid,
          obstime,
          max(count)::integer as count,
          10*log(max(mean) filter(where band = 'VHb')) VHb_mean,
          max(std) filter(where band = 'VHb') VHb_std,
          case when obstime::time < '12:00' then 'D' else 'A' end orbit,
          10*log(max(mean) filter(where band = 'VVb')) VVb_mean,
          max(std) filter(where band = 'VVb') VVb_std
        FROM
          """ + sigs + ", " + parcels + " , " + sentinel_metadata + """
        WHERE
          card = 'bs' and
          """ + parcels + """.ogc_fid = """ + sigs + """.pid and
          """ + sigs + """.obsid =  """ + sentinel_metadata + """.id
          """ + sql_additional_conditions + """
        GROUP BY
          """ + sigs + """.pid,
          """ + sigs + """.obsid,
          """ + parcels + """.""" + fid_col + """,
          obstime
          ORDER BY
          """ + sigs + """.pid, obstime::date;"""

        # Following condition is removed from here because it is applied when the indivisual parcel is analyzed
        # The full TS is loaded then it is limited when the parcel is analysed (get_ts)
        # The ts retrieveal can be constrained with condition in the sql_additional_conditions parameter

        # obstime BETWEEN '""" + start_time + "' and '" + end_time + """' AND

        return sql_select

    def get_ts_db(self, host : str, port : str, dbname : str, user : str, password : str, sql_select : str) -> pd.DataFrame :
        """
        Summary :
             Function that call get_extracted_data_from_db to extract the ts data from the db and store in a dataframe
             It uses the connection parameters and the string with the SQL query
        """
        # Connect with the database to get 'ALL' the related data
        ts_db = gts.get_extracted_data_from_db(host, port, dbname, user, password, sql_select)

        # Force garbage collection
        gc.collect()

        return ts_db


    def get_ts(self, fid : str, start_date : datetime.datetime = None, end_date : datetime.datetime = None) -> pd.DataFrame :
        """
        Summary :
            Return the time series associated to the set pg parcels defined in the conditions for a given time range

        Arguments:
            fid - identifier of the parcel
            start_date - start date of the time series as datetime
            stop_date - stop date of the time series as datetime

        Returns:
            A pandas data frame
        """

        # here selection on dates makes little sense as i already selected it when i imported from the database
        # maybe i should remove the condition on the query and keep it here?

        #start_date = pd.to_datetime(start_date).to_pydatetime()
        #end_date = pd.to_datetime(end_date).to_pydatetime()
        if start_date is not None and end_date is not None:
            ts_final = self.ts_db.query('parcel_id == "' + str(fid) + '" and obstime >= "' + start_date + '" and obstime <= "' + end_date + '"')
        else:
            ts_final = self.ts_db.query('parcel_id == "' + str(fid) + '"')

        # Force garbage collection
        gc.collect()

        return ts_final

    def get_ts_full(self) -> pd.DataFrame :
        """
        Summary :
            Get the complete time series as specificed in the SQL statement defined by the option files and store in a data frame
            This can be called to have the whole set (get_ts() is used to retrieve one single parcel)
        Returns:
            A pandas data frame
        """

        ts_final = self.ts_db

        # Force garbage collection
        gc.collect()

        return ts_final


class time_serie_source_factory :
    """
    Summary :
        Object responsible for the creation of time_series_sources using the
        information from the option file
    """

    def get_time_series_sources(self, options : dict) -> list :
        """
        Summary :
            Return a list of time_series_sources as defined in the option file.

        Arguments :
            options - dictionary with the options for creating the time_series_sources

        Returns :
            List of time_series_sources.
        """

        # First check if the related options are available
        if 'dataReaders' not in options :
            raise Exception("time_serie_source_factory.get_time_series_sources() - no option specified")

        # A list of time series sources should be found
        option_list = options['dataReaders']
        output_list = []

        # Output list
        for option in option_list :

            # get the source
            output_list.append( self.get_source(option) )

        return output_list

    def get_source(self, option : dict) -> base_time_series_source :
        """
        Summary :
            Return a single time series source from a single option block.

        Arguments :
            option - dictionary with the option for creating the time_series_source

        Returns :
            A time_series_source.
        """

        # Check if the option has the right format
        if 'type' not in option :
            raise Exception("time_serie_source_factory.get_source() - wrong option format")

        source_type = option['type']
        signal_type = option['signal']

        if source_type == 'csv' :

            filename = option['path']

            if 'fidAttribute' in option :
                fid_col = option['fidAttribute']
            else:
                fid_col = 'FID'

            if 'date_column' in option :
                date_col = option['date_column']
            else :
                date_col = None

            source = csv_time_series_source(signal_type, filename, fid_col, date_col)

        elif source_type == 'dir_csv' :

            # determine the path of the directory with the csv files to load
            dirname = option['path']

            if 'fidAttribute' in option :
                fid_col = option['fidAttribute']
            else:
                fid_col = 'FID'

            if 'date_column' in option :
                date_col = option['date_column']
            else :
                date_col = None

            source = dir_csv_time_serie_source(signal_type, dirname, fid_col, option, date_col)

        elif source_type == "rest_s2" :
            conn_opt = option["connection_options"]

            if "cloud_categories" in option :
                source = restful_s2_time_series_source(signal_type, conn_opt, \
                                                    option["cloud_categories"])
            else :
                source = restful_s2_time_series_source(signal_type, conn_opt)

        elif source_type == "rest_c6" :
            conn_opt = option["connection_options"]

            source = restful_s1_time_series_source(signal_type, conn_opt, "c6")

        elif source_type == "rest_bs" :
            conn_opt = option["connection_options"]

            source = restful_s1_time_series_source(signal_type, conn_opt, "bs")

        elif source_type == "db_s2" :
            host =option['db_host']
            port = option['db_port']
            dbname = option['db_name']
            user = option['db_user']
            password = option['db_password']
            db_schema = option['db_schema']
            fid_col = option['fidAttribute']
            parcels_table = option['parcels_table']
            sigs_table = option['sigs_table']
            hists_table = option['hists_table']
            sentinel_metadata_table = option['sentinel_metadata_table']
            start_time = option['start_time']
            end_time = option['end_time']
            sql_additional_conditions = option['sql_additional_conditions']
            cloud_free = option['cloud_free']

            source = db_s2_time_series_source(signal_type, host, port, dbname, user, password, db_schema, fid_col, parcels_table, sigs_table, hists_table, sentinel_metadata_table, start_time, end_time, sql_additional_conditions, cloud_free)

        elif source_type == "db_c6" :
            host =option['db_host']
            port = option['db_port']
            dbname = option['db_name']
            user = option['db_user']
            password = option['db_password']
            db_schema = option['db_schema']
            fid_col = option['fidAttribute']
            parcels_table = option['parcels_table']
            sigs_table = option['sigs_table']
            sentinel_metadata_table = option['sentinel_metadata_table']
            start_time = option['start_time']
            end_time = option['end_time']
            sql_additional_conditions = option['sql_additional_conditions']

            source = db_c6_time_series_source(signal_type, host, port, dbname, user, password, db_schema, fid_col, parcels_table, sigs_table, sentinel_metadata_table, start_time, end_time, sql_additional_conditions)

        elif source_type == "db_bs" :
            host =option['db_host']
            port = option['db_port']
            dbname = option['db_name']
            user = option['db_user']
            password = option['db_password']
            db_schema = option['db_schema']
            fid_col = option['fidAttribute']
            parcels_table = option['parcels_table']
            sigs_table = option['sigs_table']
            sentinel_metadata_table = option['sentinel_metadata_table']
            start_time = option['start_time']
            end_time = option['end_time']
            sql_additional_conditions = option['sql_additional_conditions']

            source = db_bs_time_series_source(signal_type, host, port, dbname, user, password, db_schema, fid_col, parcels_table, sigs_table, sentinel_metadata_table, start_time, end_time, sql_additional_conditions)

        # elif source_type == '' :
        # add here additional source types
        else :
            raise Exception("time_serie_source_factory.get_source() - unsupported source type")

        return source
