#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import json
import psycopg2
import psycopg2.extras
import logging
import pandas as pd

from scripts import db


logging.basicConfig(filename='logs/queryHandler.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)


with open('config/datasets.json') as json_file:
    datasets = json.load(json_file)


# Requests
# Parcel information

def getParcelByLocation(aoi, year, lon, lat, ptype='',
                        withGeometry=False, wgs84=False):
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []
    parcels_table = dataset['tables']['parcels']

    try:
        logging.debug("start queries")
        getTableSrid = f"""
            SELECT Find_SRID('', '{parcels_table}{ptype}',
                'wkb_geometry');"""
        logging.debug(getTableSrid)
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]
        logging.debug(srid)
        cropname = dataset['pcolumns']['crop_name']
        cropcode = dataset['pcolumns']['crop_code']

        if withGeometry:
            if wgs84:
                geometrySql = ", st_asgeojson(st_transform(wkb_geometry, 4326)) as geom"
            else:
                geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        getTableDataSql = f"""
            SELECT ogc_fid, {cropname} as cropname, {cropcode} as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat
            FROM {parcels_table}{ptype}
            WHERE st_intersects(wkb_geometry,
            st_transform(st_geomfromtext('POINT({lon} {lat})', 4326), {srid}));
        """

        #  Return a list of tuples
        cur.execute(getTableDataSql)
        rows = cur.fetchall()
        logging.debug(rows)

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            logging.debug(
                f"No parcel found in {parcels_table}{ptype} that",
                f"intersects with point ({lon}, {lat})")
        logging.debug(data)
        return data

    except Exception as err:
        print(err)
        logging.debug("Did not find data, please select the right database",
                      "and table: ", err)
        return data.append('Ended with no data')


def getParcelById(aoi, year, pid, ptype='', withGeometry=False,
                  wgs84=False):
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    parcels_table = dataset['tables']['parcels']

    try:
        logging.debug("start queries")
        getTableSrid = f"""
            SELECT Find_SRID('', '{parcels_table}{ptype}',
                'wkb_geometry');"""
        logging.debug(getTableSrid)
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]
        logging.debug(srid)
        cropname = dataset['pcolumns']['crop_name']
        cropcode = dataset['pcolumns']['crop_code']

        if withGeometry:
            if wgs84:
                geometrySql = ", st_asgeojson(st_transform(wkb_geometry, 4326)) as geom"
            else:
                geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        getTableDataSql = f"""
            SELECT ogc_fid, {cropname} as cropname, {cropcode}::text as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat
            FROM {parcels_table}{ptype}
            WHERE ogc_fid = {pid};
        """

        #  Return a list of tuples
        # print(getTableDataSql)
        cur.execute(getTableDataSql)
        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            logging.debug(
                f"No parcel found in the selected table with id ({pid}).")
        return data

    except Exception as err:
        print(err)
        logging.debug("Did not find data, please select the right database",
                      "and table: ", err)
        return data.append('Ended with no data')


