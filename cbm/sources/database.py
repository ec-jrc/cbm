#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


"""
Project: Copernicus DIAS for CAP 'checks by monitoring'.
Functions:
  connection(db=1)
      - Create a new database session and return a new connection object.
  connection_cursor(db=1):
      - Create a cursor to execute PostgreSQL command in a database session.
  information(db=1)
      - Get database connection information.
  get_value(dict_keys, var_name=None)
      - Get value a table's name as value based on the given dictionary keys.

Options:
  -h, --help    Show this screen.
  --version     Show version.
"""


import psycopg2
import pandas as pd
from cbm.utils import config


# Database conection configurations
# #############################################################################
def crls(db=1):
    try:
        # Database
        values = config.read()
        DB_HOST = values['db'][f'{db}']['conn']['host']
        DB_NAME = values['db'][f'{db}']['conn']['name']
        DB_SCHE = values['db'][f'{db}']['conn']['sche']
        DB_USER = values['db'][f'{db}']['conn']['user']
        DB_PORT = values['db'][f'{db}']['conn']['port']
        DB_PASS = values['db'][f'{db}']['conn']['pass']
        return DB_HOST, DB_NAME, DB_USER, DB_PORT, DB_PASS
    except Exception as err:
        print(f"Could not read config file: {err}")


def conn_str(db=1):
    """Get the database connection string to connect the application to the database.\
    You will need the database credentials for this to work (database server address,\
    port, databese name, username and password)."""
    postgres = ("host={} dbname={} user={} port={} password={}"
                .format(*crls(db)))
    return postgres


def connection(db=1):
    """Create a new database session and return a new connection object."""
    try:
        conn = psycopg2.connect(conn_str(db))
        return conn
    except (Exception, psycopg2.Error) as err:
        print(f"Could not connect to the database {db}: {err}")
        return ''


def connection_cursor(db=1):
    """Create a cursor to execute PostgreSQL command in a database session"""
    try:
        conn = psycopg2.connect(conn_str(db))
        cur = conn.cursor()
        return cur
    except Exception:
        return ''


# Geting informationand and data
# #############################################################################
def get_value(dict_keys, var_name=None):
    """Get value for tables.

    Example:

        database.get_value(['database', 'table'], variable_table_name)

    Arguments:
        dict_keys, list of keys to get value from.
        var_name, the name ofthe variable

    """
    if dict_keys[0][-1] == '2':
        config_value = config.get_value(dict_keys)
        value = config.autoselect(config_value, tables(2), True)
    else:
        config_value = config.get_value(dict_keys)
        value = config.autoselect(config_value, tables(1), True)
    if var_name is not None:
        if value == None:
            print(f"!WARNING! The value for table '{var_name}' is: '{value}'.")
        else:
            print(f"The value for table '{var_name}' is: '{value}'.")
    return value


def information(db=1):
    """Get postgres database connection information."""
    try:
        conn = psycopg2.connect(conn_str(db))
        cur = conn.cursor()
        print("\n--> PostgreSQL Connection properties for database: ", db)
        print(conn.get_dsn_parameters(), "\n")
        # Print PostgreSQL version
        cur.execute("SELECT version();")
        record = cur.fetchone()
        print(f"You are connected to (db{db}) - {record}\n")
    except Exception as err:
        print("Error while connecting to PostgreSQL: ", err)
        print("Be sure the credentials are correct and restart the notebook.")


def tables(db=1, matching_text=None, print_list=False):
    """Get the database tables as a python list"""
    list_ = []
    try:
        conn = psycopg2.connect(conn_str(db))
        cur = conn.cursor()
        allTablesSql = """
          SELECT table_name
          FROM information_schema.tables
          WHERE table_type='BASE TABLE'
          AND table_schema='public'
          ORDER BY table_name ASC;
        """
        # Execute the query
        cur.execute(allTablesSql)
        for row in cur:
            list_.append(row[0])
        if matching_text is not None:
            value = config.autoselect(matching_text, list_)
            if value is not None:
                list_.remove(value)
                list_.insert(0, value)
        if print_list is True:
            print(f"-Tables in database {db}:-")
            for t_ in list_:
                print(t_)
        else:
            return list_
    except Exception as err:
        return []


def table_data(table, where, db=1):
    """Get the rows from a table with a limit 1000"""
    conn = psycopg2.connect(conn_str(db))
    try:
        getTableDataSql = f"""
          SELECT * FROM {table}
          WHERE 
          LIMIT 1000;
        """
        df_data = pd.read_sql_query(getTableDataSql, conn)
    except Exception:
        print("Did not found data, please select the right database and table")
        df_data = pd.DataFrame(columns=['name'])
    return df_data


