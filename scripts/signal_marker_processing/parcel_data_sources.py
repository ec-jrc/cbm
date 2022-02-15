#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Authors    : Daniele Borio, Fernando Urbano, Csaba WIRNHARDT
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import geopandas as gpd
import numpy as np
import abc

import get_time_series as gts
import json
import shapely.geometry as sg
from shapely import wkt
import psycopg2

"""
Summary :
    Classes for manipulating information related to parcels.
"""

class base_parcel_data_source(metaclass = abc.ABCMeta) :
    """
    Summary :
        Abstract class defining the basic interfaces for all the derived
        classes.
    """
    @abc.abstractmethod
    def get_fid_list(self) :
        """
        Summary :
            Return the list FIDs (parcel identifiers) for which the data source
            has information.

        Arguments :
            None.

        Returns :
            Array of parcel identifiers.
        """
        return

    def get_parcel( self, fid : int ) :
        """
        Summary :
            Return the geometry and other properties related to the parcel with
            identifier equal to fid.

        Arguments :
            fid - the parcel identifier

        Returns :
            Geometry of the parcel (to be better defined).
        """

        return None

class simple_list_data_source(base_parcel_data_source) :
    """
    Summary :
        This is the simplest data source. It is based on an external text file
        with the list of fids to be processed. It is not able to provide the
        geometry of the parcels.
    """

    def __init__(self, filename : str) :
        """
        Summary :
            Object constructor.

        Arguments :
            filename - pathname of  the text file with the list of parcels to process.

        Returns :
            Nothing.
        """
        self.fid_list = np.loadtxt(filename, dtype = int, ndmin=1)

    def get_fid_list(self) :
        """
        Summary :
            Return the list FIDs (parcel identifiers) for which the data source
            has information.

        Arguments :
            None.

        Returns :
            Array of parcel identifiers.
        """

        return self.fid_list

class list_rest_data_source(simple_list_data_source) :
    """
    Summary :
        Extension of the simple_list_data_source where the parcel geometry
        is retrieved using the restful API developed for the outrach.
    """
    def __init__(self, filename : str, conn_opt : dict):
        """
        Summary :
            Object constructor.

        Arguments :
            filename - pathname of  the text file with the list of parcels to process.
            conn_opt - options specifying the connection parameters to the restful API.

            connection options must have the following format:
                {"ms" : "nl",
                 "year": 2018,
                 "api_user": "",
                 "api_pass": "",
                 "ptype": "m"}

        Returns :
            Nothing.
        """
        # Initialize the base class
        super().__init__(filename)

        # Save the connection options
        self.conn_opt = conn_opt

    def get_parcel( self, fid : int ) :
        """
        Summary :
            Return the geometry and other properties related to the parcel with
            identifier equal to fid.

        Arguments :
            fid - the parcel identifier

        Returns :
            Geometry of the parcel.
        """

        # get the ptype
        if "ptype" in self.conn_opt :
            ptype = self.conn_opt["ptype"]
        else :
            ptype = ""

        _, df, was_error = gts.get_parcel_data_from_restful( self.conn_opt["ms"], \
                           self.conn_opt["year"], fid, self.conn_opt["api_user"],\
                           self.conn_opt["api_pass"], ptype)

        if was_error :
            return None

        # extract the geometry information and put it in a dictionary
        geo_dict = json.loads(df["geom"].iloc[0])

        # create the associated multi-polygon
        poly = sg.MultiPolygon(sg.shape(geo_dict))

        # get the CRS
        crs = geo_dict["crs"]["properties"][geo_dict["crs"]["type"]]

        df.drop(columns = ['geom'], inplace=True)

        # This function works only for newer version of geopandas
        # df['Coordinates'] = gpd.GeoSeries.from_wkt([p.wkt for p in poly])
        df['WKT'] = [p.wkt for p in poly]
        df['Coordinates'] = df.WKT.apply(wkt.loads)
        df.drop('WKT', axis=1, inplace=True) #Drop WKT column

        # creat the geopandas dataframe
        gdf = gpd.GeoDataFrame(df, geometry='Coordinates', crs=crs)

        return gdf

