#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import json
from os.path import join, normpath, dirname
from cbm.utils import config


def by_location(aoi, year, lon, lat, ptype=None, geom=True,
                wgs84=False, debug=False):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.parcel.by_location(aoi, year, lon, lat)

    Arguments:
        aoi, the area of interest (str)
        year, the year of parcels table
        lon, lat, the the coords of the parcel (float).
    """
    get_requests = data_source()
    parcel = get_requests.parcel_by_loc(
        aoi, year, lon, lat, ptype, geom, wgs84, debug)
    if validate_parcel(parcel, debug):
        parcel = json.loads(parcel)
        if type(parcel['pid']) is list:
            pid = parcel['pid'][0]
        else:
            pid = parcel['pid']
        json_file = normpath(join(config.get_value(
            ['paths', 'temp']), aoi, str(year), str(pid), 'info.json'))
        os.makedirs(dirname(json_file), exist_ok=True)
        with open(json_file, "w") as f:
            json.dump(parcel, f)
        if debug:
            print("Parcel information saved at: ", json_file)
        return parcel
    else:
        return None


def by_pid(aoi, year, pid, ptype=None, geom=True,
           wgs84=False, debug=False):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.parcel.by_pid(aoi, pid)

    Arguments:
        aoi, the area of interest (str)
        year, the year of parcels table
        pid, the parcel id (int).
    """
    get_requests = data_source()
    parcel = get_requests.parcel_by_id(
        aoi, year, pid, ptype, geom, wgs84, debug)
    if validate_parcel(parcel, debug):
        parcel = json.loads(parcel)
        json_file = normpath(join(config.get_value(
            ['paths', 'temp']), aoi, str(year), str(pid), 'info.json'))
        os.makedirs(dirname(json_file), exist_ok=True)
        with open(json_file, "w") as f:
            json.dump(parcel, f)
        if debug:
            print("Parcel information saved at: ", json_file)
        return parcel
    else:
        return None


def validate_parcel(parcel, debug=False):
    try:
        parcel = json.loads(parcel)
        if type(parcel) is dict:
            if parcel != {}:
                if parcel['pid'] != []:
                    return True
        return False
    except Exception:
        if debug:
            print("[Err]: No parcel information found")
        return False


def by_polygon(aoi, year, polygon, ptype=None, geom=False,
               wgs84=False, only_ids=True, debug=False):
    get_requests = data_source()
    return get_requests.parcel_by_polygon(
        aoi, year, polygon, ptype, geom, wgs84, only_ids, debug)


def data_source():
    source = config.get_value(['set', 'data_source'])
    if source == 'api':
        from cbm.datas import api
        return api
    elif source == 'direct':
        from cbm.datas import direct
        return direct


if __name__ == "__main__":
    import sys
    by_pid(sys.argv)
