#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import psycopg2
import psycopg2.extras
import logging

from scripts import backgroundExtract as bgext
# from scripts import chipS2Extractor2 as ces2
# from scripts import rawChipBatchExtract as rceb
# from scripts import rawChipExtractor as rce
# from scripts import rawS1ChipBatchExtract as rces1

from scripts import db
conn_str = db.conn_str()

logging.basicConfig(filename='logs/queryHandler.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)


# Parcel Images

def getBackgroundByLocation(lon, lat, chipsize, chipextend, tms,
                            unique_id, iformat):
    try:
        logging.debug(unique_id)
        logging.debug(f"{unique_id} {iformat}")
        bgext.getWindowedExtract(lon, lat, chipsize, chipextend,
                                 unique_id, tms, iformat)
        return True
    except Exception as err:
        print(err)


def getChipsByLocation(lon, lat, start_date, end_date, unique_id, lut='5_95',
                       bands='B08_B04_B03', plevel='LEVEL2A'):
    logging.debug(lut)
    logging.debug(bands)
    logging.debug(f"{lon} {lat} {start_date} {end_date} {unique_id} {lut} {bands} {plevel}")

    numchips = ces2.parallelExtract(
        lon, lat, start_date, end_date, unique_id, lut, bands, plevel)

    if numchips == -1:
        print(f"Request results in too many chips, please revise selection")
    elif numchips > 0:
        print(ces2.chipCollect(unique_id))
    else:
        print(f"Chips already cached in {unique_id}")

    print(ces2.buildHTML(unique_id, start_date, end_date))

    return True


def getRawChipByLocation(lon, lat, start_date, end_date, unique_id, band,
                         chipsize='1280', plevel='LEVEL2A'):
    logging.debug(
        f"{lon} {lat} {start_date} {end_date} {unique_id} {band} {plevel}")

    numchips = rce.parallelExtract(lon, lat, start_date, end_date, unique_id,
                                   band, chipsize, plevel)

    if numchips == -1:
        print(f"Request results in too many chips, please revise selection")
    elif numchips > 0:
        print(rce.chipCollect(unique_id))
    else:
        print(f"Chips already cached in {unique_id}")

    print(rce.buildJSON(unique_id, start_date, end_date))
    return True


def getRawChipsBatch(unique_id):
    # params are dumped in params.json on unique_id directory

    logging.debug(unique_id)
    numchips = rceb.parallelExtract(unique_id)

    if numchips == -1:
        print(f"Request results in too many chips, please revise selection")
    elif numchips > 0:
        print(rceb.chipCollect(unique_id))
    else:
        print(f"Chips already cached in {unique_id}")

    print(rceb.buildJSON(unique_id))
    return True


def getRawS1ChipsBatch(unique_id):
    # params are dumped in params.json on unique_id directory

    logging.debug(unique_id)

    numchips = rces1.parallelExtract(unique_id)

    if numchips == -1:
        print(f"Request results in too many chips, please revise selection")
    elif numchips > 0:
        print(rces1.chipCollect(unique_id))
    else:
        print(f"Chips already cached in {unique_id}")

    print(rces1.buildJSON(unique_id))
    return True


# Parcel Time Series

def getParcelTimeSeries(parcelTable, pid, tstype, band=None):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    try:
        if band:
            getTableDataSql = f"""
                SELECT extract('epoch' from obstime), count,
                    mean, std, min, p25, p50, p75, max
                FROM {parcelTable}_{tstype}_signatures s,
                    {parcelTable}_dias_catalogue d
                WHERE s.obsid = d.id and
                pid = {pid} and
                band = '{band}'
                ORDER By obstime asc;
            """
        else:
            getTableDataSql = f"""
                SELECT extract('epoch' from obstime), band,
                    count, mean, std, min, p25, p50, p75, max
                FROM {parcelTable}_{tstype}_signatures s,
                    {parcelTable}_dias_catalogue d
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
            print("No time series found for",
                  f"{pid} in {parcelTable}_{tstype}_signatures")
        return data

    except Exception as err:
        print("Did not find data, please select the right database and table: ",
              err)
        return data.append('Ended with no data')


def getParcelPeers(parcelTable, pid, distance, maxPeers):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    try:
        logging.debug("start queries")
        getCropCodes = f"""
            SELECT cropname, cropcode, codetype FROM croplabels
            WHERE parceltable = '{parcelTable}'"""
        logging.debug(getCropCodes)
        cur.execute(getCropCodes)
        row = cur.fetchone()
        cropname = row[0]

        getTableDataSql = f"""
            WITH current_parcel AS (SELECT {cropname}, wkb_geometry
            FROM {parcelTable} where ogc_fid = {pid})
            SELECT ogc_fid as pid, st_distance(wkb_geometry,
                (SELECT wkb_geometry FROM current_parcel))
                as distance from {parcelTable}
            where {cropname} = (SELECT {cropname} from current_parcel)
            And ogc_fid != {pid}
            And st_dwithin(wkb_geometry,
                (SELECT wkb_geometry FROM current_parcel), {distance})
            And st_area(wkb_geometry) > 3000.0
            Order by st_distance(wkb_geometry,
                (SELECT wkb_geometry FROM current_parcel)) asc
            LIMIT {maxPeers};
            """
        #  Return a list of tuples
        logging.debug(getTableDataSql)
        cur.execute(getTableDataSql)
        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            logging.debug(f"No parcel peers found in {parcelTable} within",
                          "{distance} meters from parcel {pid}")
        return data

    except Exception as err:
        logging.debug("Did not find data, please select the right",
                      "database and table: ", err)
        return data.append('Ended with no data')


# Parcel information

def getParcelByLocation(parcelTable, lon, lat, withGeometry=False):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    try:
        logging.debug("start queries")
        getTableSrid = f"""
            SELECT srid FROM geometry_columns
            WHERE f_table_name = '{parcelTable}'"""
        logging.debug(getTableSrid)
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]
        logging.debug(srid)
        getCropCodes = f"""
            SELECT cropname, cropcode, codetype FROM croplabels
            WHERE parceltable = '{parcelTable}'"""
        cur.execute(getCropCodes)
        row = cur.fetchone()
        cropname = row[0]
        cropcode = row[1]
        codetype = row[2]
        logging.debug(row)

        if withGeometry:
            geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        getTableDataSql = f"""
            SELECT ogc_fid, {cropname} as cropname, {cropcode} as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat
            FROM {parcelTable}
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
            logging.debug(f"No parcel found in {parcelTable} that intersects",
                          f"with point ({lon}, {lat})")
        logging.debug(data)
        return data

    except Exception as err:
        logging.debug("Did not find data, please select the right database",
                      "and table: ", err)
        return data.append('Ended with no data')


def getParcelById(parcelTable, parcelid, withGeometry=False):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    try:
        logging.debug("start queries")
        getTableSrid = f"""
            SELECT srid FROM geometry_columns
            WHERE f_table_name = '{parcelTable}'"""
        logging.debug(getTableSrid)
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]
        logging.debug(srid)
        getCropCodes = f"""
            SELECT cropname, cropcode, codetype FROM croplabels
            WHERE parceltable = '{parcelTable}'"""
        cur.execute(getCropCodes)
        row = cur.fetchone()
        cropname = row[0]
        cropcode = row[1]
        # codetype = row[2]

        if withGeometry:
            geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        getTableDataSql = f"""
            SELECT ogc_fid, {cropname} as cropname, {cropcode} as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat
            FROM {parcelTable}
            WHERE ogc_fid = {parcelid};
        """

        #  Return a list of tuples
        cur.execute(getTableDataSql)
        rows = cur.fetchall()

        data.append(tuple(etup.name for etup in cur.description))
        if len(rows) > 0:
            for r in rows:
                data.append(tuple(r))
        else:
            logging.debug(
                f"No parcel found in {parcelTable} with id ({parcelid}).")
        return data

    except Exception as err:
        logging.debug("Did not find data, please select the right database",
                      "and table: ", err)
        return data.append('Ended with no data')


