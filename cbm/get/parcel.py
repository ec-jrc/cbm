#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import json
from os.path import join, normpath, isfile, dirname, exists
from cbm.utils import config


def by_location(aoi, lon, lat, quiet=True):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.parcel.by_pid(aoi, pid, save)

    Arguments:
        aoi, the area of interest and year e.g.: es2019, nld2020 (str)
        lat, lon, the the coords of the parcel (float).
    """
    get_requests = data_source()
    try:
        json_data = json.loads(get_requests.ploc(aoi, lon, lat, True))
        if type(json_data['ogc_fid']) is list:
            pid = json_data['ogc_fid'][0]
        else:
            pid = json_data['ogc_fid']

        workdir = normpath(join(config.get_value(['paths', 'temp']),
                                aoi, str(pid)))
        json_file = normpath(join(workdir, 'info.json'))
        if not exists(workdir):
            os.makedirs(workdir)
        if not isfile(json_file):
            with open(json_file, "w") as f:
                json.dump(json_data, f)
    except Exception:
        workdir = normpath(join(config.get_value(['paths', 'temp']),
                                aoi, f'_{lon}_{lat}'))

    file_pinf = normpath(join(workdir, 'info.json'))
    if not isfile(file_pinf):
        try:
            parcel = json.loads(get_requests.pid(aoi, pid, True))
            os.makedirs(dirname(file_pinf), exist_ok=True)
            with open(file_pinf, "w") as f:
                json.dump(parcel, f)
        except Exception as err:
            return f"Could not create the file: {err}"
    else:
        with open(file_pinf, 'r') as f:
            parcel = json.load(f)
        return parcel


def by_pid(aoi, pid, quiet=True):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.parcel.by_pid(aoi, pid)

    Arguments:
        aoi, the area of interest and year e.g.: es2019, nld2020 (str)
        pid, the parcel id (int).
    """
    workdir = config.get_value(['paths', 'temp'])
    get_requests = data_source()
    file_pinf = normpath(join(workdir, aoi, str(pid), 'info.json'))
    if not isfile(file_pinf):
        try:
            parcel = json.loads(get_requests.pid(aoi, pid, True))
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
