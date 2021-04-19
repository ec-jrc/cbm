#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" backgroundExtract.py -- A routine to extract a small subset from Google,
        Bing or national ortho imagery.

    Author: Guido Lemoine, European Commission, Joint Research Centre
    License: see git repository
    Version 1.2 - 2021-04-14

    Revisions in 1.2: by Konstantinos Anastasakis
    - Updates: pep8 code style paths and html handling
    Revisions in 1.1:
    - Added national orthos
    Revisions in 1.0:
    - Adapted to run as a RESTful service
"""

import os
import glob
import math

import numpy as np
import logging

import rasterio as rio
from rasterio.windows import Window
from rasterio.transform import Affine
from flask import url_for


from osgeo import osr, ogr


def getWindowedExtract(lon, lat, chipSize, chipExtend, unique_dir,
                       tms="Google", format='tif'):
    """Generate an extract from either Google or Bing.
    It uses the WMTS standard to grab and compose,
    which makes it fast (does not depend on DIAS S3 store).
    Arguments:
        on, lat (float): longitude, latitude in decimal degrees
        chipSize (int): size of the chip in pixels
        chipExtend (float): size of the chip in meters
        unique_dir (str): the path for the file to be stored
        tms (str): tile map server
        format (str): File format '.tif' or '.png'
    """
    lon, lat = float(lon), float(lat)
    chipSize = int(chipSize)
    chipExtend = float(chipExtend)

    if os.path.exists(unique_dir):
        # Check which chips are already in the unique_dir
        # (simple form of caching)
        cachedList = glob.glob(f"{unique_dir}/{tms}.tif")

        logging.debug("CACHED")
        logging.debug(cachedList)

        if len(cachedList) == 1:
            logging.debug("No new chips to be processed")
            return 0
    else:
        logging.debug(f"Creating {unique_dir} on host")
        os.makedirs(unique_dir)

    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(lon, lat)
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)

    # Assign this projection to the geometry
    point.AssignSpatialReference(source)
    target = osr.SpatialReference()
    target.ImportFromEPSG(3857)
    transform = osr.CoordinateTransformation(source, target)

    # Reproject the point geometry to image projection
    point.Transform(transform)
    west = point.GetX() - chipExtend / 2
    east = point.GetX() + chipExtend / 2
    south = point.GetY() - chipExtend / 2
    north = point.GetY() + chipExtend / 2

    if os.path.isfile(f"tms/{tms.lower()}_tms.xml"):
        with rio.open(f"tms/{tms.lower()}_tms.xml") as TMS_dataset:
            bl = TMS_dataset.index(west, south, op=math.floor)
            tr = TMS_dataset.index(east, north, op=math.ceil)

            window = Window(bl[1], tr[0], tr[1] - bl[1], bl[0] - tr[0])

            # image_size is a tuple (num_bands, h, w)
            output_dataset = np.empty(shape=(
                TMS_dataset.count, chipSize, chipSize),
                dtype=TMS_dataset.profile['dtype'])

            # Read all bands
            TMS_dataset.read(out=output_dataset, window=window)

            res = float(chipExtend) / chipSize
            transform = Affine.translation(
                west + res / 2, north - res / 2) * Affine.scale(res, -res)

            if format == 'tif':
                chipset = rio.open(f"{unique_dir}/{tms.lower()}.tif", 'w',
                                   driver='GTiff',
                                   width=output_dataset.shape[2],
                                   height=output_dataset.shape[1],
                                   count=TMS_dataset.count,
                                   crs=3857,
                                   transform=transform,
                                   dtype=TMS_dataset.profile['dtype']
                                   )
            elif format == 'png':
                chipset = rio.open(f"{unique_dir}/{tms.lower()}.png", 'w',
                                   driver='PNG',
                                   width=output_dataset.shape[2],
                                   height=output_dataset.shape[1],
                                   count=TMS_dataset.count,
                                   crs=3857,
                                   transform=transform,
                                   dtype=TMS_dataset.profile['dtype']
                                   )
            else:
                return False

            chipset.write(output_dataset)
            chipset.close()
            return True
    else:
        return False


def buildHTML(unique_dir, tms, format='tif'):
    """Build an HTML page that displays the selected chip as a PNG tile.
    Arguments:
        unique_dir (str): the path for the file to be stored
        tms (str): tile map server
        format (str): File format '.tif' or '.png'
    """
    flist = glob.glob(f"{unique_dir}/{tms.lower()}.{format}")

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>table {'{border-spacing: 10px;}'}</style>
</head>
<body>
    <table style="width:100%">
        <tr>
            <td>
                <label>
                <img id = '{flist[0]}' src='{url_for(
                    'static', filename=flist[0].replace('static/', ''))}'/>
                <br/>
                {flist[0]}
                </label>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    with open(f"{unique_dir}/dump.html", "w") as out:
        out.write(html)

    return True
