# Get modules

To check individual parcel, the parcel information, time series, background high resolution images can be downloaded to the local storage.


## Time series

```python
import cbm

aoi = 'aoi'      # area of interest (str)
year = 2019      # the year of the parcels dataset (int)
pid = 123456     # Parcel id (int)
tstype = 's2'    # time series type (str)
band = ''        # a selected band
save = True      # Save to file (bool)

cbm.get.time_series.by_pid(aoi, year, pid, tstype, band, save)
```

## Chipimages

Download the chip image by selected parcel id.

Example
```python
import cbm

aoi = 'nld'               # Area of interest (str)
year = 2019               # Year of the parcels dataset (int)
pid = 575532              # Parcel id (int)
start_date = '2019-06-01' # Start date '2019-06-01' (str)
end_date = '2019-06-30'   # End date '2019-06-01' (str)
sat = 's2'                # Time series type  (str)
band = 'SCL'              # Selected band
chipsize = 2560           # size of the chip in pixels (int)

cbm.get.chip_images.by_pid(aoi, year, pid, start_date, end_date, band, chipsize)
```

Arguments

    sat:  
    band: 3 Sentinel-2 band names. One of [‘B02’, ‘B03’, ‘B04’, ‘B08’] (10 m bands) or
        [‘B05’, ‘B06’, ‘B07’, ‘B8A’, ‘B11’, ‘B12’] (20 m bands). 10m and 20m bands can be combined.
        The first band determines the resolution in the output
        composite. Defaults to B08_B04_B03.


## Background

Download the background image by selected location. This function will get an image from the given longitude and latitude of the parcel.

If not configured alredy the RESTful API credentials can be set with:
```python
# Import the cbm python library
import cbm

# Add the RESTful API credentials
api_url = 'http://0.0.0.0'
api_user = ''
api_pass = ''
cbm.config.set_value(['api', 'url'], api_url)
cbm.config.set_value(['api', 'user'], api_user)
cbm.config.set_value(['api', 'pass'], api_pass)
```

To download background images and orthophotos
```python
import cbm
# Set parcel parameters
aoi = 'aoi'      # area of interest (str)
year = 2019      # the year of the parcels dataset (int)
pid = 123456     # The pasrcel id (str)
lat = 123.45     # latitude in decimal degrees (float)
lon = 123.45     # longitude in decimal degrees (float)
chipsize = 728   # size of the chip in pixels (int)
extend = 728     # size of the chip in meters (float)
# images from tile map servers: Google Bing (list)
tms=['Google', 'Bing']

# Get the background images by lon, lat:
cbm.get.background.by_location(aoi, year, lon, lat, chipsize, extend, tms, quiet)

# Get the background images by parcel id:
cbm.get.background.by_pid(aoi, year, pid, chipsize, extend, tms, quiet)
```


## Data stracture

Example folder structure for parcel with ID 12345 stored in temp folder:
```sh
temp/
    aoi2019/p12345/info.json                             # Parcel information in .json format
    aoi2019/p12345/time_series_s2.csv                    # Time series form the parcel in .csv format
    aoi2019/p12345/backgrounds/*                         # Background images
    aoi2019/p12345/chipimages/images_list.B04.csv        # A list of downloaded images in .csv format
    aoi2019/p12345/chipimages/S2A_MSIL2A_2019---.B04.tif # The downloaded chip images
    aoi2019/p12345/chipimages/S2A_MSIL2A_...             # ...
```


## Get widgets

The get() function of ipycbm library provides an interactive Jupyter Notebook widget to get data from different sources, with variety of different methods (coordinates, parcels ids, map marker, polygon).

```python
from cbm import ipycbm
ipycbm.get()
```

![](https://raw.githubusercontent.com/konanast/cbm_media/main/ipycbm_get_01.png)


### Background widgets

```python
# Add the API credentials with:
from cbm import ipycbm
ipycbm.config()

# Set parcel parameters
aoi = 'aoi'      # area of interest (str)
year = 2019      # the year of the parcels dataset (int)
pid = 123456     # latitude in decimal degrees (float)
chipsize = 728   # size of the chip in pixels (int)
extend = 728     # size of the chip in meters (float)
# images from tile map servers: Google Bing (list)
tms=['Google', 'Bing']

#  View a grid of background images with:
ipycbm.bg_grid(aoi, year, pid, chipsize, extend, tms)
```

![](https://raw.githubusercontent.com/konanast/cbm_media/main/ipycbm_bg_grid_01.png)

```python
# Or view a slider with the background images:
ipycbm.bg_slider(aoi, year, pid, chipsize, extend, tms)
```

![](https://raw.githubusercontent.com/konanast/cbm_media/main/ipycbm_bg_slider_01.png)
