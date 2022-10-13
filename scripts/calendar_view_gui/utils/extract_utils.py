#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Csaba Wirnhardt
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from rasterstats import zonal_stats
import rasterio
import numpy
import warnings


def calculate_ndvi(image_file, ndvi_file):
    # Load red and NIR bands - note all PlanetScope 4-band images have band order BGRN
    with rasterio.open(image_file) as src:
        band_red = src.read(3)

    with rasterio.open(image_file) as src:
        band_nir = src.read(1)
        
    # Allow division by zero
    numpy.seterr(divide='ignore', invalid='ignore')

    # Calculate NDVI
    ndvi = (band_nir.astype(float) - band_red.astype(float)) / (band_nir + band_red)
    
    # Set spatial characteristics of the output object to mirror the input
    kwargs = src.meta
    kwargs.update(
        dtype=rasterio.float32,
        count = 1)

    # Create the file
    with rasterio.open(ndvi_file, 'w', **kwargs) as dst:
            dst.write_band(1, ndvi.astype(rasterio.float32))
    
def calculate_ndvi_from_2022(image_file, ndvi_file):
    # Load red and NIR bands - note all PlanetScope 4-band images have band order BGRN
    with rasterio.open(image_file) as src:
        band_red = src.read(3)

    with rasterio.open(image_file) as src:
        band_nir = src.read(1)
        
    band_1000 = numpy.ones_like(band_red)*1000
    band_red = band_red - band_1000
    band_nir = band_nir - band_1000
    
    # Allow division by zero
    numpy.seterr(divide='ignore', invalid='ignore')

    # Calculate NDVI
    ndvi = (band_nir.astype(float) - band_red.astype(float)) / (band_nir + band_red)
    
    # Set spatial characteristics of the output object to mirror the input
    kwargs = src.meta
    kwargs.update(
        dtype=rasterio.float32,
        count = 1)

    # Create the file
    with rasterio.open(ndvi_file, 'w', **kwargs) as dst:
            dst.write_band(1, ndvi.astype(rasterio.float32))


def calculate_ndwi(image_file, ndwi_file):
    # Load red and NIR bands - note all PlanetScope 4-band images have band order BGRN
    with rasterio.open(image_file) as src:
        band_red = src.read(3)

    with rasterio.open(image_file) as src:
        band_swir = src.read(2)
        
    # Allow division by zero
    numpy.seterr(divide='ignore', invalid='ignore')

    # Calculate ndwi
    ndwi = (band_swir.astype(float) - band_red.astype(float)) / (band_swir + band_red)
    
    # Set spatial characteristics of the output object to mirror the input
    kwargs = src.meta
    kwargs.update(
        dtype=rasterio.float32,
        count = 1)

    # Create the file
    with rasterio.open(ndwi_file, 'w', **kwargs) as dst:
            dst.write_band(1, ndwi.astype(rasterio.float32))
    
def calculate_ndwi_from_2022(image_file, ndwi_file):
    # Load red and NIR bands - note all PlanetScope 4-band images have band order BGRN
    with rasterio.open(image_file) as src:
        band_red = src.read(3)

    with rasterio.open(image_file) as src:
        band_swir = src.read(2)

    band_1000 = numpy.ones_like(band_red)*1000
    band_red = band_red - band_1000
    band_swir = band_swir - band_1000

        
    # Allow division by zero
    numpy.seterr(divide='ignore', invalid='ignore')

    # Calculate ndwi
    ndwi = (band_swir.astype(float) - band_red.astype(float)) / (band_swir + band_red)
    
    # Set spatial characteristics of the output object to mirror the input
    kwargs = src.meta
    kwargs.update(
        dtype=rasterio.float32,
        count = 1)

    # Create the file
    with rasterio.open(ndwi_file, 'w', **kwargs) as dst:
            dst.write_band(1, ndwi.astype(rasterio.float32))

    # plt.imsave("ndwi_cmap.png", ndwi, cmap=plt.cm.summer)    

def extract_stats_for_one_parcel_geopandas_presel(tif_file, parcel):
    warnings.simplefilter(action='ignore', category=UserWarning)
    src_image = rasterio.open(tif_file)
    parcel = parcel.to_crs(src_image.crs)
    
    # here we could use the src_image as input instead of the tif file itself
    # so that we can take into account the new radiometry instroduced by ESA
    # on 2022-01-25
    band_stats_for_parcel = zonal_stats(parcel,
                     tif_file,
                     stats="count mean std",
                    band=1)  
    NDVI_mean = band_stats_for_parcel[0]['mean']
    NDVI_count = band_stats_for_parcel[0]['count']
    NDVI_std = band_stats_for_parcel[0]['std']
    return NDVI_mean, NDVI_count, NDVI_std

