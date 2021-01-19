#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import requests

import rasterio
import numpy as np

# Should move to imgLib later
def byteScale(img, min, max):
    return np.clip(255 * (img - min) /(max - min), 0, 255).astype(np.uint8)

username = 'YOURUSERNAME'
password = 'YOURPASSWORD'
host = '0.0.0.0'


tifUrlBase = f"http://{username}:{password}@{host}"
url = tifUrlBase + "/query/rawS1ChipsBatch"
payloadDict = {
  "lon": 5.66425,
  "lat": 52.69444,
  "dates": ["2019-06-10", "2019-06-25"],
  "chipsize": 2560,
  "plevel": 'CARD-BS'
}

# First get the CARD-BS
response = requests.post(url, json=payloadDict)
json_BS = response.json()

# then get CARD-COH6
payloadDict['plevel'] = 'CARD-COH6'
response = requests.post(url, json=payloadDict)
json_C6 = response.json()

# Now let's do some arty compositioning
# We'll generate a mean VV and VH for the period
# and add coherence

g0 = [f for f in json_BS.get('chips') if f.find('20190614')!=-1]
g1 = [f for f in json_BS.get('chips') if f.find('20190620')!=-1]
c0 = [f for f in json_C6.get('chips') if f.find('20190614')!=-1 and f.find('20190620')!=-1]

g0VV = [g for g in g0 if g.find('VV')!=-1][0]
g0VH = g0VV.replace('VV', 'VH')
g1VV = [g for g in g1 if g.find('VV')!=-1][0]
g1VH = g1VV.replace('VV', 'VH')

# We only open the VV coherence band
c0VV = [c for c in c0 if c.find('VV')!=-1][0]

with rasterio.open(tifUrlBase + g0VV) as src:
    vv = src.read(1)
    kwargs = src.meta.copy()

# Take the average of the 2 VV bands and convert to dB
with rasterio.open(tifUrlBase + g1VV) as src:
    vv = 10.0*np.log10((vv + src.read(1))/2)

with rasterio.open(tifUrlBase + g0VH) as src:
    vh = src.read(1)

# Take the average of the 2 VV bands
with rasterio.open(tifUrlBase + g1VH) as src:
    vh = 10.0*np.log10((vh + src.read(1))/2)

with rasterio.open(tifUrlBase + c0VV) as src:
    c6 = src.read(1)

kwargs.update({'count': 3, 'dtype': np.uint8})
with rasterio.open(f"test.tif", 'w',**kwargs) as sink:
    sink.write(byteScale(vv, -15.0, -3.0),1) # R
    sink.write(byteScale(vh, -20.0, -8.0),2) # R
    sink.write(byteScale(c6, 0.2, 0.9),3) # R

    