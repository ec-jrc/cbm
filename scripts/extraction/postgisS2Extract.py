#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Version   : 


""" postgisS2Extract_ext.py:
        A routine to extract zonal statistics from imagery in S3 object storage.
        Assumes postgis data base use for scene metadata, features to extract and result storage.
        Essential part of DIAS functionality for CAP Checks by Monitoring
    Author: Guido Lemoine, European Commission, Joint Research Centre
    License: see git repository
    Version 1.1 - 2019-06-27

    Revisions in 1.1:
    - Externalize configuration parameters to postgisS2Extract_ext.json
    - Get parcel_table srid and image srid dynamically
    - Exit if no records found for processing
    - Resolve missing data accounting
    - Housekeeping
    Revisions in 1.2 - 2020-12-11 Konstantinos Anastasakis:
    - Code cleanup (flake8)

"""

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

import download_with_boto3 as dwb

start = time.time()

# Rev 1.1. configuration parsing from json
with open('s3_config.json', 'r') as f:
    s3config = json.load(f)
s3config = s3config['s3']

with open('db_config_s2.json', 'r') as f:
    dbconfig = json.load(f)
dbconfig = dbconfig['database']

# Input data base is postgis
connString = "host={} dbname={} user={} port={} password={}".format(
    dbconfig['connection']['host'], dbconfig['connection']['dbname'],
    dbconfig['connection']['dbuser'], dbconfig['connection']['port'],
    dbconfig['connection']['dbpasswd'])

# print(connString)

inconn = psycopg2.connect(connString)
if not inconn:
    print("No in connection established")
    sys.exit(1)

outconn = psycopg2.connect(connString)
if not outconn:
    print("No out connection established")
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

# Get the first image record that is not yet processed
imagesql = """
    SELECT id, reference, obstime from dias_catalogue, {}
    WHERE footprint && wkb_geometry and {} = '{}'
    And obstime between '{}' and '{}'
    And status ='ingested' and card='s2' ORDER by obstime asc limit 1
    """

updateSql = """
    UPDATE dias_catalogue set status='{}'
    WHERE id = {} and status = '{}'"""

try:
    incurs.execute(imagesql.format(
        dbconfig['tables']['aoi_table'],
        dbconfig['args']['aoi_field'], dbconfig['args']['name'],
        dbconfig['args']['startdate'], dbconfig['args']['enddate']))
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

parcelcountsql = """
    SELECT count(es.ogc_fid)
    FROM {} es, dias_catalogue dias, {} aoi
    WHERE es.wkb_geometry && st_transform(dias.footprint, {})
    And es.wkb_geometry && st_transform(st_buffer(aoi.wkb_geometry::geography,
        1000)::geometry, {})
    And st_area(es.wkb_geometry) > 3000.0
    And aoi.{} = '{}' and dias.id = {}
    """

incurs.execute(parcelcountsql.format(
    dbconfig['tables']['parcel_table'],
    dbconfig['tables']['aoi_table'], srid, srid,
    dbconfig['args']['aoi_field'], dbconfig['args']['name'],
    oid, dbconfig['tables']['results_table'], oid))

nrecs = incurs.fetchone()

# If no parcels inside, we can stop
if nrecs[0] == 0:
    print("Image {} contains no parcels (FATAL)".format(reference))
    incurs.execute(updateSql.format('no_parcels', oid, 'inprogress'))
    inconn.commit()
    incurs.close()
    inconn.close()
    sys.exit(1)

# Copy input data from S3 to local disk
# SOBLOO
# rootpath = '{}/L1C'.format(reference.split('_')[0])
# CREODIAS
rootpath = 'Sentinel-2/MSI/L2A'

obstime = reference.split('_')[2][0:8]
obs_path = "{}/{}/{}".format(obstime[0:4], obstime[4:6], obstime[6:8])

mgrs_tile = reference.split('_')[5]
full_tstamp = reference.split('_')[2]

