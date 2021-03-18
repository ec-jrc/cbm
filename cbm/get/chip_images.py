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


def by_pid(aoi, year, pid, start_date, end_date, band, chipsize, quiet=False):
    """Download the chip image by selected parcel id.

    Examples:
        import cbm
        cbm.get.chip_images.by_pid(aoi, year, pid, start_date, end_date,
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
    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            f'{aoi}{str(year)}', str(pid)))
    get_requests = data_source()
    pfile = normpath(join(workdir, 'info.json'))
    if not isfile(pfile):
        parcel = json.loads(get_requests.pid(aoi, year, pid, True))
        try:
            os.makedirs(dirname(pfile), exist_ok=True)
            with open(pfile, "w") as f:
                json.dump(parcel, f)
            if not quiet:
                print(f"File saved at: {pfile}")
        except Exception as err:
            print(f"Could not create the file: {err}")
    else:
        with open(pfile, "r") as f:
            parcel = json.load(f)
    images_dir = normpath(join(workdir, 'chip_images'))
    if not quiet:
        print(f"Getting '{band}' chip images for parcel: {pid}")

    # parcel = json.loads(get_requests.pid(aois, year, pid, True))
    get_requests.rcbl(parcel, start_date, end_date, [band],
                      chipsize, images_dir)

    images_list = normpath(join(workdir, 'chip_images',
                                f'images_list.{band}.csv'))
    if file_len(images_list) > 1:
        if not quiet:
            print(f"Completed, all GeoTIFFs for band '{band}' are downloaded",
                  f" in the folder: '{workdir}/chip_images'")
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
