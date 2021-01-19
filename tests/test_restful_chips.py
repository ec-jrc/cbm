#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import sys
import glob
import json

import requests
import rasterio

import pandas as pd
from datetime import datetime

from rasterstats import zonal_stats

from osgeo import osr, ogr

# Define your credentials here
username = 'YOURUSERNAME'
password = 'YOURPASSWORD'
host = '0.0.0.0'

# Get the parcel id for this location, make sure to get the parcel geometry as well
locurl = """http://{}/query/parcelByLocation?parcels={}&lon={}&lat={}&withGeometry=True"""

# set the query parameters
parcels = 'nld2019'
lon='5.6637'
lat='52.6936'

# Parse the response with the standard json module
response = requests.get(locurl.format(host, parcels, lon, lat), auth = (username, password))

parcel = json.loads(response.content)

# Check response
if not parcel:
    print("Parcel query returned empty result")
    sys.exit()
elif not parcel.get(list(parcel.keys())[0]):
    print(f"No parcel found in {parcels} at location ({lon}, {lat})")
    sys.exit()

print(parcel)

# Create a valid geometry from the returned JSON withGeometry
geom = ogr.CreateGeometryFromJson(parcel.get('geom')[0])

source = osr.SpatialReference()
source.ImportFromEPSG(parcel.get('srid')[0])

# Assign this projection to the geometry
geom.AssignSpatialReference(source)

target = osr.SpatialReference()
target.ImportFromEPSG(4326)

transform = osr.CoordinateTransformation(source, target)

# And get the lon, lat for its centroid, so that we can center the chips on
# the parcel
centroid = geom.Centroid()
centroid.Transform(transform)

# Use pid for next request
pid = parcel['ogc_fid'][0]
cropname = parcel['cropname'][0]

# Set up the rawChip request
rawurl = """http://{}/query/rawChipByLocation?lon={}&lat={}&start_date={}&end_date={}&band={}&chipsize={}"""

# query parameter values
start_date='2019-06-01'
end_date ='2019-06-30'
band = 'SCL'    # Start with the SCL scene, to check cloud cover conditions
chipsize = 2560 # Size of the extracted chip in meters (5120 is maximum)

response = requests.get(rawurl.format(host, str(centroid.GetX()), str(centroid.GetY()), start_date, end_date, band, chipsize), auth = (username, password))

# Directly create a pandas DataFrame from the json response
df = pd.read_json(response.content)

# Check for an empty dataframe
if df.empty:
    print(f"rawChip query returned empty result")
    sys.exit()

print(df)

# Download the GeoTIFFs that were just created in the user cache
for c in df.chips:
    url = f"http://{host}{c}"
    res = requests.get(url, stream=True)
    outf = c.split('/')[-1]
    print(f"Downloading {outf}")
    handle = open(outf, "wb")
    for chunk in res.iter_content(chunk_size=512):
        if chunk:  # filter out keep-alive new chunks
            handle.write(chunk)
    handle.close()

# Check whether our parcel is cloud free

# We should have a list of GeoTIFFs ending with .SCL.tif
tiflist = glob.glob('*.SCL.tif')

for t in tiflist:
    with rasterio.open(t) as src:
        affine = src.transform
        CRS = src.crs
        data = src.read(1)

    # Reproject the parcel geometry in the image crs
    imageCRS = int(str(CRS).split(':')[-1])

    # Cross check with the projection of the geometry
    # This needs to be done for each image, because the parcel could be in a
    # straddle between (UTM) zones
    geomCRS = int(geom.GetSpatialReference().GetAuthorityCode(None))

    if geomCRS != imageCRS:
        target = osr.SpatialReference()
        target.ImportFromEPSG(imageCRS)
        source = osr.SpatialReference()
        source.ImportFromEPSG(geomCRS)
        transform = osr.CoordinateTransformation(source, target)
        geom.Transform(transform)

    # Format as a feature collection (with only 1 feature) and extract the histogram
    features = { "type": "FeatureCollection",
        "features": [{"type": "feature", "geometry": json.loads(geom.ExportToJson()), "properties": {"pid": pid}}]}
    zs = zonal_stats(features, data, affine=affine, prefix="", nodata=0, categorical=True, geojson_out=True)

    # This has only one record
    properties = zs[0].get('properties')

    # pid was used as a dummy key to make sure the histogram values are in 'properties'
    del properties['pid']

    histogram = {int(float(k)):v for k, v in properties.items()}
    print(t, histogram)