# There was an issue with the manifest.safe sometime during 2018, and we need
#   to check the GRANULE directory to understand where image data is located
# CREODIAS
s3path = "{}/{}/{}/GRANULE/".format(rootpath, obs_path, reference)
# SOBLOO
# s3path = "{}/{}/{}.SAFE/GRANULE/".format(rootpath, reference, reference.replace('MSIL1C', 'MSIL2A'))

flist = dwb.listFileFromS3(s3path)
# print(flist)

if not flist:
    print("Resource {} not available in S3 storage (FATAL)".format(s3path))
    incurs.execute(updateSql.format('S2_nopath', oid, 'inprogress'))
    inconn.commit()
    incurs.close()
    inconn.close()
    sys.exit(1)

# We want 3 image files only, e.g. to create NDVI and have some idea about local image quality
# SOBLOO does not produce 10 m L2A bands and only B8A (not B08)!
s3subdir = flist[1].replace(s3path, '').split('/')[0]

print(s3path)
print(flist[1])
print(s3subdir)

selection = {'B4': '{}/{}_{}_{}_{}.jp2'.format('R10m', mgrs_tile, full_tstamp, 'B04', '10m'),
             'B8': '{}/{}_{}_{}_{}.jp2'.format('R10m', mgrs_tile, full_tstamp, 'B08', '10m'),
             'SC': '{}/{}_{}_{}_{}.jp2'.format('R20m', mgrs_tile, full_tstamp, 'SCL', '20m')
             }

file_set = {}

for k in selection.keys():
    s = selection.get(k)
    fpath = "data/{}".format(s.split('/')[-1])
    alt_s = s.replace('0m/', '0m/L2A_')

    if dwb.getFileFromS3('{}{}/IMG_DATA/{}'.format(s3path, s3subdir, s), fpath) == 1:
        print("Image {} found in bucket".format(s))
        file_set[k] = fpath
    elif dwb.getFileFromS3('{}{}/IMG_DATA/{}'.format(s3path, s3subdir, alt_s), fpath) == 1:
        # LEVEL2AP has another naming convention.
        print("Image {} found in bucket".format(alt_s))
        file_set[k] = fpath
    else:
        print("Neither Image {} nor {} found in bucket".format(s, alt_s))
        incurs.execute(updateSql.format(
            '{} notfound'.format(k), oid, 'inprogress'))
        inconn.commit()
        incurs.close()
        inconn.close()
        sys.exit(1)


# Get the parcel polygon in this image' footprint
print(file_set)

outsrid = int('326{}'.format(mgrs_tile[1:3]))

incurs.close()

outconn = psycopg2.connect(connString)
if not outconn:
    print("No out connection established")
    sys.exit(1)

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
    And aoi.{} = '{}' and dias.id = {}
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
for k in file_set.keys():
    nrows[k] = 0

affine = {}
array = {}

bands = file_set.keys()

for b in bands:
    with rasterio.open(file_set.get(b)) as src:
        affine[b] = src.transform
        array[b] = src.read(1)


while True:
    rowset = incurs.fetchmany(size=2000)

    if not rowset:
        break

    features = {"type": "FeatureCollection",
                "features": [{"type": "feature", "geometry": f[1],
                              "properties": {"pid": int(f[0])}} for f in rowset]}

    for b in bands:

        zs = zonal_stats(
            features, array[b], affine=affine[b],
            stats=["count", "mean", "std", "min", "max",
                   "percentile_25", "percentile_50", "percentile_75"],
            prefix="", nodata=0, geojson_out=True)

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
                except psycopg2.IntegrityError:
                    print("insert statement {} contains duplicate index")
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
    print("Removing {}".format(fpath))
    os.remove(fpath)

for f in file_set.keys():
    if os.path.exists(file_set.get(f)):
        print("Removing {}".format(file_set.get(f)))
        os.remove(file_set.get(f))

print("Total time required for {} features and {} bands: {} seconds".format(
    nrows.get('B8'), len(bands), time.time() - start))
