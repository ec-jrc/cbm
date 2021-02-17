#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import psycopg2
import pandas as pd
from cbm.sources import db

# Requests
def getParcelByLocation(dsc, lon, lat, withGeometry=False, set_db='main'):
    """Find the parcel under the given coordinates"""
    conn = db.conn(set_db)
    cur = db.cur(set_db)
    data = []
    values = config.read()
    dsc = values['set']['dataset']
    dsy = values['set']['ds_year']
    try:
        values = config.read()
        parcels_table = values['dataset'][dsc]['tables']['parcels']
        crop_names = values['dataset'][dsc]['columns']['crop_names']
        crop_codes = values['dataset'][dsc]['columns']['crop_codes']
        parcels_id = values['dataset'][dsc]['columns']['parcels_id']

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


def getParcelById(dsc, pid, withGeometry=False, set_db='main'):
    """Get parcel information for the given parcel id"""
    conn = db.conn(set_db)
    cur = db.cur(set_db)
    data = []
    values = config.read()
    dsc = values['set']['dataset']
    dsy = values['set']['ds_year']
    try:
        values = config.read()
        parcels_table = values['dataset'][dsc]['tables']['parcels']
        crop_names = values['dataset'][dsc]['columns']['crop_names']
        crop_codes = values['dataset'][dsc]['columns']['crop_codes']
        parcels_id = values['dataset'][dsc]['columns']['parcels_id']

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


def getParcelsByPolygon(dsc, polygon, withGeometry=False, only_ids=True, set_db='main'):
    """Get list of parcels within the given polygon"""
    poly = polygon.replace('_', ' ').replace('-', ',')

    conn = db.conn(set_db)
    cur = db.cur(set_db)
    data = []
    values = config.read()
    dsc = values['set']['dataset']
    dsy = values['set']['ds_year']
    try:
        values = config.read()
        parcels_table = values['dataset'][dsc]['tables']['parcels']
        crop_names = values['dataset'][dsc]['columns']['crop_names']
        crop_codes = values['dataset'][dsc]['columns']['crop_codes']
        parcels_id = values['dataset'][dsc]['columns']['parcels_id']

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


def getParcelTimeSeries(dsc, year, pid, tstype, band=None, set_db='main'):
    """Get the time series for the given parcel"""
    conn = db.conn(set_db)
    cur = db.cur(set_db)
    data = []
    values = config.read()
    dsc = values['set']['dataset']
    dsy = values['set']['ds_year']
    try:
        values = config.read()
        dias_catalog = values['dataset'][dsc]['tables']['dias_catalog']
        signatures_tb = values['dataset'][dsc]['tables'][tstype]

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


def getParcelPeers(parcels_table, pid, distance, maxPeers, set_db='main'):
    conn = db.conn(set_db)
    cur = db.cur(set_db)
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


def getS2frames(parcel_id, start, end, set_db='main'):
    """Get the sentinel images frames from dias cataloge for the given parcel"""
    conn = db.conn(set_db)
    values = config.read()
    dsc = values['set']['dataset']
    dsy = values['set']['ds_year']
    dias_catalog = values['dataset'][dsc]['tables']['dias_catalog']
    parcels_table = values['dataset'][dsc]['tables']['parcels']
    parcels_id = values['dataset'][dsc]['columns']['parcels_id']
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


def getSRID(dsc, set_db='main'):
    """Get the SRID"""
    # Get parcels SRID.
    conn = db.conn(set_db)
    values = config.read()
    dsc = values['set']['dataset']
    dsy = values['set']['ds_year']
    parcels_table = values['dataset'][dsc]['tables']['parcels']

    pgq_srid = f"""
        SELECT ST_SRID(wkb_geometry) FROM {parcels_table} LIMIT 1;
        """

    df_srid = pd.read_sql_query(pgq_srid, conn)
    srid = df_srid['st_srid'][0]
    target_EPSG = int(srid)

    return target_EPSG


def getPolygonCentroid(parcel_id, set_db='main'):
    """Get the centroid of the given polygon"""
    conn = db.conn(set_db)
    values = config.read()
    dsc = values['set']['dataset']
    dsy = values['set']['ds_year']
    parcels_table = values['dataset'][dsc]['tables']['parcels']
    parcels_id = values['dataset'][dsc]['columns']['parcels_id']

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


def getTableCentroid(parcels_table, set_db='main'):
    conn = db.conn(set_db)

    getTablePolygonSql = f"""
        SELECT ST_Asgeojson(ST_Transform(ST_PointOnSurface(ST_Union(geom)),4326)) as center
        FROM (SELECT wkb_geometry FROM {parcels_table} LIMIT 100) AS t(geom);
    """

    # Read result set into a pandas dataframe
    df_tcent = pd.read_sql_query(getTablePolygonSql, conn)

    return df_tcent