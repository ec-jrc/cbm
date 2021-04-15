#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import json
from os.path import join, normpath, isfile, dirname
from cbm.utils import config


def by_location(aoi, year, lon, lat, tstype, band, quiet=True):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.time_series.by_pid(aoi, year, pid, tstype, band, save)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        pid, the parcel id (int).
    """
    get_requests = data_source()
    try:
        json_data = json.loads(get_requests.ploc(aoi, year, lon, lat, True))
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
    except Exception:
        workdir = normpath(join(config.get_value(['paths', 'temp']),
                                f'{aoi}{str(year)}', f'_{lon}_{lat}'))

    file_pinf = normpath(join(workdir, 'info.json'))
    if not isfile(file_pinf):
        try:
            parcel = json.loads(get_requests.pid(aoi, year, pid, True))
            os.makedirs(dirname(file_pinf), exist_ok=True)
            with open(file_pinf, "w") as f:
                json.dump(parcel, f)
        except Exception as err:
            return f"Could not create the file: {err}"
    else:
        with open(file_pinf, 'r') as f:
            parcel = json.load(f)
        return parcel


def by_pid(aoi, year, pid, tstype, band, quiet=True):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.time_series.by_pid(aoi, year, pid, tstype, band, save)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        pid, the parcel id (int).
    """
    workdir = config.get_value(['paths', 'temp'])
    get_requests = data_source()
    file_pinf = normpath(join(workdir, f'{aoi}{year}', pid, 'info.json'))
    if not isfile(file_pinf):
        try:
            parcel = json.loads(get_requests.pid(aoi, year, pid, True))
            os.makedirs(dirname(file_pinf), exist_ok=True)
            with open(file_pinf, "w") as f:
                json.dump(parcel, f)
        except Exception as err:
            return f"Could not create the file: {err}"
    else:
        with open(file_pinf, 'r') as f:
            parcel = json.load(f)
        return parcel


def data_source():
    source = config.get_value(['set', 'data_source'])
    if source == 'api':
        from cbm.sources import api
        return api
    elif source == 'direct':
        from cbm.sources import direct
        return direct


if __name__ == "__main__":
    import sys
    by_pid(sys.argv)