class shape_data_source(base_parcel_data_source) :
    """
    Summary :
        Object responsible for reading/providing data related to parcels. It is
        based on ESRI shape files and geopandas.
    """
    def __init__(self, filename : str, fid_col : str, ext_fid : str = "") :
        """
        Summary :
            Object constructor.

        Arguments :
            filename - pathname of  the shape file to use to initialize the object
            fid_col - name of the attribute corresponding to the parcel identifier
                      in the geopandas dataframe/shape file
        Returns :
            Nothing.
        """

        # Open the geopandas dataframe
        self.df = gpd.read_file(filename)

        # Name of the column with the fids
        self.fid_col = fid_col

        if ext_fid != "" :

            # Load the fid list
            fid_list = np.loadtxt(ext_fid, dtype=int)

            # Find the fid intersection
            _, ind1, ind2 = np.intersect1d(self.df[self.fid_col].values, \
                                           fid_list, return_indices = True )

            self.df = self.df.iloc[ind1]

    def get_fid_list(self) :
        """
        Summary :
            Return the list FIDs (parcel identifiers) for which the data source
            has information.

        Arguments :
            None.

        Returns :
            Array of parcel identifiers.
        """
        fids = self.df[self.fid_col].values

        return fids

    def get_parcel( self, fid : int ) :
        """
        Summary :
            Return the geometry and other properties related to the parcel with
            identifier equal to fid.

        Arguments :
            fid - the parcel identifier

        Returns :
            Geometry of the parcel (to be better defined).
        """
        return self.df[self.df[self.fid_col] == fid]

class db_data_source(base_parcel_data_source) :
    """
        This data source is the direct database connection. It uses psycopg2 to directly connec with the db
        It retrieves all the information stored in the parcel table. Parameters connections must be set.
        This includes the schema where the table is stored, the name of the table, the ID column of the table and the name of the geometry column.
        It is possible to set a condition to limit the rows returned.
        This data source is not specific to Outreach and can be used in other context.
        A user with acess to the database must be incuded in the connection parameters.
    """

    def __init__(self, db_schema : str, parcel_table : str, host : str, port : str, dbname : str, user : str, password : str, fid_col : str, geometry_col : str, sql_additional_conditions : str) :

        """
        Summary :
            Object constructor.

        Arguments :
            db_schema - name of the schema where the parcle layer is stored (in outreach it corresponds to the code of the member state/paying agency)
            parcel_table - name of the table that stores parcels in the database (part of the standard name of the parcel layer: "db_schema"."parcel_table")
            host - IP address of the database server
            port - port of the database (usually, 5432)
            dbname - name of the database where parcels are stored
            user - database user (with access privilege to the parcel table)
            password - database password
            fid_col - column of the table where the unique identifier of the parcel is stored
            geometry_col - column of the table where the geometry of the parcel is stored
            sql_additional_conditions - string with sql code that specify the conditions that restrict the rows that will retrieved (it can be empty, if not empty a WHERE is added by the code)

            The option fid_list_file is not implemented (we can add it, if needed)

            Example of use in the option file:
            	"parcelSource" : {
            		"type" : "db",
            		"db_schema" : "HEREtheNAMEofSCHEMA",
            		"parcel_table" : "HEREtheNAMEofTABLE",
            		"db_host" : "HEREtheIPofDB",
            		"db_port" : "5432",
            		"db_name" : "HEREtheNAMEofDB",
            		"db_user" : "HEREtheUSER",
            		"db_password" : "HEREthePASSWORD",
            		"fidAttribute" : "id",
            		"geomAttribute" : "geom",
            		"sql_additional_conditions" : "st_area(geom) > 1000 ORDER BY id LIMIT 100"
            	},

        Returns :
            Nothing.
        """

        # Check if the connection parameters are correct and establish a connection with the db
        conn = None
        try:
            conn = psycopg2.connect(host=host, port=port, dbname= dbname, user= user, password= password)
            print("Coonection to DB established")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        # Check if the table exists (if not I print a message)
        exists = False
        cur = conn.cursor()
        cur.execute("select exists(Select 1 FROM information_schema.tables WHERE table_schema = '" + db_schema + "' AND table_name = '" + parcel_table + "')")
        exists = cur.fetchone()[0]
        cur.close()
        if exists == False :
            print ("The table " + db_schema + "." + parcel_table + " does not exist.")

        # Retrive data fom the table and count the rows
        cur = conn.cursor()
        if sql_additional_conditions:
            sql_additional_conditions = 'WHERE ' + sql_additional_conditions
        self.df = gpd.GeoDataFrame.from_postgis("SELECT * FROM " + db_schema + "." + parcel_table + " " + sql_additional_conditions + ";",  conn, geometry_col)
        cur.close()
        conn.close()
        total_rows = len(self.df.index)
        print ("The table " + db_schema + "." + parcel_table + " has " + str(total_rows) + " rows.")

        # Name of the column with the fids
        self.fid_col = fid_col

    def get_fid_list(self) :
        """
        Summary :
            Return the list FIDs (parcel identifiers) for which the data source
            has information.

        Arguments :
            None.

        Returns :
            Array of parcel identifiers.
        """
        fids = self.df[self.fid_col].values

        return fids

    def get_parcel( self, fid : int ) :
        """
        Summary :
            Return the geometry and other properties related to the parcel with
            identifier equal to fid.

        Arguments :
            fid - the parcel identifier

        Returns :
            Geometry of the parcel (to be better defined).
        """
        return self.df[self.df[self.fid_col] == fid]

