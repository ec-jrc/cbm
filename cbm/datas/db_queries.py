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
from cbm.datas import db


# Requests
# Parcel information

def getParcelByLocation(dataset, lon, lat, ptype='',
                        withGeometry=False, wgs84=False):
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
        parcel_id = dataset['pcolumns']['parcel_id']

        if withGeometry:
            if wgs84:
                geometrySql = ", st_asgeojson(st_transform(wkb_geometry, 4326)) as geom"
            else:
                geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        getTableDataSql = f"""
            SELECT {parcel_id}::text as pid, {cropname} as cropname, {cropcode} as cropcode,
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


def getParcelByID(dataset, pid, ptype='', withGeometry=False,
                  wgs84=False):

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
        parcel_id = dataset['pcolumns']['parcel_id']

        if withGeometry:
            if wgs84:
                geometrySql = ", st_asgeojson(st_transform(wkb_geometry, 4326)) as geom"
            else:
                geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        getTableDataSql = f"""
            SELECT {parcel_id}::text as pid, {cropname} as cropname, {cropcode}::text as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat
            FROM {parcels_table}{ptype}
            WHERE {parcel_id} = '{pid}';
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


def getParcelsByPolygon(dataset, polygon, ptype='', withGeometry=False,
                        only_ids=True, wgs84=False):

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
        parcel_id = dataset['pcolumns']['parcel_id']

        if withGeometry:
            if wgs84:
                geometrySql = ", st_asgeojson(st_transform(wkb_geometry, 4326)) as geom"
            else:
                geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        if only_ids:
            selectSql = f"{parcel_id} as pid{geometrySql}"
        else:
            selectSql = f"""
                {parcel_id} as pid, {cropname} As cropname, {cropcode} As cropcode,
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

def getParcelTimeSeries(dataset, pid, ptype='',
                        tstype='s2', band=None, scl=True, ref=False):
    """Get the time series for the given parcel"""

    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    sigs_table = dataset['tables'][tstype]
    dias_catalog = dataset['tables']['dias_catalog']
    parcels_table = dataset['tables']['parcels']
    parcel_id = dataset['pcolumns']['parcel_id']

    from_hists = f", {dataset['tables']['scl']} h" if scl else ''
    select_scl = ', h.hist' if scl else ''
    select_ref = ', d.reference' if ref else ''

    where_shid = 'And s.pid = h.pid And h.obsid = s.obsid' if scl else ''
    where_band = f"And s.band = '{band}' " if band else ''

    if tstype.lower() == 's2':
        where_tstype = "And band IN ('B02', 'B03', 'B04', 'B05', 'B08', 'B11') "
    elif tstype.lower() == 'c6':
        where_tstype = "And band IN ('VVc', 'VHc') "
    elif tstype.lower() == 'bs':
        where_tstype = "And band IN ('VVb', 'VHb') "
    else:
        where_tstype = ""

    try:
        getTableDataSql = f"""
            SELECT extract('epoch' from d.obstime), s.band,
                s.count, s.mean, s.std, s.min, s.p25, s.p50, s.p75,
                s.max{select_scl}{select_ref}
            FROM {parcels_table}{ptype} p, {sigs_table} s,
                {dias_catalog} d{from_hists}
            WHERE
                p.ogc_fid = s.pid
                And p.{parcel_id} = '{pid}'
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


