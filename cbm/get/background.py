#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
import os
from os.path import join, normpath

from cbm.utils import config
from cbm.get import parcel_info


def by_location(aoi, year, lon, lat, chipsize=512, extend=512,
                tms=['Google'], ptype=None, axis=True, debug=False):
    """Download the background image with parcels polygon overlay by selected
    location. This function will get an image from the center of the polygon.

    Examples:
        from cbm.view import background
        background.by_location(aoi, lon, lat, 512, 512, 'Google',
                                True, True)

    Arguments:
        aoi, the area of interest (str)
        year, the year of parcels table
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        debug, print or not procedure information (Boolean).
    """
    get_requests = data_source()
    if type(tms) is str:
        tms = [tms]
    try:
        parcel = parcel_info.by_location(aoi, year, lon, lat, ptype,
                                         True, False, debug)
        if type(parcel['pid']) is list:
            pid = parcel['pid'][0]
        else:
            pid = parcel['pid']

        workdir = normpath(join(config.get_value(['paths', 'temp']),
                                aoi, str(year), str(pid)))
        if debug:
            print('pid: ', pid)
            print('workdir: ', workdir)

    except Exception as err:
        workdir = normpath(join(config.get_value(['paths', 'temp']), aoi,
                                str(year), f'_{lon}_{lat}'.replace('.', '_')))
        if debug:
            print("No parcel information found.", err)

    bg_path = normpath(join(workdir, 'backgrounds'))
    os.makedirs(bg_path, exist_ok=True)
    with open(f"{bg_path}/chipsize_extend_{chipsize}_{extend}", "w") as f:
        f.write('')

    if debug:
        print('bg_path: ', bg_path)
        print('lon, lat:', lon, lat)
    for t in tms:
        if debug:
            print('lon, lat, chipsize, extend, t, bg_path, debug')
            print(lon, lat, chipsize, extend, t, bg_path, debug)
        get_requests.background(lon, lat, chipsize, extend, t, bg_path, debug)


def by_pid(aoi, year, pid, chipsize=512, extend=512,
           tms=['Google'], ptype=None, axis=True, debug=False):
    """Download the background image with parcels polygon overlay by selected
    location.

    Examples:
        from cbm.view import background
        background.by_pid(aoi, pid, 512, 512, 'Google',
                                True, True)

    Arguments:
        aoi, the area of interest (str)
        year, the year of parcels table
        pid, the parcel id (str).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        debug, print or not procedure information (Boolean).
    """
    get_requests = data_source()
    if type(tms) is str:
        tms = [tms]
    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            aoi, str(year), str(pid)))

    parcel = parcel_info.by_pid(aoi, year, pid, ptype, True, False, debug)
    if debug:
        print('workdir: ', workdir)
    lon = parcel['clon'][0]
    lat = parcel['clat'][0]

    bg_path = normpath(join(workdir, 'backgrounds'))
    os.makedirs(bg_path, exist_ok=True)
    with open(f"{bg_path}/chipsize_extend_{chipsize}_{extend}", "w") as f:
        f.write('')

    if debug:
        print('bg_path: ', bg_path)
        print('lon, lat:', lon, lat)

    for t in tms:
        if debug:
            print('lon', 'lat', 'chipsize', 'extend', 't', 'bg_path', 'debug')
            print(lon, lat, chipsize, extend, t, bg_path, debug)
        get_requests.background(lon, lat, chipsize, extend, t, bg_path, debug)


def data_source():
    source = config.get_value(['set', 'data_source'])
    if source == 'api':
        from cbm.datas import api
        return api
    elif source == 'direct':
        from cbm.datas import direct
        return direct