class parcel_data_factory :
    """
    Summary :
        Object responsible for the creation of parcel data sources.
        It performs this task using the data read from an the option file
        (json format)
    """

    def get_parcel_data_source(self, options : dict) -> base_parcel_data_source :
        """
        Summary :
            Create the parcel data source using the information defined in the
            option file.

        Arguments :
            options - dictionary containing the information specified in the option file

        Returns :
            The parcel data source.
        """

        # First check if the related options are available
        if 'parcelSource' not in options :
            raise Exception("parcel_data_factory.get_parcel_data_source() - no option specified")

        # If here options are available
        source_options = options['parcelSource']
        parcel_source = None

        if source_options['type'] in ['shape', 'geojson', 'json']  :
            # get the name of the shape file
            filename = source_options['parcelFile']
            fid_col = source_options['fidAttribute']

            ext_list = ""
            if "externalFid" in source_options :
                ext_list = source_options["externalFid"]

            parcel_source = shape_data_source(filename, fid_col, ext_list)

        elif source_options['type'] == 'txt' :
            # simplest parcel data source with only the fid list
            # get the path of the file with the fid list
            filename = source_options['fid_list_file']

            parcel_source = simple_list_data_source(filename)

        elif source_options['type'] == 'db' :
            # load parcel data from the database
            # get the connection parameters, table information and selection criteria
            db_schema = source_options['db_schema']
            parcel_table = source_options['parcel_table']
            host =source_options['db_host']
            port = source_options['db_port']
            dbname = source_options['db_name']
            user = source_options['db_user']
            password = source_options['db_password']
            fid_col = source_options['fidAttribute']
            geometry_col = source_options['geomAttribute']
            sql_additional_conditions = source_options['sql_additional_conditions']

            parcel_source = db_data_source(db_schema, parcel_table, host, port, dbname, user, password, fid_col, geometry_col, sql_additional_conditions)

        elif source_options['type'] == 'txt_rest' :
            filename = source_options['fid_list_file']

            conn_opt = source_options["connection_options"]

            parcel_source = list_rest_data_source(filename, conn_opt)

        # elif source_options['type'] == '' :
        #   add other types
        else :
            raise Exception("parcel_data_factory.get_parcel_data_source() - unsupported type")

        return parcel_source
