#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

""" postgisS2Extract.py --
        A routine to extract zonal statistics from imagery in S3 object storage.
        Assumes postgis data base use for scene metadata, features to extract
        and result storage.
        Essential part of DIAS functionality for CAP Checks by Monitoring
    Author: Guido Lemoine, European Commission, Joint Research Centre
    License: see git repository
    Version 1.3 - 2020-02-03

    Revisions in 1.3 (2020-7-12):
    By: Konstantinos Anastasakis, European Commission, Joint Research Centre
    - Configure to be compatible with the graphical notebooks panels

    Revision in 1.2 (2020-02-03)
    - oid select and status update in transaction

    Revisions in 1.1 (2019-06-27):
    - Externalize configuration parameters to postgisS2Extract_ext.json
    - Get parcel_table srid and image srid dynamically
    - Exit if no records found for processing
    - Resolve missing data accounting
    - Housekeeping


"""

import os
import io
import sys
import time
import pandas as pd
import psycopg2
import psycopg2.extras
import rasterio
from rasterstats import zonal_stats

from cbm.utils import config
from cbm.datas import db, object_storage


def main(startdate, enddate, parcels_table=None, results_table=None,
         dias=None, dias_catalogue=None):
    start = time.time()

    values = config.read()
    dsc = values['set']['dataset']
    if dias_catalogue is None:
        dias_catalogue = values['dataset'][dsc]['tables']['dias_catalog']
    if parcels_table is None:
        parcels_table = values['dataset'][dsc]['tables']['parcels']
    if results_table is None:
        results_table = values['dataset'][dsc]['tables']['s2']
    if dias is None:
        dias = values['s3']['dias']

    inconn = db.connection()
    if not inconn:
        print("No in connection established")
        sys.exit(1)

    outconn = db.connection()
    if not outconn:
        print("No out connection established")
        sys.exit(1)

    incurs = inconn.cursor()
    srid = -1
    sridSql = "SELECT srid FROM geometry_columns WHERE f_table_name = '{}';"

    try:
        incurs.execute(sridSql.format(parcels_table))
        result = incurs.fetchone()
        if not result:
            print("{} does not exist or is not a spatial table")
        else:
            srid = result[0]
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        inconn.close()
        sys.exit(1)
    # print("Parcel srid = ", srid)

    # Get the first image record that is not yet processed
    imagesql = f"""
    SELECT id, reference, obstime FROM {dias_catalogue}
    WHERE obstime between '{startdate}' And '{enddate}'
    And status ='ingested' And card = 's2'
    ORDER by obstime asc LIMIT 1
    """
    updateSql = """
    UPDATE {} SET status='{}'
    WHERE id = {} And status = '{}'
    """

    with inconn:
        with inconn.cursor() as trans_cur:
            trans_cur.execute(imagesql)
            result = trans_cur.fetchone()
            if not result:
                print("All signatures for the given dates have been extracted.")
                inconn.close()
                sys.exit(1)
            else:
                oid = result[0]
                reference = result[1]
                obstime = result[2]
            # Fails if this record is changed in the meantime
            trans_cur.execute(updateSql.format(
                dias_catalogue, 'inprogress', oid, 'ingested'))

    obstime = reference.split('_')[2][0:8]
    # print(obstime)
    obs_path = "{}/{}/{}".format(obstime[0:4], obstime[4:6], obstime[6:8])

    mgrs_tile = reference.split('_')[5]
    full_tstamp = reference.split('_')[2]

    # Due to some ESA issues with the manifest.safe sometime during 2018, the GRANULE
    # directory need to be checked to understand where image data is located.
    if dias in ['EOSC', 'CREODIAS']:
        rootpath = 'Sentinel-2/MSI/L2A'
        s3path = "{}/{}/{}/GRANULE/".format(rootpath, obs_path, reference)
    elif dias == 'SOBLOO':
        rootpath = '{}/L1C'.format(reference.split('_')[0])
        s3path = "{}/{}/{}.SAFE/GRANULE/".format(rootpath, reference,
                                                 reference.replace('MSIL1C', 'MSIL2A'))
    elif dias == 'MUNDI':
        from .utils.mundi import get_mundi_s3path
        s3path = get_mundi_s3path(reference, obs_path)

    flist = object_storage.list_files(s3path)
    if not flist:
        print("Resource {} not available in S3 storage (FATAL)".format(s3path))
        incurs.execute(updateSql.format(
            dias_catalogue, 'S2_nopath', oid, 'inprogress'))
        inconn.commit()
        incurs.close()
        inconn.close()
        sys.exit(1)

    # We want 3 image files only, e.g. to create NDVI
    # SOBLOO does not produce 10 m L2A bands and only B8A (not B08)
    s3subdir = flist[1]['Key'].replace(s3path, '').split('/')[0]
    # print(s3path)
    # print(flist[1])
    # print(s3subdir)

    selection = {
        'B4': '{}/{}_{}_{}_{}.jp2'.format(
            'R10m', mgrs_tile, full_tstamp, 'B04', '10m'),
        'B8': '{}/{}_{}_{}_{}.jp2'.format(
            'R10m', mgrs_tile, full_tstamp, 'B08', '10m'),
        'SC': '{}/{}_{}_{}_{}.jp2'.format(
            'R20m', mgrs_tile, full_tstamp, 'SCL', '20m')
    }

    file_set = {}

    # Copy input data from S3 to local disk
    for k in selection.keys():
        s = selection.get(k)
        fpath = f"tmp/{s.split('/')[-1]}"
        alt_s = s.replace('0m/', '0m/L2A_')

        if object_storage.get_file('{}{}/IMG_DATA/{}'.format(
                s3path, s3subdir, s), fpath) == 1:
            #             print("Image {} found in bucket".format(s))
            file_set[k] = fpath
        elif object_storage.get_file('{}{}/IMG_DATA/{}'.format(
                s3path, s3subdir, alt_s), fpath) == 1:
            # LEVEL2AP has another naming convention.
            #             print("Image {} found in bucket".format(alt_s))
            file_set[k] = fpath
        else:
            print("Neither Image {} nor {} found in bucket".format(s, alt_s))
            incurs.execute(updateSql.format(
                dias_catalogue, '{} notfound'.format(k), oid, 'inprogress'))
            inconn.commit()
            incurs.close()
            inconn.close()
            sys.exit(1)

    # Get the parcel polygon in this image' footprint
    print(f"Downloaded '*{file_set['B4'][4:-12]}*' images ...")

    outsrid = int(f'326{mgrs_tile[1:3]}')

    incurs.close()

    outconn = db.connection()
    if not outconn:
        print("No out connection established")
        sys.exit(1)

    # Open a named cursor
    incurs = inconn.cursor(name='fetch_image_coverage',
                           cursor_factory=psycopg2.extras.DictCursor)
    dataset = config.get_value(['set', 'dataset'])
    pid_column = config.get_value(
        ['dataset', dataset, 'columns', 'parcels_id'])

    parcelsql = f"""
    SELECT p.{pid_column}, ST_AsGeoJSON(st_transform(p.wkb_geometry,
        {outsrid}))::json
    FROM {parcels_table} p, {dias_catalogue} dc
    WHERE p.wkb_geometry && st_transform(dc.footprint, {srid})
    And st_area(p.wkb_geometry) > 3000.0
    And dc.id = {oid}
    -- And p.{pid_column} not in (SELECT distinct pid
    --     FROM {results_table} where obsid = {oid})
    """
    incurs.execute(parcelsql)

    sqlload = time.time() - start
    print(f"Features selected from database in {sqlload} seconds")

    nrows = {}
    for k in file_set.keys():
        nrows[k] = 0

    affine = {}
    array = {}

    bands = file_set.keys()

    for b in bands:
        with rasterio.open(file_set.get(b)) as src:
            affine[b] = src.transform
            array[b] = src.read(1)

    print(f"Extracting signatures for '*{file_set['B4'][4:-12]}* images ...'")
    while True:
        rowset = incurs.fetchmany(size=2000)

        if not rowset:
            break

        features = {"type": "FeatureCollection",
                    "features": [{"type": "feature", "geometry": f[1],
                                  "properties": {"pid": int(f[0])}} for f in rowset]}

        for b in bands:

            zs = zonal_stats(features, array[b], affine=affine[b], stats=[
                             "count", "mean", "std", "min", "max",
                             "percentile_25", "percentile_50",
                             "percentile_75"],
                             prefix="", nodata=0, geojson_out=True)

            df = pd.DataFrame(zs)

            df = pd.DataFrame.from_dict(
                df.properties.to_dict(), orient='index')

            df['obsid'] = oid
            df['band'] = b

            df.rename(index=str, columns={
                      "percentile_25": "p25", "percentile_50": "p50",
                      "percentile_75": "p75"}, inplace=True)

            nrows[b] = nrows[b] + len(df)
            # df is the dataframe
            if len(df) > 0:
                df.dropna(inplace=True)
                if len(df.values) > 0:
                    df_columns = list(df)
                    s_buf = io.StringIO()
                    df.to_csv(s_buf, header=False, index=False, sep=',')
                    s_buf.seek(0)
                    outcurs = outconn.cursor()
                    # print(tuple(df_columns))
                    try:
                        #psycopg2.extras.execute_batch(outcurs, insert_stmt, df.values)
                        outcurs.copy_from(s_buf, results_table,
                                          columns=tuple(df_columns), sep=',')
                        outconn.commit()
                    except psycopg2.IntegrityError as e:
                        print(
                            f"insert statement {insert_stmt} contains duplicate index", e)
                    # except Exception as e:
                    #     print(e)
                    finally:
                        outcurs.close()
                else:
                    print(f"No valid data in block {nrows[b]}")

    outconn.close()

    incurs.close()

    incurs = inconn.cursor()

    try:
        incurs.execute(updateSql.format(
            dias_catalogue, 'extracted', oid, 'inprogress'))
        inconn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        inconn.close()
        if outconn:
            outconn.close()

    incurs.close()
    inconn.close()

    print(f"Removing '*{file_set['B4'][4:-12]}*' images.")
    for f in file_set.keys():
        if os.path.exists(file_set.get(f)):
            print(f"Removing {file_set.get(f)}")
            os.remove(file_set.get(f))

    print("Total time required for {} features and {} bands: {} seconds".format(
        nrows.get('B8'), len(bands), time.time() - start))


if __name__ == "__main__":
    main(sys.argv)
