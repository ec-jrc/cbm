#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).

__author__ = ["Csaba Wirnhardt"]
__copyright__ = "Copyright 2021, European Commission Joint Research Centre"
__credits__ = ["GTCAP Team"]
__license__ = "3-Clause BSD"
__version__ = ""
__maintainer__ = [""]
__status__ = "Development"


import os
import sys
sys.path.insert(0, os.path.abspath('./utils'))
import download_utils, lut, plot_utils, batch_utils, graph_utils
import extract_utils
from importlib import reload
import geopandas
import time
from glob import glob
import requests
import json
import gdal_merge as gm
from matplotlib import pyplot
import rasterio
from rasterio import plot
import datetime
from osgeo import ogr

# setting parameters that are used by the different functions below
username = ''
password = ''
url_base = "http://0.0.0.0"
cloud_categories = [3,8,9,10,11] # 10 is thin cirrus
# cloud_categories = [3,8,9,11]
# cloud_categories = []

out_tif_folder_base = "path/to/tif/folder/base"
centroid_shift_degrees = 0.00009 # if we want to make sure that the chips are not read from the cash from the Restful server
                                 # we change the fifth digit of the lat lon coordinates. this will not move much but 
                                 # assures the chips are regenerated
                   
# 2019 GSAA for parcels
vector_file_name = "path/to/vector/file.shp"

                    
parcel_id_column = 'fid_int'
crop_name_column = 'crop_en'


chipsize = '5120'
bands = ["B04", "B08", "B11"]
raw_chips_by_location_url = url_base + "/query/rawChipByLocation"
raw_chips_batch_url = url_base + "/query/rawChipsBatch"
raw_chips_s1_batch_url = url_base + "/query/rawS1ChipsBatch"

left_percent = 1
right_percent = 1
s1_bs_left_percent = 1
s1_bs_right_percent = 4

lut_txt_file = out_tif_folder_base + "/lut.txt"
logfile = out_tif_folder_base + "/log.txt"

search_window_start_date = "2019-01-01"
search_window_end_date = "2019-10-31"
search_split_days = 30
max_number_of_tiles_per_request = 12

buffer_size_meter = 100
pixel_size_meter = 10
vector_color = "yellow"

plot_title ="FR 2019"
jpg_resolution = 100

output_s1_bs_calendar_view_folder = out_tif_folder_base + "/s1_bs_calendar_view"

if not os.path.exists(out_tif_folder_base):
    os.makedirs(out_tif_folder_base)
    
parcel_id_crop_list = batch_utils.get_all_parcel_ids_from_parcel_shape(vector_file_name, parcel_id_column, crop_name_column)

list_of_parcel_ids_to_process = (
   704985,
 )