def getParcelsByPolygon(aoi, year, polygon, ptype='', withGeometry=False,
                        only_ids=True, wgs84=False):
    dataset = datasets[f'{aoi}_{year}']
    polygon = polygon.replace('_', ' ').replace('-', ',')

    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    parcels_table = dataset['tables']['parcels']

    try:
        logging.debug("start queries")
        getTableSrid = f"""
            SELECT Find_SRID('', '{parcels_table}{ptype}',
                'wkb_geometry');"""
        logging.debug(getTableSrid)
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]
        logging.debug(srid)
        cropname = dataset['pcolumns']['crop_name']
        cropcode = dataset['pcolumns']['crop_code']

        if withGeometry:
            if wgs84:
                geometrySql = ", st_asgeojson(st_transform(wkb_geometry, 4326)) as geom"
            else:
                geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        if only_ids:
            selectSql = f"ogc_fid{geometrySql}"
        else:
            selectSql = f"""
                ogc_fid, {cropname} As cropname, {cropcode} As cropcode,
                st_srid(wkb_geometry) As srid{geometrySql},
                st_area(wkb_geometry) As area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) As clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) As clat"""

        getTableDataSql = f"""
            SELECT {selectSql}
            FROM {parcels_table}{ptype}
            WHERE st_intersects(wkb_geometry,
            st_transform(st_geomfromtext('POLYGON(({polygon}))', 4326), {srid}))
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
            print(f"No parcel found in {parcels_table}{ptype} that",
                  "intersects with the polygon.")
        return data

    except Exception as err:
        print("Did not find data, please select the right database and table: ",
              err)
        return data.append('Ended with no data')


# Parcel Time Series

def getParcelTimeSeries(aoi, year, pid, ptype='',
                        tstype='s2', band=None, scl=True):
    """Get the time series for the given parcel"""
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    sigs_table = dataset['tables'][tstype]
    dias_catalog = dataset['tables']['dias_catalog']

    from_hists = f", {dataset['tables']['scl']}{ptype} h" if scl else ''
    select_scl = ', h.hist' if scl else ''

    where_shid = 'And s.pid = h.pid And h.obsid = s.obsid' if scl else ''
    where_band = f"And s.band = '{band}' " if band else ''

    if tstype.lower() == 's2':
        where_tstype = "And band IN ('B02', 'B03', 'B04', 'B05', 'B08', 'B11') "
    elif tstype.lower() == 's1':
        where_tstype = "And band IN ('VVc', 'VHc', 'VVb', 'VHb') "
    else:
        where_tstype = ""

    try:
        getTableDataSql = f"""
            SELECT extract('epoch' from d.obstime), s.band, s.count,
                s.mean, s.std, s.min, s.p25, s.p50, s.p75, s.max{select_scl}
            FROM {sigs_table}{ptype} s,
                {dias_catalog} d{from_hists}
            WHERE
                s.pid = {pid}
                And s.obsid = d.id
                {where_shid}
                {where_band}
                {where_tstype}
            ORDER By obstime, band asc;
        """
        #  Return a list of tuples
        # print(getTableDataSql)
        cur.execute(getTableDataSql)
        rows = cur.fetchall()
        data.append(tuple(etup.name for etup in cur.description))

        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            print("No time series found for",
                  f"{pid} in the selected signatures table '{sigs_table}'")
        return data

    except Exception as err:
        print("Did not find data, please select the right database and table: ",
              err)
        return data.append('Ended with no data')


def getParcelPeers(aoi, year, pid, distance, maxPeers, ptype=''):
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    parcels_table = dataset['tables']['parcels']

    try:
        logging.debug("start queries")
        getTableSrid = f"""
            SELECT Find_SRID('', '{parcels_table}{ptype}',
                'wkb_geometry');"""
        logging.debug(getTableSrid)
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]
        logging.debug(srid)
        cropname = dataset['pcolumns']['crop_name']

        getTableDataSql = f"""
            WITH current_parcel AS (select {cropname},
                wkb_geometry from {parcels_table}{ptype} where ogc_fid = {pid})
            SELECT ogc_fid as pid, st_distance(wkb_geometry,
                (SELECT wkb_geometry FROM current_parcel)) As distance
            FROM {parcels_table}{ptype}
            WHERE {cropname} = (select {cropname} FROM current_parcel)
            And ogc_fid != {pid}
            And st_dwithin(wkb_geometry,
                (SELECT wkb_geometry FROM current_parcel), {distance})
            And st_area(wkb_geometry) > 3000.0
            ORDER by st_distance(wkb_geometry,
                (SELECT wkb_geometry FROM current_parcel)) asc
            LIMIT {maxPeers};
            """
        #  Return a list of tuples
        # print(getTableDataSql)
        cur.execute(getTableDataSql)
        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            print("No parcel peers found in",
                  f"{parcels_table} within {distance} meters from parcel {pid}")
        return data

    except Exception as err:
        print("Did not find data, please select the right database and table: ",
              err)
        return data.append('Ended with no data')


def getS2frames(aoi, year, pid, start, end, ptype=''):
    """Get the sentinel images frames from dias cataloge for the given parcel"""
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])

    dias_catalog = dataset['tables']['dias_catalog']
    parcels_table = dataset['tables']['parcels']
    # Get the S2 frames that cover a parcel identified by parcel
    # ID from the dias_catalogue for the selected date.

    end_date = pd.to_datetime(end) + pd.DateOffset(days=1)

    getS2framesSql = f"""
        SELECT reference, obstime, status
        FROM {dias_catalog}, {parcels_table}{ptype}
        WHERE card = 's2'
        And footprint && st_transform(wkb_geometry, 4326)
        And ogc_fid = {pid}
        And obstime between '{start}' and '{end_date}'
        ORDER by obstime asc;
    """

    # Read result set into a pandas dataframe
    df_s2frames = pd.read_sql_query(getS2framesSql, conn)

    return df_s2frames['reference'].tolist()


def getSRID(aoi, year, ptype=''):
    """Get the SRID"""
    # Get parcels SRID.
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])

    pgq_srid = f"""
        SELECT ST_SRID(wkb_geometry)
        FROM {dataset['tables']['parcels']}{ptype}
        LIMIT 1;
        """

    df_srid = pd.read_sql_query(pgq_srid, conn)
    srid = df_srid['st_srid'][0]
    target_EPSG = int(srid)

    return target_EPSG


def getParcelSCL(aoi, year, pid, ptype=''):
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    try:
        getTableDataSql = f"""
            SELECT *
            FROM {dataset['tables']['parcels']}{ptype} h
            WHERE h.pid = {pid}
            ORDER By h.pid Asc;
        """
        #  Return a list of tuples
        cur.execute(getTableDataSql)
        rows = cur.fetchall()
        data.append(tuple(etup.name for etup in cur.description))

        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            print("No SCL time series found for",
                  f"{dataset['tables']['parcels']}{ptype}")
        return data

    except Exception as err:
        print("Did not find data, please select the right database and table: ",
              err)
        return data.append('Ended with no data')


def getParcelCentroid(aoi, year, pid, ptype=''):
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    try:
        getTableDataSql = f"""
            SELECT ST_X(ST_AsText(ST_Centroid(wkb_geometry))),
                    ST_Y(ST_AsText(ST_Centroid(wkb_geometry)))
            FROM {dataset['tables']['parcels']}{ptype}
            WHERE ogc_fid = {pid};
        """
        #  Return a list of tuples
        cur.execute(getTableDataSql)
        return cur.fetchall()[0]

    except Exception as err:
        print("Did not find data, please select the right database and table: ",
              err)
        return data.append('Ended with no data')


def getPolygonCentroid(aoi, year, pid, ptype=''):
    """Get the centroid of the given polygon"""
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])

    getParcelPolygonSql = f"""
        SELECT ST_Asgeojson(ST_transform(ST_Centroid(wkb_geometry), 4326))
            As center, ST_Asgeojson(st_transform(wkb_geometry, 4326)) As polygon
        FROM {dataset['tables']['parcels']}{ptype}
        WHERE ogc_fid = {pid}
        LIMIT 1;
    """

    # Read result set into a pandas dataframe
    df_pcent = pd.read_sql_query(getParcelPolygonSql, conn)

    return df_pcent


def getTableCentroid(aoi, year, ptype=''):
    dataset = datasets[f'{aoi}_{year}']
    conn = db.conn(dataset['db'])

    getTablePolygonSql = f"""
        SELECT ST_Asgeojson(ST_Transform(ST_PointOnSurface(ST_Union(geom)),
            4326)) As center
        FROM (SELECT wkb_geometry
        FROM {dataset['tables']['parcels']}{ptype}
        LIMIT 100) AS t(geom);
    """

    # Read result set into a pandas dataframe
    df_tcent = pd.read_sql_query(getTablePolygonSql, conn)

    return df_tcent
