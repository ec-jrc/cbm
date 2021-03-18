#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
import os
import json
from os.path import join, normpath, exists, isfile

from cbm.sources import api
from cbm.utils import spatial_utils, config


def by_location(aoi, year, lon, lat, chipsize=512, extend=512,
                tms='Google', quiet=True, axis=True):
    """Download the background image with parcels polygon overlay by selected
    location. This function will get an image from the center of the polygon.

    Examples:
        from cbm.view import background
        background.by_location(aoi, year, lon, lat, 512, 512, 'Google',
                                True, True)

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

    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            f'{aoi}{str(year)}', str(pid)))
    json_file = normpath(join(workdir, 'info.json'))
    if not exists(workdir):
        os.makedirs(workdir)
    if not isfile(json_file):
        with open(json_file, "w") as f:
            json.dump(json_data, f)

    by_pid(aoi, year, pid, chipsize, extend, tms, quiet, axis)


def by_pid(aoi, year, pid, chipsize=512, extend=512,
           tms='Google', quiet=True, axis=True):
    """Download the background image with parcels polygon overlay by selected
    location.

    Examples:
        from cbm.view import background
        background.by_location(aoi, year, lon, lat, 512, 512, 'Google',
                                True, True)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        pid, the parcel id (str).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        quiet, print or not procedure information (Boolean).
    """

    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            f'{aoi}{str(year)}', str(pid)))
    json_file = normpath(join(workdir, 'info.json'))
    if not isfile(json_file):
        json_data = json.loads(api.pid(aoi, year, pid, True))
        if not exists(workdir):
            os.makedirs(workdir)

        with open(json_file, "w") as f:
            json.dump(json_data, f)
    else:
        with open(json_file, 'r') as f:
            json_data = json.load(f)

    lat, lon = spatial_utils.centroid(
        spatial_utils.transform_geometry(json_data))

    api.background(lon, lat, chipsize, extend,
                   tms, aoi, year, pid, quiet)
