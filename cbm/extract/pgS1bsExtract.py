#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import time
import sys
import os
import io
import json
import psycopg2
import psycopg2.extras
import rasterio
from rasterstats import zonal_stats
from datetime import datetime
import pandas as pd

from cbm.utils import config
from cbm.datas import db, object_storage

def extractS1bs(startdate, enddate):
    start = time.time()
    frootpath = 'tmp'

    values = config.read()
    dsc = values['set']['dataset']
    dias_catalogue = values['dataset'][dsc]['tables']['dias_catalog']
    parcels_table = values['dataset'][dsc]['tables']['parcels']
    results_table = values['dataset'][dsc]['tables']['s1']

    inconn = db.connection()
    if not inconn:
        print("No in connection established")
        sys.exit(1)

    incurs = inconn.cursor()
    srid = -1
    sridSql = "select srid from geometry_columns where f_table_name = '{}';"

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

    print("Parcel srid = ", srid)

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
            inconn.commit()

    print(reference)
    obstime = reference.split('_')[2][0:8]
    print(obstime)
    obs_path = "{}/{}/{}".format(obstime[0:4], obstime[4:6], obstime[6:8])
    print(obs_path)

    mgrs_tile = reference.split('_')[5]
    full_tstamp = reference.split('_')[2]

    # Copy input data from S3 to local disk
    dias = values['s3']['dias']
    if dias in ['EOSC', 'CREODIAS']:
        rootpath = 'Sentinel-1/SAR/CARD-BS'
        print(datetime.strptime(obstime, '%Y/%m/%d'), reference)
        s3path = '{}/{}/{}/{}.data/Gamma0_VV.img'.format(
            rootpath, datetime.strftime(obstime, '%Y/%m/%d'), reference, reference)
    elif dias == 'SOBLOO':
        s3path = '{}/GRD/{}/{}.data/Gamma0_VV.img'.format(
            reference.split('_')[0], reference, reference)

    fpath = f'{frootpath}/{reference}_VV.img'
    outsrid = -1

    if object_storage.get_file(s3path, fpath) == 0:
        print("Resource {} not available in S3 storage (FATAL)".format(s3path))
        incurs.execute(updateSql.format('No S3 VV img', oid,'inprogress'))
        inconn.commit()
        incurs.close()
        inconn.close()
        sys.exit(1)

    s3path = s3path.replace('.img', '.hdr')
    fpath = f'{frootpath}/{reference}_VV.hdr'

    if object_storage.get_file(s3path, fpath) == 0:
        print("Resource {} not available in S3 storage (FATAL)".format(s3path))
        incurs.execute(updateSql.format('No S3 VV hdr', oid,'inprogress'))
        inconn.commit()
        incurs.close()
        inconn.close()
        sys.exit(1)
    else:
        # Only if the header file is present can we open the image to check its projection
        with rasterio.open(fpath.replace('hdr', 'img')) as src:
            outsrid = cbm.crs.to_epsg()

    print('Out SRID: ', outsrid)

    if dias in ['EOSC', 'CREODIAS']:
        rootpath = 'Sentinel-1/SAR/CARD-BS'
        s3path = '{}/{}/{}/{}.data/Gamma0_VH.img'.format(
            rootpath, datetime.strftime(obstime, '%Y/%m/%d'), reference, reference)
    elif dias == 'SOBLOO':
        s3path = '{}/GRD/{}/{}.data/Gamma0_VH.img'.format(
            reference.split('_')[0], reference, reference)
    fpath = f'{frootpath}/{reference}_VH.img'

    if object_storage.get_file(s3path, fpath) == 0:
        print("Resource {} not available in S3 storage (FATAL)".format(s3path))
        incurs.execute(updateSql.format('No S3 VH img', oid,'inprogress'))
        inconn.commit()
        incurs.close()
        inconn.close()
        sys.exit(1)

    s3path = s3path.replace('.img', '.hdr')
    fpath = f'{frootpath}/{reference}_VH.hdr'

    if object_storage.get_file(s3path, fpath) == 0:
        print("Resource {} not available in S3 storage (FATAL)".format(s3path))
        incurs.execute(updateSql.format('No S3 VH hdr', oid,'inprogress'))
        inconn.commit()
        incurs.close()
        inconn.close()
        sys.exit(1)


    # Open a connection to save results
    outconn = psycopg2.connect(connString)
    if not outconn:
        print("No out connection established")
        incurs.execute(updateSql.format('no_out_conn', oid,'inprogress'))
        inconn.commit()
        incurs.close()
        inconn.close()
        sys.exit(1)

    # Get the parcel polygon in this image' footprint

    incurs.close()
    # Open a named cursor
    incurs = inconn.cursor(name='fetch_image_coverage', cursor_factory=psycopg2.extras.DictCursor)

    dataset = config.get_value(['set', 'dataset'])
    pid_column = config.get_value(['dataset', dataset, 'columns', 'parcels_id'])

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
    print("Images loaded and nrecs[0] features selected from database in {} seconds".format(sqlload))

    nrows = {}
    nrows['VV']=0
    nrows['VH']=0

    affine = {}
    array = {}

    bands = ['VV', 'VH']

    for b in bands:
        with rasterio.open(f'{frootpath}/{reference}_{b}.img') as src:
            affine[b] = cbm.transform
            array[b] = cbm.read(1)

    while True:
        rowset = incurs.fetchmany(size=2000)

        if not rowset:
            break

        features = { "type": "FeatureCollection",
            "features": [{"type": "feature", "geometry": f[1], "properties": {"pid": int(f[0])}} for f in rowset]}

        for b in bands:

            zs = zonal_stats(features, array[b], affine=affine[b], stats=["count", "mean", "std", "min", "max", "percentile_25", "percentile_50", "percentile_75"], prefix="", nodata=0, geojson_out=True)

            df = pd.DataFrame(zs)

            df = pd.DataFrame.from_dict(df.properties.to_dict(), orient='index')

            df['obsid'] = oid
            df['band'] = b

            df.rename(index=str, columns={"percentile_25": "p25", "percentile_50": "p50","percentile_75": "p75"}, inplace=True)

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
                    #print(tuple(df_columns))
                    try:
                        #psycopg2.extras.execute_batch(outcurs, insert_stmt, df.values)
                        outcurs.copy_from(s_buf, dbconfig['tables']['results_table'], columns = tuple(df_columns), sep = ',')
                        outconn.commit()
                    except psycopg2.IntegrityError as e:
                        print("insert statement {} contains duplicate index".format(insert_stmt))
                    #except Error as e:
                    #    print(e)
                    finally:
                        outcurs.close()
                else:
                    print("No valid data in block {}".format(nrows[b]))

    outconn.close()

    incurs.close()

    incurs = inconn.cursor()

    try:
        incurs.execute(updateSql.format('extracted', oid, 'inprogress'))
        inconn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        inconn.close()
        if outconn:
            outconn.close()

    incurs.close()
    inconn.close()

    fpath = f'{frootpath}/{reference}_VV.img'

    if os.path.exists(fpath):
        os.remove(fpath)
        os.remove(fpath.replace('.img', '.hdr'))

    fpath = f'{frootpath}/{reference}_VH.img'

    if os.path.exists(fpath):
        os.remove(fpath)
        os.remove(fpath.replace('.img', '.hdr'))

    print("Total time required for {} features and {} bands: {} seconds".format(nrows['VV'], len(bands), time.time() - start))
