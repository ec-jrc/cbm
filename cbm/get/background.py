#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
import os
import json
import glob
from os.path import join, normpath, exists, isfile

from cbm.utils import spatial_utils, config


def by_location(aoi, year, lon, lat, chipsize=512, extend=512,
                tms=['Google'], axis=True, debug=False):
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
        json_data = json.loads(get_requests.ploc(aoi, year, lon, lat,
                                                 True, False, debug))
        if type(json_data['ogc_fid']) is list:
            pid = json_data['ogc_fid'][0]
        else:
            pid = json_data['ogc_fid']

        workdir = normpath(join(config.get_value(['paths', 'temp']),
                                aoi, str(year), str(pid)))
        if debug:
            print('pid: ', pid)
            print('workdir: ', workdir)
            print('json_data: ', json_data)

        json_file = normpath(join(workdir, 'info.json'))
        os.makedirs(workdir, exist_ok=True)
        if not isfile(json_file):
            with open(json_file, "w") as f:
                json.dump(json_data, f)
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
           tms=['Google'], axis=True, debug=False):
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
    if debug:
        print('workdir: ', workdir)
    json_file = normpath(join(workdir, 'info.json'))
    if not isfile(json_file):
        json_data = json.loads(get_requests.pid(aoi, year, pid,
                                                None, True, False, debug))
        os.makedirs(workdir, exist_ok=True)
        with open(json_file, "w") as f:
            json.dump(json_data, f)
    else:
        with open(json_file, 'r') as f:
            json_data = json.load(f)

    lon = json_data['clon'][0]
    lat = json_data['clat'][0]

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
