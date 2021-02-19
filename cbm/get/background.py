#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

# Download the background image
import re
import requests
from cbm.utils import config

def main(lon, lat, chipsize=512, extend=512, tms='Google', bk_file=None, quiet=True):
    """Download the background image.

    Examples:
        background(lon, lat, 512, 512, 'Google', 'temp/test.tif', True)

    Arguments:
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        bk_file, the name of the output file (str).
        quiet, print or not procedure information (Boolean).

    """

    # Get the api credentials
    api_url, api_user, api_pass = config.credentials('api')

    # The url to get the background image
    requrl = f"{api_url}/query/backgroundByLocation?lon={lon}&lat={lat}&chipsize={chipsize}&extend={extend}&tms={tms}"
    response = requests.get(requrl, auth=(api_user, api_pass))

    # Try to get the image link from the html response
    try:
        bkgdimg = re.search('src="(.+?)"/>', str(response.content)).group(1)
    except AttributeError:
        if not quiet:
            print("Image found:", bkgdimg)
        bkgdimg = '' # image not found in html response

    img_url = f"{api_url}{bkgdimg}"
    res = requests.get(img_url, stream=True)
    if not bk_file:
        bk_file = f"{img_url.split('/')[-1]}"
    # print(f"Downloading {c.split('/')[-1]}")
    with open(bk_file, "wb") as handle:
        for chunk in res.iter_content(chunk_size=512):
            if chunk:  # filter out keep-alive new chunks
                handle.write(chunk)
    if not quiet:
        print("Background image downloaded:", bk_file)

if __name__ == "__main__":
    import sys
    main(sys.argv)
