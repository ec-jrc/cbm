#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" chipRipper.py -- A routine to extract a small subset from imagery in S3 object storage.
                               Essential part of DIAS functionality for CAP Checks by Monitoring
    Author: Guido Lemoine, European Commission, Joint Research Centre
    License: see git repository
    Version 2.1 - 2020-03-17

    Revisions in 1.0 - 2019-10-31
    - Factored out from chipS2Extractor, to prepare for parallel ssh calls
    -
    Revisions in 2.0:
    - Write chips to subdirectory with unique name (for caching)
    -
    Revisions in 2.1:
    - lut and bands parameter handling
    -
    Revisions in 2.2 by Konstantinos Anastasakis:
    - Add main function
"""
import os
import sys
import platform
import json

import logging

from osgeo import ogr
from osgeo import osr
import boto3

import numpy as np

import rasterio
from rasterio.mask import mask
from rasterio.session import AWSSession

from concurrent.futures import ProcessPoolExecutor, as_completed

from scripts.image_chips import download_with_boto3 as dwb

# logging.basicConfig(filename=os.path.basename(sys.argv[0]).replace(
#     '.py', '.log'), filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def main(lon, lat, reference, unique_dir, lut, bands, plevel):
    lut = lut.split('_')
    bands = bands.split('_')
    try:
        flut = [float(lt) for lt in lut]
    except Exception:
        logging.error(f"LUT {lut} does not translate to array of floats")
        flut = [5.0, 95.0]

    if float(lat) > 0.0:
        outCRS = int("326{}".format(reference.split('_')[5][1:3]))
    else:
        outCRS = int("327{}".format(reference.split('_')[5][1:3]))

    features = createPolygon(lon, lat, 1280, 1280, outCRS)
    # print(features)
    if generateChip(reference, features, outCRS,
                    unique_dir, flut, bands, plevel):
        logging.debug(f"Chip generated for {reference}")
    else:
        logging.debug(f"No chip generated for {reference}")


# Configure S3 access (-> to config loading)
def getSubset(fkey, features, lut, fixscale=False):
    try:
        flut = [float(l) for l in lut]
        logging.debug(flut)
    except:
        logging.error("Error converting LUT to float values")
        flut = [5.0, 95.0]

    BUCKET = 'DIAS'
    access_key = 'anystring'
    secret_key = 'anystring'

    session = boto3.Session(aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key)

    with rasterio.Env(AWSSession(session), AWS_S3_ENDPOINT='data.cloudferro.com', AWS_HTTPS='NO', AWS_VIRTUAL_HOSTING=False) as env:
        with rasterio.open(f"/vsis3/{BUCKET}/{fkey}") as src:
            out_image, out_transform = mask(
                src, features, crop=True, pad=False, all_touched=False)
            # print(out_image.shape)
            if not fixscale:
                w_low = np.percentile(out_image, flut[0])
                w_high = np.percentile(out_image, flut[1])
            else:
                w_low = flut[0]
                w_high = flut[1]

            if w_low < w_high:
                chip_set = np.clip(255 * (out_image - w_low) /
                                   (w_high - w_low), 0, 255).astype(np.uint8)
            else:
                # Degenerate chips will be zero filled
                chip_set = np.clip(255 * (out_image - w_low),
                                   0, 255).astype(np.uint8)

    return chip_set, out_transform


def bandSelect(bands, plevel, mgrs_tile, full_tstamp):

    b10 = ['B02', 'B03', 'B04', 'B08']
    b20 = ['B05', 'B06', 'B07', 'B8A', 'B11', 'B12']

    bdict = {}

    for k in bands:
        bdict[k] = '10m' if k in b10 else '20m'

    selection = {}

    if plevel == 'LEVEL2A':
        for k in bands:
            v = bdict.get(k)
            selection[k] = 'R{}/{}_{}_{}_{}.jp2'.format(
                v, mgrs_tile, full_tstamp, k, v)
    else:
        for k in bands:
            selection[k] = '{}_{}_{}.jp2'.format(mgrs_tile, full_tstamp, k)

    logging.debug(selection)

    return selection


def generateChip(reference, features, outCRS, dumpdir, lut, bands, plevel):

    if plevel == 'LEVEL2A':
        rootpath = 'Sentinel-2/MSI/L2A'
    elif plevel == 'LEVEL1C':
        rootpath = 'Sentinel-2/MSI/L1C'
    else:
        logging.debug(f"No data for level {plevel}")
        return False

    logging.debug(f"Search path: {rootpath}")

    obstime = reference.split('_')[2][0:8]
    obs_path = f"{obstime[0:4]}/{obstime[4:6]}/{obstime[6:8]}"

    mgrs_tile = reference.split('_')[5]
    full_tstamp = reference.split('_')[2]

    # We need to check the GRANULE directory to understand where image data is located
    # CREODIAS
    s3path = f"{rootpath}/{obs_path}/{reference}/GRANULE/"

    flist = dwb.listFileFromS3(s3path)

    if len(flist) == 0:
        logging.debug(f"No file found at {s3path}")
        return False

    # We want 3 image files only, e.g. to create NDVI and have some idea about local image quality
    s3subdir = flist[1].replace(s3path, '').split('/')[0]

    selection = bandSelect(bands, plevel, mgrs_tile, full_tstamp)

    file_set = {}

    for k in selection.keys():
        s = selection.get(k)

        if len(dwb.listFileFromS3(f"{s3path}{s3subdir}/IMG_DATA/{s}")) == 1:
            logging.debug(f"{platform.node()}: Image {s} found in bucket")
            file_set[k] = f"{s3path}{s3subdir}/IMG_DATA/{s}"
        else:
            logging.debug(f"{platform.node()}: Image {s} not found in bucket")
            return False

    # Get the chip in this image' footprint

    chip_set = {}

    # Get multiple band concurrently, because they are in separate files on S3
    with ProcessPoolExecutor(len(bands)) as executor:
        jobs = {}
        i = 0
        for b in bands:
            if len(lut) == 2:
                job = executor.submit(
                    getSubset, file_set.get(b), features, lut)
                jobs[job] = b
            elif len(lut) == 6:
                job = executor.submit(getSubset, file_set.get(
                    b), features, lut[i:i + 2], True)
                jobs[job] = b
                i = i + 2

        for job in as_completed(jobs):
            b = jobs[job]
            chip_set[b] = job.result()

    falseColor = None
    # Dump a composite to disk
    if not os.path.exists(dumpdir):
        logging.debug(f"Creating {dumpdir} on slave")
        os.makedirs(dumpdir)

    logging.debug(chip_set.keys())

    falseColor = rasterio.open(f"{dumpdir}/{reference}.png", 'w', driver='PNG',
                               width=128, height=128,
                               count=3,
                               crs=outCRS,
                               transform=chip_set.get(bands[0])[1],
                               dtype=np.uint8
                               )
    falseColor.write(chip_set.get(bands[0])[0][0, :, :], 1)  # R
    falseColor.write(chip_set.get(bands[1])[0][0, :, :], 2)  # G
    falseColor.write(chip_set.get(bands[2])[0][0, :, :], 3)  # B
    falseColor.close()
    logging.debug(f"{dumpdir}/{reference}.png written.")
    return True


def createPolygon(lon, lat, dx, dy, outCRS):
    # Set up a chip that is centered around the point of interest
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)

    target = osr.SpatialReference()
    target.ImportFromEPSG(outCRS)

    transform = osr.CoordinateTransformation(source, target)

    point = ogr.CreateGeometryFromWkt(f"POINT ({lon} {lat})")
    point.Transform(transform)

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(point.GetX() - dx / 2, point.GetY() + dx / 2)
    ring.AddPoint(point.GetX() - dx / 2, point.GetY() - dx / 2)
    ring.AddPoint(point.GetX() + dx / 2, point.GetY() - dx / 2)
    ring.AddPoint(point.GetX() + dx / 2, point.GetY() + dx / 2)
    ring.AddPoint(point.GetX() - dx / 2, point.GetY() + dx / 2)

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    # format for use in rasterio
    return [json.loads(poly.ExportToJson())]


if __name__ == "__main__":
    lon, lat = sys.argv[1], sys.argv[2]
    reference = sys.argv[3]
    unique_dir = sys.argv[4]
    lut = sys.argv[5].split('_')
    try:
        flut = [float(l) for l in lut]
    except:
        logging.error(f"LUT {lut} does not translate to array of floats")
        flut = [5.0, 95.0]

    bands = sys.argv[6].split('_')

    plevel = sys.argv[7]
    if float(lat) > 0.0:
        outCRS = int("326{}".format(reference.split('_')[5][1:3]))
    else:
        outCRS = int("327{}".format(reference.split('_')[5][1:3]))

    features = createPolygon(lon, lat, 1280, 1280, outCRS)
    # print(features)
    if generateChip(reference, features, outCRS, unique_dir, flut, bands, plevel):
        logging.debug(f"Chip generated for {reference}")
    else:
        logging.debug(f"No chip generated for {reference}")