def getParcelPeers(dataset, pid, distance, maxPeers, ptype=''):

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
        parcel_id = dataset['pcolumns']['parcel_id']

        getTableDataSql = f"""
            WITH current_parcel AS (select {cropname},
                wkb_geometry from {parcels_table}{ptype} where {parcel_id} = {pid})
            SELECT {parcel_id}::text as pid, st_distance(wkb_geometry,
                (SELECT wkb_geometry FROM current_parcel)) As distance
            FROM {parcels_table}{ptype}
            WHERE {cropname} = (select {cropname} FROM current_parcel)
            And {parcel_id} != {pid}
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


def getS2frames(dataset, pid, start, end, ptype=''):
    """Get the sentinel images frames from dias cataloge for the given parcel"""

    conn = db.conn(dataset['db'])

    dias_catalog = dataset['tables']['dias_catalog']
    parcels_table = dataset['tables']['parcels']
    parcel_id = dataset['pcolumns']['parcel_id']
    # Get the S2 frames that cover a parcel identified by parcel
    # ID from the dias_catalogue for the selected date.

    end_date = pd.to_datetime(end) + pd.DateOffset(days=1)

    getS2framesSql = f"""
        SELECT reference, obstime, status
        FROM {dias_catalog}, {parcels_table}{ptype}
        WHERE card = 's2'
        And footprint && st_transform(wkb_geometry, 4326)
        And {parcel_id} = {pid}
        And obstime between '{start}' and '{end_date}'
        ORDER by obstime asc;
    """

    # Read result set into a pandas dataframe
    df_s2frames = pd.read_sql_query(getS2framesSql, conn)

    return df_s2frames['reference'].tolist()


def getSRID(dataset, ptype=''):
    """Get the SRID"""
    # Get parcels SRID.

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


def getParcelSCL(dataset, pid, ptype=''):

    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []
    parcel_id = dataset['pcolumns']['parcel_id']

    try:
        getTableDataSql = f"""
            SELECT h.obsid, h.hist
            FROM {dataset['tables']['scl']} h,
                {dataset['tables']['parcels']}{ptype} p
            WHERE h.pid = p.ogc_fid
            And p.{parcel_id} = '{pid}'
            ORDER By h.obsid Asc;
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


def getParcelCentroid(dataset, pid, ptype=''):

    conn = db.conn(dataset['db'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []
    parcel_id = dataset['pcolumns']['parcel_id']

    try:
        getTableDataSql = f"""
        SELECT ST_Asgeojson(ST_transform(ST_Centroid(wkb_geometry), 4326))
        FROM {dataset['tables']['parcels']}{ptype}
        WHERE {parcel_id} = {pid}
        LIMIT 1;
        """
        #  Return a list of tuples
        cur.execute(getTableDataSql)
        json_centroid = cur.fetchall()[0]
        return json.loads(json_centroid[0])['coordinates']

    except Exception as err:
        print("Can not get the parcel centroid: ", err)
        return data.append('Ended with no data')


def getPolygonCentroid(dataset, pid, ptype=''):
    """Get the centroid of the given polygon"""

    conn = db.conn(dataset['db'])
    parcel_id = dataset['pcolumns']['parcel_id']

    getParcelPolygonSql = f"""
        SELECT ST_Asgeojson(ST_transform(ST_Centroid(wkb_geometry), 4326))
            As center, ST_Asgeojson(st_transform(wkb_geometry, 4326)) As polygon
        FROM {dataset['tables']['parcels']}{ptype}
        WHERE {parcel_id} = {pid}
        LIMIT 1;
    """

    # Read result set into a pandas dataframe
    df_pcent = pd.read_sql_query(getParcelPolygonSql, conn)

    return df_pcent


def getTableCentroid(dataset, ptype=''):

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


def get_datasets():
    datasets_file = 'config/datasets.json'
    try:
        with open(datasets_file) as json_file:
            datasets = json.load(json_file)
        return datasets
    except Exception:
        datasets = """{
    "default_2020": {
        "db": "main",
        "description": "Dataset description",
        "center": "51.0,14.0",
        "zoom": "5",
        "year": "",
        "start_date": "",
        "end_date": "",
        "extent": "",
        "flip_coordinates": "False",
        "tables": {
            "parcels": "par",
            "dias_catalog": "dias_cat",
            "scl": "hists",
            "s2": "s2_sig",
            "bs": "bs_sig",
            "c6": "c6_sig",
            "bs_tf": "bs_ten"
        },
        "pcolumns": {
            "parcel_id": "id",
            "crop_name": "name",
            "crop_code": "code"
        }
    }
}"""
        with open(datasets_file, 'w') as outfile:
            json.dump(json.loads(datasets), outfile, indent=4)
        print("The datasets.json file did not exist, a new file was created.")
        return json.loads(datasets)
