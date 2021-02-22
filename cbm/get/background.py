#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import json
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.plot import show
from descartes import PolygonPatch

from cbm.sources import api
from cbm.view import spatial_utils
from mpl_toolkits.axes_grid1 import ImageGrid

def by_location(aoi, year, lon, lat, chipsize=512, extend=512, tms='Google',
                prefix='', path='temp', quiet=False):
    """Download the background image with parcels polygon overlay by selected
    location. This function will get an image from the center of the polygon.

    Examples:
        from cbm.view import background
        background.by_location(aoi, year, lon, lat, 512, 512, 'Google',
                                'temp/test.tif', True)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        prefix, the name of the output file (str).
        path, the path to be stored (str).
        quiet, print or not procedure information (Boolean).

    """
    json_data = json.loads(api.ploc(aoi, year, lon, lat, True))
    with open(f'{path}/{prefix}info.json', "w") as f:
        json.dump(json_data, f)

    lat, lon = spatial_utils.centroid(
        spatial_utils.transform_geometry(json_data))
    if type(tms) is list:
        for t in tms:
            img_overlay(aoi, year, lon, lat, chipsize,
                        extend, t, prefix, path, True)
        view_all(tms, prefix, path)
    else:
        img_overlay(aoi, year, lon, lat, chipsize,
                    extend, tms, prefix, path, quiet)


def by_pid(aoi, year, pid, chipsize=512, extend=512, tms='Google', prefix='',
           path='temp', quiet=False):
    """Download the background image with parcels polygon overlay by selected
    location.

    Examples:
        from cbm.view import background
        background.by_location(aoi, year, lon, lat, 512, 512, 'Google',
                                'temp/test.tif', True)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        pid, the parcel id (str).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        prefix, the name of the output file (str).
        path, the path to be stored (str).
        quiet, print or not procedure information (Boolean).

    """
    json_data = json.loads(api.pid(aoi, year, pid, True))
    with open(f'{path}/{prefix}info.json', "w") as f:
        json.dump(json_data, f)

    lat, lon = spatial_utils.centroid(
        spatial_utils.transform_geometry(json_data))
    if type(tms) is list:
        for t in tms:
            img_overlay(aoi, year, lon, lat, chipsize,
                        extend, t, prefix, path, True)
        view_all(tms, prefix, path)
    else:
        img_overlay(aoi, year, lon, lat, chipsize,
                    extend, tms, prefix, path, quiet)


def img_overlay(aoi, year, lon, lat, chipsize=512, extend=512, tms='Google',
                prefix='', path='temp', quiet=False):
    """Main function to download the background image with parcels polygon
    overlay by selected location. This function will get an image from the
    given coordinates not the center of the polygon that was founded.

    Examples:
        from cbm.view import background
        background.img_overlay(aoi, year, lon, lat, 512, 512, 'Google',
                                'temp/test.tif', True)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        prefix, the name of the output file (str).
        path, the path to be stored (str).
        quiet, print or not procedure information (Boolean).

    """

    bk_file = api.background(lon, lat, chipsize, extend, tms, prefix, path)

    with open(f'{path}/{prefix}info.json', "r") as f:
        json_data = json.load(f)

    with rasterio.open(bk_file) as img:
        def overlay_parcel(img, json_data):
            img_epsg = img.crs.to_epsg()
            geo_json = spatial_utils.transform_geometry(
                json_data, img_epsg)
            patche = [PolygonPatch(feature, edgecolor="yellow",
                                   facecolor="none", linewidth=2
                                   ) for feature in [geo_json['geom'][0]]]
            return patche

        ax = plt.gca()
        for p in overlay_parcel(img, json_data):
            ax.add_patch(p)
        plt.axis('off')
        show(img, ax=ax)

        plt.savefig(f"{bk_file.split('.')[0]}.png".lower(), dpi=None,
                    facecolor='w', edgecolor='w', orientation='portrait',
                    format=None, transparent=False, bbox_inches='tight',
                    pad_inches=0.1, metadata=None)

        if quiet is not False:
            plt.clf()
            plt.cla()
            plt.close()


def view_all(tms, prefix='', path='temp'):

    columns = 5
    rows = int(len(tms) // columns + (len(tms) % columns > 0))
    fig = plt.figure(figsize=(25, 5 * rows))
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(rows, columns),  # creates 2x2 grid of axes
                     axes_pad=0.1,  # pad between axes in inch.
                     )

    for ax, im in zip(grid, tms):
        # Iterating over the grid returns the Axes.
        ax.axis('off')
        ax.imshow(plt.imread(f'temp/{im.lower()}.png', 3))
        ax.set_title(im)

    plt.show()