for parcel_id, crop in parcel_id_crop_list:

    if parcel_id in list_of_parcel_ids_to_process:
  

        print(parcel_id, crop)
        chip_folder = str(parcel_id) + '_' + crop
        out_s1_bs_folder = out_tif_folder_base + "/" + chip_folder + "_s1_bs"
        out_s1_bs_folder_rescale = out_tif_folder_base + "/" + chip_folder + "_s1_bs_rescale"
        out_s1_bs_folder_rescale_lut = out_tif_folder_base + "/" + chip_folder + "_s1_bs_rescale_lut"        
                
        parcel = batch_utils.select_parcel(vector_file_name, parcel_id_column, parcel_id, logfile)

        chipsize = str(int(download_utils.get_max_parcel_extent_in_meters(parcel) + buffer_size_meter)+ buffer_size_meter*2+50)
        lon, lat = download_utils.get_centroid_of_parcel(parcel_id, parcel, centroid_shift_degrees, logfile)

        #Get and downlod Scene Classification Layer imagettes
        batch_utils.run_get_scl_imagettes(parcel, parcel_id, crop, out_tif_folder_base, 
                                    search_window_start_date, search_window_end_date, search_split_days,
                                    raw_chips_by_location_url, username, password, chipsize,
                                    url_base, lon, lat, logfile
                                   )

        #create a list of tiles to be downloaded (based on cloud cover inside the parcel)
        tiles_to_download = batch_utils.create_list_of_tiles_to_be_downloaded(parcel, parcel_id, crop, out_tif_folder_base, 
                                                                              cloud_categories, logfile)

        #Get and download band imagettes
        batch_utils.run_get_and_download_band_imagettes(max_number_of_tiles_per_request, tiles_to_download, 
                                                        raw_chips_batch_url,
                                                lon, lat, bands, username, password, chipsize, url_base, 
                                                parcel_id, crop, out_tif_folder_base, logfile)

        #merge downloaded bands
        batch_utils.run_merge_bands(parcel_id, crop, out_tif_folder_base, logfile)

        #Create LUT stretched images with fixed stretching        
        batch_utils.run_lut_stretch(parcel_id, crop, out_tif_folder_base, left_percent, right_percent, lut_txt_file, logfile)

        #Get list of fix LUT stretched images
        acq_dates, merged_lut_files = batch_utils.get_merged_lutstretched_files_and_acquisition_dates(parcel_id, crop, 
                                                                                                      out_tif_folder_base,
                                                                                                      logfile)
        #Create calendar view of fix LUT stretched imagettes
        vector_color = "yellow"
        fig, a = plot_utils.calendar_view_half_weekly_more_param(parcel_id, crop, out_tif_folder_base, 
                                                             tiles_to_download, parcel, vector_file_name, 
                                                parcel_id_column, buffer_size_meter, vector_color, logfile, jpg_resolution, acq_dates, merged_lut_files)
                                                
        #Create LUT stretched images with dynamic stretching
        batch_utils.run_lut_stretch_dynamic(parcel_id, crop, out_tif_folder_base, left_percent, right_percent, lut_txt_file, logfile)
                                                
        #Get list of dynamic LUT stretched images
        acq_dates, merged_lut_files = batch_utils.get_merged_lutstretched_files_and_acquisition_dates_dynamic(parcel_id, crop, 
                                                                                                    out_tif_folder_base,
                                                                                                    logfile)
        #Create calendar view of dynamic LUT stretched imagettes
        vector_color = "yellow"
        fig, a = plot_utils.calendar_view_half_weekly_more_param_dynamic(parcel_id, crop, out_tif_folder_base, 
                                                             tiles_to_download, parcel, vector_file_name, 
                                                parcel_id_column, buffer_size_meter, vector_color, logfile, jpg_resolution, acq_dates, merged_lut_files)

        #Create NDVI imagettes
        batch_utils.run_ndvi_creation(parcel_id, crop, out_tif_folder_base, logfile)

        #Get list of ndvi imagettes
        acq_dates, merged_ndvi_files = batch_utils.get_merged_ndvi_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base)   
        
        #Calendar view of NDVI imagettes
        vector_color = "black"
        fig, a = plot_utils.calendar_view_half_weekly_more_param_ndvi(parcel_id, crop, out_tif_folder_base, 
                                                             tiles_to_download, parcel, vector_file_name, 
                                                parcel_id_column, buffer_size_meter, vector_color, logfile, jpg_resolution, acq_dates, merged_ndvi_files)                                                

        #Calculate NDVI statistics, output to csv files
        batch_utils.calculate_ndvi_statistics(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, 
                                              vector_file_name, parcel_id_column, logfile)

        #Plot NDVI profile graph
        ndvi_profile = graph_utils.display_ndvi_profiles(parcel_id, crop, plot_title, out_tif_folder_base, logfile, 
                                               add_error_bars = True)     

        #Calendar view of NDVI histograms
        plot_utils.plot_histogram_for_one_parcel(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, 
                                            parcel_id_column, logfile)
                                            
        #Calendar view of Red-NIR scatter plots
        plot_utils.plot_scatter_for_one_parcel_fixed_scale_cumulative(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, parcel_id_column, logfile)


####################################################################################
#extract S1 imagettes and calculate corresponding statistics
####################################################################################    
        batch_utils.run_get_and_download_s1_bs_imagettes(raw_chips_s1_batch_url, out_s1_bs_folder,
                                        search_window_start_date, search_window_end_date,
                                        lon, lat, username, password, chipsize, url_base, logfile)    


        batch_utils.run_rescale_s1_bs_images(out_s1_bs_folder, out_s1_bs_folder_rescale)
        batch_utils.run_lut_stretch_one_band_s1_bs(out_s1_bs_folder_rescale, out_s1_bs_folder_rescale_lut, s1_bs_left_percent, s1_bs_right_percent)       
        polarisations = ["VV", "VH"]
        orbit_orientations = ["D", "A"]
        for polarisation in polarisations:
            for orbit_orientation in orbit_orientations:
                plot_utils.calendar_view_s1_bs_imagettes(parcel_id, crop, out_s1_bs_folder_rescale_lut, parcel, vector_file_name, 
                                            parcel_id_column, buffer_size_meter, vector_color, logfile, jpg_resolution, output_s1_bs_calendar_view_folder,
                                            polarisation, orbit_orientation)
        
                batch_utils.calculate_bs_statistics(parcel_id, crop, out_tif_folder_base, parcel, logfile, polarisation, orbit_orientation)
                add_error_bars = False
                graph_utils.display_s1_bs_profiles(parcel_id, crop, plot_title, out_tif_folder_base, logfile, add_error_bars, polarisation, orbit_orientation)
        
        graph_utils.display_s1_bs_profiles_together(parcel_id, crop, plot_title, out_tif_folder_base, logfile, add_error_bars)
                

