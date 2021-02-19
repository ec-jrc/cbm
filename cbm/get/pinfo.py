#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

# Download parcel information as json file
import json
import requests
from cbm.utils import config

def main(aoi, year, lon, lat, geom=False, pinf_file='parcel_info.json', quiet=True):
    """Download the background image.

    Examples:
        pinf(aoi, year, lon, lat, True, 'temp/test.json', True)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        pinf_file, the name of the output file (str).
        quiet, print or not procedure information (Boolean).

    """

    # Get the api credentials
    api_url, api_user, api_pass = config.credentials('api')

    parcels = f'{aoi}{year}'

    requrl = """{}/query/parcelByLocation?parcels={}&lon={}&lat={}"""
    # Check if geometry is requested.
    if geom is True:
        requrl = f"{requrl}&withGeometry=True"

    response = requests.get(requrl.format(api_url, parcels, lon, lat),
                            auth=(api_user, api_pass))
    parcel_info = response.content
    
    with open(pinf_file, "w") as f:
        json.dump(json.loads(parcel_info.decode()), f)
    if not quiet:
        print("The parcel information is downloaded:", pinf_file)


if __name__ == "__main__":
    import sys
    main(sys.argv)
