#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import sys
import json

import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Define your credentials here
username = 'YOUR USERNAME'
password = 'YOUR PASSWORD'
host = '0.0.0.0'

# Get the parcel id for this location
locurl = """http://{}/query/parcelByLocation?parcels={}&lon={}&lat={}"""

# set the query parameters
parcels = 'nld2018'
lon='6.31'
lat='52.34'

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

# Use pid for next request
pid = parcel['ogc_fid'][0]
cropname = parcel['cropname'][0]

# Set up the timeseries request
tsurl = """http://{}/query/parcelTimeSeries?aoi={}&year={}&pid={}&tstype={}"""

# query parameter values
aoi = 'nld'
year ='2018'
tstype = 's2'

response = requests.get(tsurl.format(host, aoi, year, pid, tstype), auth = (username, password))

# Directly create a pandas DataFrame from the json response
# This should work even if the response is and empty dictionary
df = pd.read_json(response.content)

# Check for an empty dataframe
if df.empty:
    print(f"Timeseries query returned empty result for parcel {pid} and {aoi}, {year} and {tstype}")
    sys.exit()

# Convert the epoch timestamp to a datetime
df['date_part']=df['date_part'].map(lambda e: datetime.fromtimestamp(e))

# Treat each band separately. Drop duplicate timestamps and rename the 'mean'
df4 = df[df['band']=='B4'][['date_part', 'mean']]
df4.drop_duplicates(['date_part'], inplace=True)
df4.rename(columns={'mean': 'B4'}, inplace=True)

df8 = df[df['band']=='B8'][['date_part', 'mean']]
df8.drop_duplicates(['date_part'], inplace=True)
df8.rename(columns={'mean': 'B8'}, inplace=True)

dfQA = df[df['band']=='SC'][['date_part', 'mean']]
dfQA.drop_duplicates(['date_part'], inplace=True)
dfQA.rename(columns={'mean': 'SC'}, inplace=True)

# Merge back into one DataFrame
dff = pd.merge(df4, df8, on = 'date_part')
dff = pd.merge(dff, dfQA, on = 'date_part')
# Create a NDVI
dff['ndvi'] = (dff['B8']-dff['B4'])/(dff['B8']+dff['B4'])

print(dff)

# Define the criteria for having a cloud free observation
cloudfree = ((dff['SC']>=4) & (dff['SC'] < 7))

plt.figure()
plt.plot(dff['date_part'], dff['ndvi'], linestyle = ' ', marker = 'o', color = 'blue')
plt.plot(dff[cloudfree]['date_part'], dff[cloudfree]['ndvi'], linestyle = ' ', marker = '*', color = 'red')
plt.title(f"{tstype} time series for parcel {pid} ({cropname})")
plt.xlabel('Date')
plt.ylabel('NDVI')
plt.show()
