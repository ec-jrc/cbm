#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import json
import pandas as pd
from os.path import join, normpath
from cbm.utils import config


def by_pid(aoi, year, pid, tstype='s2', ptype=None, band='', debug=False):
    return sentinel(aoi, year, pid, tstype, ptype, band, debug)


def sentinel(aoi, year, pid, tstype='s2', ptype=None, band='', debug=False):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.time_series.by_pid(aoi, pid, tstype, band, save)

    Arguments:
        aoi, the area of interest and year e.g.: es2019, nld2020 (str)
        pid, the parcel id (int).
    """
    get_requests = data_source()
    workdir = config.get_value(['paths', 'temp'])
    file_ts = normpath(join(workdir, aoi, str(year), str(pid),
                            f'time_series_{tstype}{band}.csv'))
    ts = json.loads(get_requests.parcel_ts(
        aoi, year, pid, tstype, ptype, band, debug))
    if isinstance(ts, pd.DataFrame):
        ts.to_csv(file_ts, index=True, header=True)
    elif isinstance(ts, dict):
        os.makedirs(os.path.dirname(file_ts), exist_ok=True)
        df = pd.DataFrame.from_dict(ts, orient='columns')
        df.to_csv(file_ts, index=True, header=True)
    if debug:
        print(f"File saved at: {file_ts}")
    return ts


def weather(aoi, year, pid, ptype=None, debug=False):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.time_series.weather(aoi, pid)

    Arguments:
        aoi, the area of interest and year e.g.: es2019, nld2020 (str)
        pid, the parcel id (int).
    """
    get_requests = data_source()
    workdir = config.get_value(['paths', 'temp'])
    file_ts = normpath(join(workdir, aoi, str(year), str(pid),
                            f'time_series_weather.csv'))
    ts = json.loads(get_requests.parcel_wts(aoi, year, pid, ptype, debug))
    if isinstance(ts, pd.DataFrame):
        ts.to_csv(file_ts, index=True, header=True)
    elif isinstance(ts, dict):
        os.makedirs(os.path.dirname(file_ts), exist_ok=True)
        df = pd.DataFrame.from_dict(ts, orient='columns')
        df.to_csv(file_ts, index=True, header=True)
    if debug:
        print(f"File saved at: {file_ts}")
    return ts


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
