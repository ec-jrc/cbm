#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
import os
import os.path
import json
import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import show
from descartes import PolygonPatch

from cbm.sources import api
from cbm.utils import spatial, config


def by_location(aoi, year, lon, lat, chipsize=512, extend=512,
                tms='Google', quiet=True):
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
        quiet, print or not procedure information (Boolean).

    """

    json_data = json.loads(api.ploc(aoi, year, lon, lat, True))
    if type(json_data['ogc_fid']) is list:
        pid = json_data['ogc_fid'][0]
    else:
        pid = json_data['ogc_fid']

    workdir = config.get_value(['paths', 'temp'])
    path = f'{workdir}{aoi}{year}/pid{pid}/'
    if not os.path.exists(path):
        os.makedirs(path)

    with open(f'{path}info.json', "w") as f:
        json.dump(json_data, f)

    lat, lon = spatial.centroid(
        spatial.transform_geometry(json_data))

    img_overlay(aoi, year, pid, lon, lat, chipsize,
                extend, tms, quiet)


def by_pid(aoi, year, pid, chipsize=512, extend=512, tms='Google', quiet=True):
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
        quiet, print or not procedure information (Boolean).

    """
    json_data = json.loads(api.pid(aoi, year, pid, True))

    workdir = config.get_value(['paths', 'temp'])
    path = f'{workdir}{aoi}{year}/pid{pid}/'
    if not os.path.exists(path):
        os.makedirs(path)

    with open(f'{path}info.json', "w") as f:
        json.dump(json_data, f)

    lat, lon = spatial.centroid(
        spatial.transform_geometry(json_data))

    img_overlay(aoi, year, pid, lon, lat, chipsize,
                extend, tms, quiet)


def img_overlay(aoi, year, pid, lon, lat, chipsize=512, extend=512,
                tms='Google', quiet=True):
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
        quiet, print or not procedure information (Boolean).

    """

    bg_file = api.background(lon, lat, chipsize, extend,
                             tms, aoi, year, pid, quiet)

    workdir = config.get_value(['paths', 'temp'])
    path = f'{workdir}{aoi}{year}/pid{pid}/'
    if not os.path.exists(path):
        os.makedirs(path)

    with open(f'{path}info.json', "r") as f:
        json_data = json.load(f)

    with rasterio.open(bg_file) as img:
        def overlay_parcel(img, json_data):
            img_epsg = img.crs.to_epsg()
            geo_json = spatial.transform_geometry(
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

        plt.savefig(f"{bg_file.split('.')[0]}.png".lower(), dpi=None,
                    facecolor='w', edgecolor='w', orientation='portrait',
                    format=None, transparent=False, bbox_inches='tight',
                    pad_inches=0.1, metadata=None)

        if quiet is True:
            plt.clf()
            plt.cla()
            plt.close()
