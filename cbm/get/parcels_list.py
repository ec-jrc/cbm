#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import json
from os.path import join, normpath
from cbm.utils import config


def peers(aoi, year, pid, distance=1000.0, maxPeers=10,
          ptype=None, debug=False):
    """Get the parcel peers for the selected parcel

    Examples:
        import cbm
        cbm.get.parcels_list.peers(aoi, year, pid)

    Arguments:
        aoi, the area of interest (str)
        year, the year of parcels table
        pid, the parcel id (str).
        distance, distance from the given parcel
        maxPeers, the max number of parcels to be returned
    """
    get_requests = data_source()
    parcels = json.loads(get_requests.parcel_peers(aoi, year, pid, distance,
                                                   maxPeers, ptype, debug))

    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            aoi, str(year), str(pid)))
    json_file = normpath(join(workdir, f'parcel_peers.json'))
    os.makedirs(workdir, exist_ok=True)
    with open(json_file, "w") as f:
        json.dump(parcels, f)
    return parcels





def data_source():
    source = config.get_value(['set', 'data_source'])
    if source == 'api':
        from cbm.datas import api
        return api
    elif source == 'direct':
        from cbm.datas import direct
        return direct
