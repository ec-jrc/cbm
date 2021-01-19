#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import requests

import imgLib

username = 'YOURUSERNAME'
password = 'YOURPASSWORD'
host = '0.0.0.0'

# Authenticate directly in URL
tifUrlBase = f"http://{username}:{password}@{host}"
url = tifUrlBase + "/query/rawChipsBatch"

payloadDict = {
  "lon": 5.66425,
  "lat": 52.69444,
  "tiles": ["S2B_MSIL2A_20190617T104029_N0212_R008_T31UFU_20190617T131553",
            "S2A_MSIL2A_20190625T105031_N0212_R051_T31UFU_20190625T134744",
            "S2B_MSIL2A_20190620T105039_N0212_R051_T31UFU_20190620T140845"],
  "bands": ["B08", "B04", "B11"],
  "chipsize": 2560
}

response = requests.post(url, json=payloadDict)

jsonOut = response.json()

# Instead of transfering the image bands from cache
# generate an normalizedDifference output directly from the cache URLs
for c in jsonOut.get('chips'):
    if c.endswith('B08.tif'):
        name = c.split('/')[-1].replace('B08', 'NDVI')
        url0 = tifUrlBase + c
        url1 = url0.replace('B08.tif', 'B04.tif')

        imgLib.normalizedDifference(url0, url1, name)
        imgLib.scaled_palette(name, 0, 1, 'RdYlGn')