def extract_stats_for_one_parcel_geopandas_presel_bs(tif_file, parcel):
    warnings.simplefilter(action='ignore', category=UserWarning)
    src_image = rasterio.open(tif_file)
    parcel = parcel.to_crs(src_image.crs)

    band_stats_for_parcel_including_zeros = zonal_stats(parcel,
                     tif_file,
                     stats="count mean std",
                    band=1)  
                    
# This is a patch we might want to remove later on
# I had problems with parcels that are on the edge of the image
# Nodata in Sentinel-1 CARD backscatter images are coded as 0
# I'll calculate the statistics within the parcel including and excluding zeros
# If the results are the same it means there are no Nodata pixels within the parcel, so we keep that date
# Let's see if it works                    
    band_stats_for_parcel_excluding_zeros = zonal_stats(parcel,
                     tif_file,
                     stats="count mean std",
                    band=1,
                    nodata=0.0)  
      
    if band_stats_for_parcel_including_zeros[0]['mean'] == band_stats_for_parcel_excluding_zeros[0]['mean']:
        BS_mean = band_stats_for_parcel_including_zeros[0]['mean']
        BS_count = band_stats_for_parcel_including_zeros[0]['count']
        BS_std = band_stats_for_parcel_including_zeros[0]['std']
    else:
        BS_mean = None
        BS_count = None
        BS_std = None
    return BS_mean, BS_count, BS_std


# inputTifFileName = "e:/chips/nour2019_new01/266449_MELON_merged/S2A_MSIL2A_20190426T105031_N0211_R051_T31TCG_20190426T134237.tif"
# outputNDVIFileName = "e:/chips/nour2019_new01/266449_MELON_merged_ndvi/S2A_MSIL2A_20190426T105031_N0211_R051_T31TCG_20190426T134237.tif"

# vector_file_name = "e:/MS/ES/Catalunia2019/vector/GSAA2019_nour.shp"
# parcel_id_column = 'fid_int'
# # outputMaskedNDVIFileName = "y:/Data/HHR_TS_2019/generic/python/extract_pixels_for_polygons/raster/ITPUG19_832733259_21A_NDVI_v5_masked.tif"
# parcel_id = 266449

# parcel = batch_utils.select_parcel(vector_file_name, parcel_id_column, parcel_id)


# calculate_ndvi(inputTifFileName, outputNDVIFileName)
# print("NDVI calculated")

# parcelStats = extract_stats_for_one_parcel_geopandas_presel(outputNDVIFileName, parcel)
# print(parcelStats)

# outputCsvFile = "e:/chips/nour2019_new01/ndvi.csv"

# firstLine ="Field_ID,acq_date,NDVI_mean, NDVI_count, NDVI_std"
# print(firstLine, file=open(outputCsvFile, "w"))

# acq_date = '2019-05-06'
# NDVI_mean = parcelStats[0]['mean']
# NDVI_count = parcelStats[0]['count']
# NDVI_std = parcelStats[0]['std']


# print(parcel_id, acq_date, NDVI_mean, NDVI_count, NDVI_std, sep=',',
    # file=open(outputCsvFile, "a"))


def calculate_baresoil_index_image(image_folder, index_file):
    # https://giscrack.com/list-of-spectral-indices-for-sentinel-and-landsat/
    with rasterio.open(image_file) as src:
        band_red = src.read(3)

    with rasterio.open(image_file) as src:
        band_nir = src.read(1)
        
    band_1000 = numpy.ones_like(band_red)*1000
    band_red = band_red - band_1000
    band_nir = band_nir - band_1000
        
        
    # Allow division by zero
    numpy.seterr(divide='ignore', invalid='ignore')

    # Calculate BSI
    bsi = (band_nir.astype(float) - band_red.astype(float)) / (band_nir + band_red)
    
    # Set spatial characteristics of the output object to mirror the input
    kwargs = src.meta
    kwargs.update(
        dtype=rasterio.float32,
        count = 1)

    # Create the file
    with rasterio.open(ndvi_file, 'w', **kwargs) as dst:
            dst.write_band(1, bsi.astype(rasterio.float32))
