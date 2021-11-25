# parcelTimeSeries

**Using RESTful services to get parcel time series**

Extract time series statistics from the Sentinel data are available, both actual and archived, for all parcels in an annual declaration set.

The table below shows the parameters for time series selection.

| Parameters  | Description   | Values | Default value |
| ----------- | ----------- | ----------- | ----------- |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. | - |
| **year** | year of parcels dataset   | e.g.: 2018, 2019   | - |
| **pid** | parcel ID | - | - |
| ptype | parcels type | b, g, m, atc. | - |
| **tstype** | Sentinel-2 Level 2A, S1 CARD Backscattering Coefficients, S1 CARD 6-day Coherence | s2, bs, c6, scl | s2 |
| scl | Include scl in the s2 extraction, for use in cloud screening | True or False | True |
| ref | Include Sentinel image reference in time series | True or False | False |
| tsformat | parcels type | csv, json | json |

Examples: **Change the parameters aoi, year and pid based on your provided parcels data.**
- Example 1, returns the S2 time series of the parcel with SCL histograms and image reference,
https://cap.users.creodias.eu/query/parcelTimeSeries?aoi=ms&year=2020&pid=123&tstype=s2&scl=True&ref=True
- Example 2, returns the S1 Backscattering Coefficients time series of the parcel,
https://cap.users.creodias.eu/query/parcelTimeSeries?aoi=ms&year=2020&pid=123&tstype=bs
- Example 3, returns the S1 6-day Coherence time series of the parcel,
https://cap.users.creodias.eu/query/parcelTimeSeries?aoi=ms&year=2020&pid=123&tstype=c6
- Example 4, returns only the SCL histogram for the selected parcel,
https://cap.users.creodias.eu/query/parcelTimeSeries?aoi=ms&year=2020&pid=123&tstype=scl


returns

| Key            | Values  | Description   |
| ---------------| ------- | ----------- |
| date_part     | a list of timestamps     | as seconds since 'Unix epoch' (1970-01-01 00:00:00 UTC)  |
| *band*        | a list of image bands  | Missing if *band* query parameter is provided |
| count      | a list of counts  | count of pixels extracted for each parcel and observation |
| mean       | a list of means   | mean etc. |
| std       | a list of stds   | standard deviation etc. |
| min       | a list of mins   | min etc. |
| max       | a list of maxs   | max etc. |
| p25       | a list of p25s   | 25% histogram percentile etc. |
| p50       | a list of p50s   | 50% histogram percentile etc. |
| p75       | a list of p75s   | 75% histogram percentile etc. |


## Simple python client to consume parcelTimeSeries response

We show a complete example on how to use the RESTful queries in a python script. The script first requests the parcel details at the geographical location, and than retrieves the Sentinel-2 time series in a second request. The response of the latter query is parsed into a pandas DataFrame, which allows some data reorganisation and cleanup. The cleaned data is used to generate an NDVI profile which is then plotted, resulting in a figure as the one below. The blue dots are showing all NDVI values, those with a red inset are for observations that are cloud-free according to the "scene classifier" band of Sentinel 2 Level 2A.

![Example time series](https://raw.githubusercontent.com/ec-jrc/cbm/main/docs/img/figure_1.png)


[Get the source](https://github.com/ec-jrc/cbm/tree/main/tests/test_restful.py)


```python
import sys
import json

import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Define your credentials here
username = 'YOUR USERNAME'
password = 'YOUR PASSWORD'

# Get the parcel id for this location, make sure to get the parcel geometry as well
locurl = """https://{}/query/parcelByLocation?aoi={}&year={}&lon={}&lat={}&withGeometry=True&ptype={}"""

# set the query parameters
aoi = 'nl'
year = '2018'
ptype = 'm'
lon='6.24617'
lat='52.99011'

# Parse the response with the standard json module
response = requests.get(locurl.format(host, aoi, year, lon, lat, ptype), auth = (username, password))

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
pid = parcel['pid'][0]
cropname = parcel['cropname'][0]

# Set up the timeseries request
tsurl = """https://cap.users.creodias.eu/query/parcelTimeSeries?aoi={}&year={}&pid={}&tstype={}"""

# query parameter values
aoi = 'nld'
year ='2018'
tstype = 's2'

response = requests.get(tsurl.format(aoi, year, pid, tstype), auth = (username, password))

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
```
