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
from osgeo import osr, ogr


def getBackgroundExtract(lon, lat, chipSize=256, chipExtend=500, unique_dir='',
                         tms="google", iformat='tif', withGeometry=False):
    """Generate an extract from either Google or Bing.
    It uses the WMTS standard to grab and compose,
    which makes it fast (does not depend on DIAS S3 store).
    Arguments:
        on, lat (float): longitude, latitude in decimal degrees
        chipSize (int): size of the chip in pixels
        chipExtend (float): size of the chip in meters
        unique_dir (str): the path for the file to be stored
        tms (str): tile map server
        iformat (str): File format '.tif' or '.png'
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

    if os.path.isfile(f"tms/{tms.lower()}.xml"):
        with rio.open(f"tms/{tms.lower()}.xml") as TMS_dataset:
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

            if iformat == 'tif':
                chipset = rio.open(f"{unique_dir}/{tms.lower()}.tif", 'w',
                                   driver='GTiff',
                                   width=output_dataset.shape[2],
                                   height=output_dataset.shape[1],
                                   count=TMS_dataset.count,
                                   crs=3857,
                                   transform=transform,
                                   dtype=TMS_dataset.profile['dtype']
                                   )
            elif iformat == 'png':
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
            if withGeometry and iformat == 'png':
                from copy import copy
                from rasterio.plot import show
                import matplotlib.pyplot as plt
                from descartes import PolygonPatch

                from scripts import spatial_utils
                from scripts import db_queries

                def overlay_parcel(img, geom):
                    """Create parcel polygon overlay"""
                    patche = [PolygonPatch(feature, edgecolor="yellow",
                                           facecolor="none", linewidth=2
                                           ) for feature in geom['geom']]
                    return patche
                datasets = db_queries.get_datasets()
                aoi, year, pid, ptype = withGeometry
                dataset = datasets[f'{aoi}_{year}']
                pdata = db_queries.getParcelByID(dataset, pid, ptype,
                                                 withGeometry, False)
                if len(pdata) == 1:
                    parcel = dict(zip(list(pdata[0]),
                                      [[] for i in range(len(pdata[0]))]))
                else:
                    parcel = dict(zip(list(pdata[0]),
                                      [list(i) for i in zip(*pdata[1:])]))

                with rio.open(f"{unique_dir}/{tms.lower()}.png") as img:
                    geom = spatial_utils.transform_geometry(parcel, 3857)
                    patches = overlay_parcel(img, geom)
                    for patch in patches:
                        fig = plt.figure()
                        ax = fig.gca()
                        plt.axis('off')
                        plt.box(False)
                        ax.add_patch(copy(patch))
                        show(img, ax=ax)
                        plt.savefig(f"{unique_dir}/{tms.lower()}.png",
                                    bbox_inches='tight')
            return True
    else:
        return False
