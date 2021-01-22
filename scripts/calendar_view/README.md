# Calendar view

## JRC Ispra Unit Food security

#### Main author(s): Csaba Wirnhardt

## 1. Introduction
The “**calendar_view**” python library provides a set of functions that allows one to download, process and display Sentinel-1 and Sentinel-2 data products. The library is designed to operate on “**parcels**” provided as input in a ESRI shape file. Sentinel-1 and -2 data are extracted for the specific parcels and are displayed in a “**calendar view**”, which as been designed and optimized to provide an immediate and intuitive access to both temporal and spatial dimensions of Sentinel-derived data.

While the scripts exploit the RESTful APIs developed by the JRC D5 unit to download raw Sentinel imagettes tailored to the extent of the parcels provided as input, the code is general and can be easily adapted to work, for example, on geotiff downloaded from other sources.

## 2. Dependencies
The *run_calendar_view.py* script depends on several standard python libraries that can be found in the *requirements.txt* file. The dependencies can be installed with:

  pip install -r requirements.txt

As well the gdal_merge.py module that can be download from [https://github.com/geobox-infrastructure/gbi-client/blob/master/app/geobox/lib/gdal_merge.py](https://github.com/geobox-infrastructure/gbi-client/blob/master/app/geobox/lib/gdal_merge.py)
and should be added to the utils folder.

### 2.1 JRC CbM Modules for the calendar_view package
The following custom libraries are called by the *run_calendar_view.py* script:

- **batch_utils**: provides general functions for the processing of parcels and Sentinel data. The set of functions provided in this library allows the selection of parcels, the determination of the list of imagettes to be downloaded on the basis of cloud mask criteria, the download of imagettes, processing of Sentinel data including image color stretching (lookup table stretch or LUT stretch)and computation of derived indexes such as NDVI and NDWI. For download operations, the library uses the functions developed under *download_utils*.
    
- **download_utils**: library for downloading and processing Sentinel-1 and 2 imagettes.
 
- **plot_utils**: functions for plotting Sentinel-1 and 2 imagettes in structured calendar views. Sentinel products are displayed in a coherent way, in order to provide an enhanced accessibility to both temporal and spatial dimensions of Sentinel-1 and 2 products. 

- **graph_utils**: library providing functions for displaying and plotting temporal profiles such as NDVI and NDWI. The library focuses on temporal (1-D) signals and complements the utilities in *plot_utils*, which focuses on displaying images (set of 2-D signals).   

- **extract_utils**: functions for the calculation of the NDVI and NDWI indexes. The functions in this library are called by *batch_utils*.

The call graph of the run_calendar_view script is provided in Figure 1.

![Call graph of the run_calendar_view script.](media/img/calendar_view_fun.png)
**Figure 1: Call graph of the run_calendar_view script.** 