def table_columns(table, db=1, matching_text=None):
    """Get a list of the columns from a table."""
    conn = psycopg2.connect(conn_str(db))
    try:
        getTableColumns = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table}';
            """
        df_columns = pd.read_sql_query(getTableColumns, conn)
        columns_list = df_columns['column_name'].tolist()
        if matching_text is not None:
            value = config.autoselect(matching_text, columns_list)
            if value is not None:
                columns_list.remove(value)
                columns_list.insert(0, value)
    except Exception:
        print("Did not found columns, please select the right database and table")
        df_columns = pd.DataFrame(columns=['column_name'])
    return columns_list


def close_connection(close_1='', close_2=''):
    """Close the database connection"""
    try:
        connection.conn.close()
        print("The connection to the database is now closed.")
    except Exception:
        pass
    try:
        connection.conn_2.close()
        print("The connection to the second database is now closed.")
    except Exception:
        pass
    try:
        close_1.close()
        print("First argument is closed.")
    except Exception:
        pass
    try:
        close_2.close()
        print("Second argument is closed.")
    except Exception:
        pass


# Requests

def getParcelByLocation(dsc, lon, lat, withGeometry=False, db=1):
    """Find the parcel under the given coordinates"""
    conn = psycopg2.connect(conn_str(db))
    cur = conn.cursor()
    data = []
    values = config.read()
    dsc = values['set']['ds_conf']
    dsy = values['set']['ds_year']
    try:
        values = config.read()
        parcels_table = values['ds_conf'][dsc]['years'][dsy]['tables']['parcels']
        crop_names = values['ds_conf'][dsc]['columns']['crop_names']
        crop_codes = values['ds_conf'][dsc]['columns']['crop_codes']
        parcels_id = values['ds_conf'][dsc]['columns']['parcels_id']

        getTableSrid = f"""
            SELECT srid FROM geometry_columns
            WHERE f_table_name = '{parcels_table}'"""
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]


        if withGeometry:
            geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        getTableDataSql = f"""
            SELECT {parcels_id}, {crop_names} as cropname, {crop_codes} as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat
            FROM {parcels_table}
            WHERE st_intersects(wkb_geometry,
                  st_transform(st_geomfromtext('POINT({lon} {lat})', 4326), {srid}));
        """

        #  Return a list of tuples
        cur.execute(getTableDataSql)
        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            print(f"No parcel found in {parcels_table} that intersects with point ({lon}, {lat})")
        return data

    except Exception as err:
        print("1 Did not find data, please select the right database and table: ", err)
        return data.append('Ended with no data')


def getParcelById(dsc, pid, withGeometry=False, db=1):
    """Get parcel information for the given parcel id"""
    conn = psycopg2.connect(conn_str(db))
    cur = conn.cursor()
    data = []
    values = config.read()
    dsc = values['set']['ds_conf']
    dsy = values['set']['ds_year']
    try:
        values = config.read()
        parcels_table = values['ds_conf'][dsc]['years'][dsy]['tables']['parcels']
        crop_names = values['ds_conf'][dsc]['years'][dsy]['columns']['crop_names']
        crop_codes = values['ds_conf'][dsc]['years'][dsy]['columns']['crop_codes']
        parcels_id = values['ds_conf'][dsc]['years'][dsy]['columns']['parcels_id']

        getTableSrid = f"""
            SELECT srid FROM geometry_columns
            WHERE f_table_name = '{parcels_table}'"""
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]

        if withGeometry:
            geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        getTableDataSql = f"""
            SELECT {parcels_id}, {crop_names} as cropname, {crop_codes} as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat
            FROM {parcels_table}
            WHERE {parcels_id} = {pid};
        """

        #  Return a list of tuples
        cur.execute(getTableDataSql)
        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            print(f"No parcel found in {parcels_table} with id ({pid}).")
        return data

    except Exception as err:
        print("2 Did not find data, please select the right database and table: ", err)
        return data.append('Ended with no data')


def getParcelsByPolygon(dsc, polygon, withGeometry=False, only_ids=True, db=1):
    """Get list of parcels within the given polygon"""
    poly = polygon.replace('_', ' ').replace('-', ',')

    conn = psycopg2.connect(conn_str(db))
    cur = conn.cursor()
    data = []
    values = config.read()
    dsc = values['set']['ds_conf']
    dsy = values['set']['ds_year']
    try:
        values = config.read()
        parcels_table = values['ds_conf'][dsc]['years'][dsy]['tables']['parcels']
        crop_names = values['ds_conf'][dsc]['years'][dsy]['columns']['crop_names']
        crop_codes = values['ds_conf'][dsc]['years'][dsy]['columns']['crop_codes']
        parcels_id = values['ds_conf'][dsc]['years'][dsy]['columns']['parcels_id']

        getTableSrid = f"""
            SELECT srid FROM geometry_columns
            WHERE f_table_name = '{parcels_table}'"""
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]

        if withGeometry:
            geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        if only_ids:
            selectSql = f"{parcels_id}{geometrySql}"
        else:
            selectSql = f"""{parcels_id}, {crop_names} as cropname, {crop_codes} as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat"""

        getTableDataSql = f"""
            SELECT {selectSql}
            FROM {parcels_table}
            WHERE st_intersects(wkb_geometry,
                  st_transform(st_geomfromtext('POLYGON(({poly}))', 4326), {srid}))
            LIMIT 100;
        """

        #  Return a list of tuples
        cur.execute(getTableDataSql)
        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            print(f"No parcel found in {parcels_table} that intersects with the polygon.")
        return data

    except Exception as err:
        print("3 Did not find data, please select the right database and table: ", err)
        return data.append('Ended with no data')


def getParcelTimeSeries(dsc, year, pid, tstype, band=None, db=1):
    """Get the time series for the given parcel"""
    conn = psycopg2.connect(conn_str(db))
    cur = conn.cursor()
    data = []
    values = config.read()
    dsc = values['set']['ds_conf']
    dsy = values['set']['ds_year']
    try:
        values = config.read()
        dias_catalog = values['ds_conf'][dsc]['years'][dsy]['tables']['dias_catalog']
        signatures_tb = values['ds_conf'][dsc]['years'][dsy]['tables'][tstype]

        if band:
            getTableDataSql = f"""
                SELECT extract('epoch' from obstime), count,
                    mean, std, min, p25, p50, p75, max
                FROM {signatures_tb} s, {dias_catalog} d
                WHERE s.obsid = d.id and
                pid = {pid} and
                band = '{band}'
                ORDER By obstime asc;
            """
        else:
            getTableDataSql = f"""
                SELECT extract('epoch' from obstime), band,
                    count, mean, std, min, p25, p50, p75, max
                FROM {signatures_tb} s, {dias_catalog} d
                WHERE s.obsid = d.id and
                pid = {pid}
                ORDER By obstime, band asc;
            """
        #  Return a list of tuples
        cur.execute(getTableDataSql)

        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            print(f"No time series found for {pid} in {signatures_tb}")
        return data

    except Exception as err:
        print("4 Did not find data, please select the right database and table: ", err)
        return data.append('Ended with no data')


def getParcelPeers(parcels_table, pid, distance, maxPeers, db=1):
    conn = psycopg2.connect(conn_str(db))
    cur = conn.cursor()
    data = []

    try:
        print("start queries")
        getCropCodes = f"""
            SELECT cropname, cropcode FROM croplabels
            WHERE parceltable = '{parcels_table}'"""
        print(getCropCodes)
        cur.execute(getCropCodes)
        row = cur.fetchone()
        crop_names = row[0]

        getTableDataSql = f"""
            WITH current_parcel AS (select {crop_names},
                wkb_geometry from {parcels_table} where {parcels_id} = {pid})
            SELECT {parcels_id} as pid, st_distance(wkb_geometry,
                (SELECT wkb_geometry FROM current_parcel)) as distance from {parcels_table} 
            where {crop_names} = (select {crop_names} from current_parcel)
            And {parcels_id} != {pid}
            And st_dwithin(wkb_geometry, (SELECT wkb_geometry FROM current_parcel), {distance})
            And st_area(wkb_geometry) > 3000.0
            order by st_distance(wkb_geometry, (SELECT wkb_geometry FROM current_parcel)) asc
            LIMIT {maxPeers};
            """
        #  Return a list of tuples
        print(getTableDataSql)
        cur.execute(getTableDataSql)
        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            print(f"No parcel peers found in {parcels_table} within {distance} meters from parcel {pid}")
        return data

    except Exception as err:
        print("5 Did not find data, please select the right database and table: ", err)
        return data.append('Ended with no data')


def getS2frames(parcel_id, start, end, db=1):
    """Get the sentinel images frames from dias cataloge for the given parcel"""
    conn = psycopg2.connect(conn_str(db))
    values = config.read()
    dsc = values['set']['ds_conf']
    dsy = values['set']['ds_year']
    dias_catalog = values['ds_conf'][dsc]['years'][dsy]['tables']['dias_catalog']
    parcels_table = values['ds_conf'][dsc]['years'][dsy]['tables']['parcels']
    parcels_id = values['ds_conf'][dsc]['years'][dsy]['columns']['parcels_id']
    # Get the S2 frames that cover a parcel identified by parcel
    # ID from the dias_catalogue for the selected date.

    end_date = pd.to_datetime(end) + pd.DateOffset(days=1)

    getS2framesSql = f"""
        SELECT reference, obstime, status
        FROM {dias_catalog}, {parcels_table}
        WHERE card = 's2'
        And footprint && st_transform(wkb_geometry, 4326)
        And {parcels_id} = {parcel_id}
        And obstime between '{start}' and '{end_date}'
        ORDER by obstime asc;
    """

    # Read result set into a pandas dataframe
    df_s2frames = pd.read_sql_query(getS2framesSql, conn)

    return df_s2frames['reference'].tolist()


def getSRID(dsc, db=1):
    """Get the SRID"""
    # Get parcels SRID.
    conn = psycopg2.connect(conn_str(db))
    values = config.read()
    dsc = values['set']['ds_conf']
    dsy = values['set']['ds_year']
    parcels_table = values['ds_conf'][dsc]['years'][dsy]['tables']['parcels']

    pgq_srid = f"""
        SELECT ST_SRID(wkb_geometry) FROM {parcels_table} LIMIT 1;
        """

    df_srid = pd.read_sql_query(pgq_srid, conn)
    srid = df_srid['st_srid'][0]
    target_EPSG = int(srid)

    return target_EPSG


def getPolygonCentroid(parcel_id, db=1):
    """Get the centroid of the given polygon"""
    conn = psycopg2.connect(conn_str(db))
    values = config.read()
    dsc = values['set']['ds_conf']
    dsy = values['set']['ds_year']
    parcels_table = values['ds_conf'][dsc]['years'][dsy]['tables']['parcels']
    parcels_id = values['ds_conf'][dsc]['years'][dsy]['columns']['parcels_id']

    getParcelPolygonSql = f"""
        SELECT ST_Asgeojson(ST_transform(ST_Centroid(wkb_geometry), 4326)) as center,
          ST_Asgeojson(st_transform(wkb_geometry, 4326)) as polygon
        FROM {parcels_table} 
        WHERE {parcels_id} = {parcel_id}
        LIMIT 1;
    """

    # Read result set into a pandas dataframe
    df_pcent = pd.read_sql_query(getParcelPolygonSql, conn)
    
    return df_pcent


def getTableCentroid(parcels_table, db=1):
    conn = psycopg2.connect(conn_str(db))

    getTablePolygonSql = f"""
        SELECT ST_Asgeojson(ST_Transform(ST_PointOnSurface(ST_Union(geom)),4326)) as center
        FROM (SELECT wkb_geometry FROM {parcels_table} LIMIT 100) AS t(geom);
    """

    # Read result set into a pandas dataframe
    df_tcent = pd.read_sql_query(getTablePolygonSql, conn)

    return df_tcent


def insert_function(func, db=1):
    """
    Insert functions to database.
    Args:
    func: Sql text to add a new function to the database.
        type: srt
    db: Database configurarion
    """
    import psycopg2.extras
    import psycopg2.extensions
    conn = psycopg2.connect(conn_str(db))
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Execute function.
    cur.execute(func)


def exact_count(table, db=1):
    """Return the exact count of rown of the given table"""
    conn = psycopg2.connect(conn_str(db))
    cur = conn.cursor()
    getExactCount = f"""
        SELECT count(*) AS exact_count
        FROM {table};"""
    
    cur.execute(getExactCount)
    return cur.fetchall()[0][0]

def execute_query(query, db=1):
    """Return query"""
    conn = psycopg2.connect(conn_str(db))
    cur = conn.cursor()
    cur.execute(query)
    data = cur.fetchall()
    conn.close()
    cur.close()
    return data

def execute_sql(sql, db=1):
    """Execute sql"""
    try:
        conn = psycopg2.connect(conn_str(db))
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit() # <--- makes sure the change is shown in the database
        conn.close()
        cur.close()
        return 0
    except Exception as err:
        return 1


def tb_extent(table, db=1):
    """Get the extent of the table"""
    data = []
    try:
        conn = psycopg2.connect(conn_str(db))
        cur = conn.cursor()
        sql = f"""
        SELECT ST_AsText(ST_SetSRID(ST_Extent(st_transform(wkb_geometry, 4326)),4326))
            As bextent
        FROM {table};"""
        cur.execute(sql)
        for row in cur:
            data.append(row)
        conn.commit() # <--- makes sure the change is shown in the database
        conn.close()
        cur.close()
        data = data[0][0].replace(' ', '+')
        return data.replace('POLYGON((', '').replace('))', '')
    except Exception as err:
        return err


def tb_exist(table, db=1):
    """Check if table exist"""
    tbExistSql = f"""
        SELECT * FROM information_schema.tables
        WHERE table_name = '{table}';
    """
    conn = psycopg2.connect(conn_str(db))
    cur = conn.cursor()
    cur.execute(tbExistSql)
    exist = bool(cur.rowcount)
    conn.close()
    cur.close()
    return exist
