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


def by_pid(aoi, year, pid, start_date, end_date, sat, band, chipsize):
    """Download the chip image by selected parcel id.

    Examples:
        import cbm
        cbm.get.chip_images.by_pid(aoi, year, pid, start_date, end_date, sat,
                                    band, chipsize)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        pid, the parcel id (int).
        start_date, Start date '2019-06-01' (str)
        end_date, End date '2019-06-01' (str)
        band, 3 Sentinel-2 band names. One of [‘B02’, ‘B03’, ‘B04’, ‘B08’]
            (10 m bands) or [‘B05’, ‘B06’, ‘B07’, ‘B8A’, ‘B11’, ‘B12’]
            (20 m bands). 10m and 20m bands can be combined.
            The first band determines the resolution in the output
            composite. Defaults to B08_B04_B03.
        chipsize, size of the chip in pixels (int).
    """
    datapath = config.get_value(['paths', 'temp'])
    get_requests = data_source()
    pfile = f"{datapath}{aoi}{year}/{pid}/info.json"
    if not os.path.isfile(pfile):
        parcel = json.loads(get_requests.pid(aoi, year, pid, True))
        print(data_handler.export(parcel, 10, pfile.replace('.json', '')))
    else:
        with open(pfile, "r") as f:
            parcel = json.load(f)
    files_chips = f"{datapath}{aoi}{year}/{pid}/chip_images/"
    print(f"Getting '{band}' chip images for parcel: {pid}")

    # parcel = json.loads(get_requests.pid(aois, year, pid, True))
    get_requests.rcbl(parcel, start_date, end_date, [band],
                      chipsize, files_chips)

    filet = f'{datapath}{aoi}{year}/{pid}/chip_images/images_list.{band}.csv'
    if file_len(filet) > 1:
        print(f"Completed, all GeoTIFFs for band '{band}' are downloaded",
              f" in the folder: '{datapath}{aoi}{year}/{pid}/chip_images'")
    else:
        print("No files where downloaded, please check your configurations")


def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


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
