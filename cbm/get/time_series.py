#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import json
import os.path
from cbm.utils import data_handler, config


def by_pid(aoi, year, pid, tstype, band, save=True):
    """Download the time series for the selected year

    Examples:
        import cbm
        cbm.get.time_series.by_pid(aoi, year, pid, tstype, band, save)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        pid, the parcel id (int).
        save, save or not to file (Boolean).
    """
    datapath = config.get_value(['paths', 'temp'])
    get_requests = data_source()
    file_ts = f"{datapath}/{aoi}{year}/{pid}/time_series_{tstype}{band}"
    if not os.path.isfile(file_ts):
        ts = json.loads(get_requests.pts(aoi, year, pid, tstype, band))
        if save:
            print(data_handler.export(ts, 11, file_ts))


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
