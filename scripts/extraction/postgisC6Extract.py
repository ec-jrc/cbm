#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Version   : 

import time
import sys
import os
import io
import json

import psycopg2
import psycopg2.extras
import rasterio
import pandas as pd
from rasterstats import zonal_stats
from datetime import datetime

import download_with_boto3 as dwb

start = time.time()

# Rev 1.1. configuration parsing from json
with open('s3_config.json', 'r') as f:
    s3config = json.load(f)
s3config = s3config['s3']

with open('db_config_c6.json', 'r') as f:
    dbconfig = json.load(f)
dbconfig = dbconfig['database']

# Input data base is postgis
connString = "host={} dbname={} user={} port={} password={}".format(
    dbconfig['connection']['host'], dbconfig['connection']['dbname'],
    dbconfig['connection']['dbuser'], dbconfig['connection']['port'],
    dbconfig['connection']['dbpasswd'])

inconn = psycopg2.connect(connString)
if not inconn:
    print("No in connection established")
    sys.exit(1)

incurs = inconn.cursor()

srid = -1

sridSql = "select srid from geometry_columns where f_table_name = '{}';"

try:
    incurs.execute(sridSql.format(dbconfig['tables']['parcel_table']))
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

# Get the first image records that is not yet processed
imagesql = """
    SELECT id, reference, obstime from dias_catalogue, {}
    WHERE footprint && wkb_geometry and {} = '{}'
    And obstime between '{}' and '{}'
    And status ='ingested'
    And card='c6' order by obstime asc limit 1"""

updateSql = """update dias_catalogue set status='{}' where id = {} and status = '{}'"""

try:
    incurs.execute(imagesql.format(
        dbconfig['tables']['aoi_table'], dbconfig['args']['aoi_field'],
        dbconfig['args']['name'], dbconfig['args']['startdate'],
        dbconfig['args']['enddate']))
    result = incurs.fetchone()
    if not result:
        print("No images with status 'ingested' found")
        inconn.close()
        sys.exit(1)
    else:
        oid = result[0]
        reference = result[1]
        obstime = result[2]
    # Fails if this record is changed in the meantime
    incurs.execute(updateSql.format('inprogress', oid, 'ingested'))
    inconn.commit()
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
    inconn.close()
    sys.exit(1)

# Count parcels inside this image footprint
parcelcountsql = """
    SELECT count(es.ogc_fid)
    FROM {} es, dias_catalogue dias, {} aoi
    WHERE es.wkb_geometry && st_transform(dias.footprint, {})
    And es.wkb_geometry && st_transform(st_buffer(aoi.wkb_geometry::geography, 1000)::geometry, {})
    And st_area(es.wkb_geometry) > 3000.0
    And aoi.{} = '{}' And dias.id = {}
    -- and es.ogc_fid not in (select distinct pid from {} where obsid = {})
    """

incurs.execute(parcelcountsql.format(
    dbconfig['tables']['parcel_table'],
    dbconfig['tables']['aoi_table'], srid, srid,
    dbconfig['args']['aoi_field'], dbconfig['args']['name'],
    oid, dbconfig['tables']['results_table'], oid))

nrecs = incurs.fetchone()

# If no parcels inside, we can stop
if nrecs[0] == 0:
    print("No parcels inside image bounds")
    incurs.execute(updateSql.format('No_parcels', oid, 'inprogress'))
    inconn.commit()
    incurs.close()
    inconn.close()
    sys.exit(1)

# Copy input data from S3 to local disk
# CREODIAS
s3path = "Sentinel-1/SAR/CARD-COH6/{}/{}/{}.tif".format(
    datetime.strftime(obstime, '%Y/%m/%d'), reference, reference)

# SOBLOO
# s3path = "{}/SLC/{}/".format(reference.split('_')[0], reference)

flist = dwb.listFileFromS3(s3path)

if not flist:
    print("Resource {} not available in S3 storage (FATAL)".format(s3path))
    incurs.execute(updateSql.format('C6_nopath', oid, 'inprogress'))
    inconn.commit()
    incurs.close()
    inconn.close()
    sys.exit(1)

s3path = flist[0]

fpath = 'data/{}'.format(s3path.split('/')[-1])

outsrid = -1

if dwb.getFileFromS3(s3path, fpath) == 0:
    print("Resource {} not available in S3 storage (FATAL)".format(s3path))
    incurs.execute(updateSql.format('No S3 C6 img', oid, 'inprogress'))
    inconn.commit()
    incurs.close()
    inconn.close()
    sys.exit(1)
else:
    # Only if the header file is present can we open the image to
    #   check its projection
    with rasterio.open(fpath) as src:
        outsrid = src.crs.to_epsg()

print('Out SRID: ', outsrid)

# Open a connection to save results
outconn = psycopg2.connect(connString)
if not outconn:
    print("No out connection established")
    incurs.execute(updateSql.format('no_out_conn', oid, 'inprogress'))
    inconn.commit()
    incurs.close()
    inconn.close()
    sys.exit(1)

# Get the parcel polygon in this image' footprint

incurs.close()
# Open a named cursor
incurs = inconn.cursor(name='fetch_image_coverage',
                       cursor_factory=psycopg2.extras.DictCursor)

parcelsql = """
    SELECT es.ogc_fid, ST_AsGeoJSON(st_transform(es.wkb_geometry, {}))::json
    FROM {} es, dias_catalogue dias, {} aoi
    WHERE es.wkb_geometry && st_transform(dias.footprint, {})
    And es.wkb_geometry && st_transform(st_buffer(aoi.wkb_geometry::geography,
        1000)::geometry, {})
    And st_area(es.wkb_geometry) > 3000.0
    And aoi.{} = '{}'
    And dias.id = {}
    -- and es.ogc_fid not in (select distinct pid from {} where obsid = {})
    """

incurs.execute(parcelsql.format(
    outsrid, dbconfig['tables']['parcel_table'],
    dbconfig['tables']['aoi_table'], srid, srid,
    dbconfig['args']['aoi_field'], dbconfig['args']['name'],
    oid, dbconfig['tables']['results_table'], oid))

sqlload = time.time() - start
print("Images loaded and {} features selected from database in {} seconds".format(
    nrecs[0], sqlload))

nrows = {}
nrows['VV'] = 0
nrows['VH'] = 0

affine = {}
array = {}

bands = ['VV', 'VH']

with rasterio.open(fpath) as src:
    for b in bands:
        affine[b] = src.transform
        array[b] = src.read(bands.index(b) + 1)


while True:  # nrows['VV'] < 2:
    rowset = incurs.fetchmany(size=2000)

    if not rowset:
        break

    features = {"type": "FeatureCollection",
                "features": [{"type": "feature", "geometry": f[1],
                              "properties": {"pid": int(f[0])}} for f in rowset]}

    for b in bands:

        zs = zonal_stats(features, array[b], affine=affine[b], stats=[
            "count", "mean", "std", "min", "max",
            "percentile_25", "percentile_50", "percentile_75"], prefix="",
            nodata=0, geojson_out=True)

        df = pd.DataFrame(zs)

        df = pd.DataFrame.from_dict(df.properties.to_dict(), orient='index')

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
                    outcurs.copy_from(
                        s_buf, dbconfig['tables']['results_table'],
                        columns=tuple(df_columns), sep=',')
                    outconn.commit()
                except psycopg2.IntegrityError as e:
                    print("insert statement {} contains duplicate index".format(
                        insert_stmt))
                # except Error as e:
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

if os.path.exists(fpath):
    os.remove(fpath)

print("Total time required for {} features and {} bands: {} seconds".format(
    nrows['VV'], len(bands), time.time() - start))