def getParcelsByPolygon(parcelTable, polygon, withGeometry=False,
                        only_ids=True):
    poly = polygon.replace('_', ' ').replace('-', ',')

    conn = psycopg2.connect(conn_str)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = []

    try:
        print("start queries")
        getTableSrid = f"""
            SELECT srid FROM geometry_columns
            WHERE f_table_name = '{parcelTable}'"""
        print(getTableSrid)
        cur.execute(getTableSrid)
        srid = cur.fetchone()[0]
        print(srid)
        getCropCodes = f"""
            SELECT cropname, cropcode, codetype FROM croplabels
            WHERE parceltable = '{parcelTable}'"""
        cur.execute(getCropCodes)
        row = cur.fetchone()
        cropname = row[0]
        cropcode = row[1]
        # codetype = row[2]

        if withGeometry:
            geometrySql = ", st_asgeojson(wkb_geometry) as geom"
        else:
            geometrySql = ""

        if only_ids:
            selectSql = f"ogc_fid{geometrySql}"
        else:
            selectSql = f"""ogc_fid, {cropname} as cropname, {cropcode} as cropcode,
                st_srid(wkb_geometry) as srid{geometrySql},
                st_area(wkb_geometry) as area,
                st_X(st_transform(st_centroid(wkb_geometry), 4326)) as clon,
                st_Y(st_transform(st_centroid(wkb_geometry), 4326)) as clat"""

        getTableDataSql = f"""
            SELECT {selectSql}
            FROM {parcelTable}
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
            print(f"No parcel found in {parcelTable} that intersects",
                  "with the polygon.")
        return data

    except Exception as err:
        print("Did not find data, please select the right database and table: ",
              err)
        return data.append('Ended with no data')
