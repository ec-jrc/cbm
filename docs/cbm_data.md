# Data access

CbM data can be accessed through RESTful API or directly accessing the
database and object storage, direct access is only for administrators.

Preferable way to access the data is through RESTful API.
To easily set the RESTful API account you can use the below python command:
```python
cbm.set_api_account('http://0.0.0.0/', 'YOUR_USERNAME', 'YOUR_PASSWORD')
```
Alternatively see '[cbm package configuration](https://jrc-cbm.readthedocs.io/en/latest/cbm_config.html)' for other options.


## Parcel information

Download parcel information by ID.
```python
import cbm

aoi = 'ms'             # area of interest (str)
year = 2020            # the year of the parcels dataset (int)
pid = '12345'          # parcel id (str)
ptype = None           # (optional) specify the dataset*
with_geometry = True   # get the parcel geometry
debug = False          # show debugging output

cbm.get.parcel_info.by_pid(aoi, year, pid, ptype, with_geometry, debug)
```

Download parcel information by location.
```python
import cbm

aoi = 'ms'             # area of interest (str)
year = 2020            # the year of the parcels dataset (int)
lat = 50.12345         # latitude in decimal degrees
lon = 5.12345          # longitude in decimal degrees
ptype = None           # (optional) specify the dataset*
with_geometry = True   # get the parcel geometry
debug = False          # show debugging output

cbm.get.parcel_info.by_location(aoi, year, pid, ptype, with_geometry, debug)
```


## Time series

**ptype** is used only in case there are different datasets dedicated to different type of analysis for the same year.
For example datasets dedicated to grazing use **g**, for mowing **m** etc.


**scl** Scene Classification Values

The classification mask is generated along with the process of generating
the cloud mask quality indicator and by merging the information obtained
from cirrus cloud detection and cloud shadow detection.

The classification map is produced for each SENTINEL-2 Level-1C product
at 60 m resolution and byte values of the classification map are organised as shown below:

![](https://raw.githubusercontent.com/konanast/cbm_media/main/scl_02.png)


### Show time series

**Plot NDVI time series**
```python
import cbm

aoi = 'ms'             # area of interest (str)
year = 2020            # the year of the parcels dataset (int)
pid = '12345'          # parcel id (str)
ptype = None           # (optional) specify the dataset*
cloud_free = True      # mark cloud free images based on scl values
scl = '3_8_9_10_11'    # scene classification values to be excluded
debug = False          # show debugging output

cbm.show.time_series.ndvi(aoi, year, pid, ptype, cloud_free, scl, debug)
```
![](https://raw.githubusercontent.com/konanast/cbm_media/main/show_ts_ndvi_01.png)

**Plot S2 bands**
```python
import cbm

aoi = 'ms'             # area of interest (str)
year = 2020            # the year of the parcels dataset (int)
pid = '12345'          # parcel id (str)
ptype = None           # (optional) specify the dataset*
bands = ['B03', 'B04'] # bands to plot in a list
cloud_free = True      # mark cloud free images based on scl values
scl = '3_8_9_10_11'    # scene classification values to be excluded
debug = False          # show debugging output

cbm.show.time_series.s2(aoi, year, lat, lon, ptype, bands, cloud_free, scl, debug)
```


### Download time series

Download the time series without plotting for a knowing parcel ID.
```python
import cbm

aoi = 'ms'        # area of interest (str)
year = 2020       # the year of the parcels dataset (int)
pid = '12345'     # parcel id (str)
ptype = None      # (optional) specify the dataset*
tstype = 's2'     # time series type (str)

import cbm
cbm.get.time_series.by_pid(aoi, year, pid, tstype, ptype)
```

Download the time series without plotting based on the parcel location.
```python
import cbm

aoi = 'ms'        # area of interest (str)
year = 2020       # the year of the parcels dataset (int)
pid = '12345'     # parcel id (str)
ptype = None      # (optional) specify the dataset*
lat = 50.12345    # latitude in decimal degrees
lon = 5.12345     # longitude in decimal degrees
tstype = 's2'     # time series type (str)

cbm.get.time_series.by_location(aoi, year, lat, lon, tstype, ptype)
```

The files will be saved by default in the **temp/** folder


## Background images


### Show background images


```python
import cbm

aoi = 'ms'             # area of interest (str)
year = 2020            # the year of the parcels dataset (int)
pid = '12345'          # parcel id (str)
chipsize = 512         # size of the chip in pixels
extend = 512           # size of the chip in meters
tms = ['Google']       # tile map server, Google, Bing or MS orthophotos
ptype = None           # (optional) specify the dataset*
columns = 4            # the number of grid columns
debug = False          # show debugging output

cbm.show.background.by_pid(aoi, year, pid, ptype, chipsize, extend, tms, ptype, columns, debug)
```

![](https://raw.githubusercontent.com/konanast/cbm_media/main/show_bg_01.png)


### Download background images

To download background images without preview 
```python
import cbm

aoi = 'ms'             # area of interest (str)
year = 2020            # the year of the parcels dataset (int)
pid = '12345'          # parcel id (str)
chipsize = 512         # size of the chip in pixels
extend = 512           # size of the chip in meters
tms = ['Google']       # tile map server, Google, Bing or MS orthophotos
ptype = None           # (optional) specify the dataset*
debug = False          # show debugging output

cbm.get.background.by_pid(aoi, year, pid, ptype, chipsize, extend, tms, ptype, debug)
```
