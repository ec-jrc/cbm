#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Csaba Wirnhardt
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import time
import geopandas
import download_utils, extract_utils, plot_utils
from glob import glob
import os
import lut
from osgeo import ogr
import datetime
import collections
import warnings
import calendar



def select_parcel(vector_file_name, parcel_id_column, parcel_id, logfile):
    fout = open(logfile, 'a')
    start = time.time()
    parcels = geopandas.read_file(vector_file_name)
    parcel = parcels[parcels[parcel_id_column]==parcel_id]
    print(f"Parcel selected in: {time.time() - start} seconds")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.select_parcel:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return parcel

def run_get_scl_imagettes(parcel, parcel_id, crop, out_tif_folder_base, 
                            search_window_start_date, search_window_end_date, search_split_days,
                            raw_chips_by_location_url, username, password, chipsize,
                            url_base, lon, lat, logfile
                           ):
    fout = open(logfile, 'a')
    start = time.time()                        
    # get the list of SCL imagettes for the parcel in a given date range 
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder

    # lon, lat = download_utils.get_centroid_of_parcel(parcel)

    date_ranges = download_utils.split_date_range(search_window_start_date, search_window_end_date, search_split_days)
    for date_range in date_ranges:
        start_date = date_range[0]
        end_date = date_range[1]
        
        print("Getting SCL imagettes from" , start_date, "to", end_date)
        
        was_error_1 = True
        was_error_2 = True
        while was_error_1:
            locurl, list_of_scl_imagettes, was_error_1 = download_utils.get_scl_imagettes(raw_chips_by_location_url, lon, lat, 
                                                                start_date, end_date, 
                                                                username, password, chipsize)
            
                                                                
        while was_error_2:                                                        
            was_error_2 = download_utils.download_scl_imagettes(url_base, list_of_scl_imagettes, out_tif_folder, username, password)

    print(f"Got list of SCL imagettes and downloaded in: {time.time() - start} seconds")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.run_get_scl_imagettes:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    
def create_list_of_tiles_to_be_downloaded(parcel, parcel_id, crop, out_tif_folder_base, cloud_categories, logfile):
    # create the list of tiles to be downloaded
    warnings.simplefilter(action='ignore', category=FutureWarning)
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder
    
    # get downloaded SCL tile tifs and see if they are cloudfree
    downloaded_scl_files_pattern = out_tif_folder + "/*/*.SCL.tif"
    downloaded_scl_files = glob(downloaded_scl_files_pattern)
    tiles_to_download = []
    for downloaded_scl_file in downloaded_scl_files:  
        is_tile_cloudy = download_utils.is_tile_cloudy_geopandas(downloaded_scl_file, parcel, cloud_categories)
        
        if not is_tile_cloudy:
            tile_scl_name = os.path.basename(downloaded_scl_file)
            tile_name = tile_scl_name.split(".")[0]
            tiles_to_download.append(tile_name)
    print(f"List of tiles to be downloaded created in {time.time() - start} seconds")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.create_list_of_tiles_to_be_downloaded:\t", "{0:.3f}".format(time.time() - start), file=fout)

    fout.close()
    return tiles_to_download
    
def run_get_and_download_band_imagettes(max_number_of_tiles_per_request, tiles_to_download, raw_chips_batch_url,
                                        lon, lat, bands, username, password, chipsize, url_base, 
                                        parcel_id, crop, out_tif_folder_base, logfile): 
    # run the batch chip extract query with the JSON input as POST
    # and get the response which contains the download folder of the extracted chips
    # and download the cloudfree band imagettes
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder

    # max_number_of_tiles_per_request = 12
    number_of_full_requests = len(tiles_to_download)//max_number_of_tiles_per_request
    
    if number_of_full_requests == 0:
        number_of_full_requests = 1

    for request in range(0,number_of_full_requests):
        list_of_band_imagettes = {}
        request_end_index = max_number_of_tiles_per_request*(request+1)
        request_start_index = request_end_index - max_number_of_tiles_per_request
        print("request number:", request)
        tiles_to_download_subset = tiles_to_download[request_start_index:request_end_index]
        
        was_error_1 = True
        was_error_2 = True
        while was_error_1:
            list_of_band_imagettes, was_error_1 = download_utils.get_band_imagettes(raw_chips_batch_url, lon, lat, 
                                               tiles_to_download_subset, 
                                               bands, username, password, chipsize )
        while was_error_2:                                                                          
            was_error_2 = download_utils.download_band_imagettes(url_base, list_of_band_imagettes, out_tif_folder, username, password)
        
        # print("*******************************************")
        # print(list_of_band_imagettes)
        # print("*******************************************")  
        
    last_request_end_index = len(tiles_to_download) + 1
    last_request_start_index = request_end_index

    print("last bunch")
    was_error_1 = True
    was_error_2 = True
    while was_error_1:
        list_of_band_imagettes, was_error_1 = download_utils.get_band_imagettes(raw_chips_batch_url, lon, lat, 
                                               tiles_to_download[last_request_start_index:last_request_end_index], 
                                               bands, username, password, chipsize )
    while was_error_2:                                            
        was_error_2 = download_utils.download_band_imagettes(url_base, list_of_band_imagettes, out_tif_folder, username, password)
        
    # print("*******************************************")
    # print(list_of_band_imagettes)
    # print("*******************************************")  
        
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.run_get_and_download_band_imagettes:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Got list of cloudfree bands and downloaded images: {time.time() - start} seconds")
    
def run_merge_bands(parcel_id, crop, out_tif_folder_base, logfile):
    # look around in the date folders where the bands were downloade and merge bands
    # B08, B11, B04 for each tile where these bands were downloaded and the bands were 
    # not yet merged
    fout = open(logfile, 'a')
    start = time.time()
    download_utils.merge_bands(parcel_id, crop, out_tif_folder_base)
    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.run_merge_bands:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Merging cloudfree bands images in {time.time() - start} seconds")

def run_merge_4_bands(parcel_id, crop, out_tif_folder_base):
    # look around in the date folders where the bands were downloade and merge bands
    # B08, B11, B04 for each tile where these bands were downloaded and the bands were 
    # not yet merged
    start = time.time()
    download_utils.merge_4_bands(parcel_id, crop, out_tif_folder_base)
    print(f"Merging 4 bands images in {time.time() - start} seconds")
    
def run_lut_stretch(parcel_id, crop, out_tif_folder_base, left_percent, right_percent, lut_txt_file, logfile):
    # lut stretch
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder    
    
    lut_bands=[1,2,3]

    merge_folder = out_tif_folder + "_merged"
    merge_lut_folder = out_tif_folder + "_merged_lut_magic"
    # merge_lut_folder = out_tif_folder + "_merged_lut_dynamic"

    if not os.path.exists(merge_lut_folder):
        os.makedirs(merge_lut_folder)

    merged_files_pattern = merge_folder + "/*.tif"
    merged_files = glob(merged_files_pattern)

    for merged_file in merged_files:
    #     print(merged_file)
        merged_file_base = os.path.basename(merged_file)
        merged_file_path = os.path.dirname(merged_file)
        tile_name = merged_file_base.split(".")[0] 
        #get acquisition date from tile name
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)

    #     print(tile_name)
        output = merge_lut_folder + "/" + tile_name + ".tif"

    #     here again: if the lut stretched image is already created we do not create it again
        if os.path.isfile(output):
            #       we already created the lut stretched image for this date for this parcel so we skip it
            print(tile_name + " already created")
        else:
            print("LUT stretching tile: ", tile_name, end="")
            lut.writeMinMaxToFile(merged_file, acq_date, lut_bands, left_percent, right_percent, lut_txt_file, tile_name)
            lut.lutStretchMagicLut(merged_file, output, lut_bands )
            # lut.lutStretch(merged_file, output, left_percent, right_percent, lut_bands )
            print("...done")
    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.run_lut_stretch:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"LUT stretch: {time.time() - start} seconds")
    
def run_lut_stretch_dynamic(parcel_id, crop, out_tif_folder_base, left_percent, right_percent, lut_txt_file, logfile):
    # lut stretch
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder    
    
    lut_bands=[1,2,3]

    merge_folder = out_tif_folder + "_merged"
    # merge_lut_folder = out_tif_folder + "_merged_lut_magic"
    merge_lut_folder = out_tif_folder + "_merged_lut_dynamic"

    if not os.path.exists(merge_lut_folder):
        os.makedirs(merge_lut_folder)

    merged_files_pattern = merge_folder + "/*.tif"
    merged_files = glob(merged_files_pattern)

    for merged_file in merged_files:
    #     print(merged_file)
        merged_file_base = os.path.basename(merged_file)
        merged_file_path = os.path.dirname(merged_file)
        tile_name = merged_file_base.split(".")[0] 
        #get acquisition date from tile name
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)

    #     print(tile_name)
        output = merge_lut_folder + "/" + tile_name + ".tif"

    #     here again: if the lut stretched image is already created we do not create it again
        if os.path.isfile(output):
            #       we already created the lut stretched image for this date for this parcel so we skip it
            print(tile_name + " already created")
        else:
            print("LUT stretching tile: ", tile_name, end="")
            lut.writeMinMaxToFile(merged_file, acq_date, lut_bands, left_percent, right_percent, lut_txt_file, tile_name)
            lut.lutStretchMagicLut(merged_file, output, lut_bands )
            # lut.lutStretch(merged_file, output, left_percent, right_percent, lut_bands )
            print("...done")
    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.run_lut_stretch_dynamic:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"LUT stretch: {time.time() - start} seconds")    

def get_merged_lutstretched_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base, logfile):
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder        
    merge_lut_folder = out_tif_folder + "_merged_lut_magic"
    # merge_lut_folder = out_tif_folder + "_merged_lut_dynamic"
    merged_lut_files_pattern = merge_lut_folder + "/*.tif"
    merged_lut_files = glob(merged_lut_files_pattern)

    acq_dates = []

    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        acq_dates.append(acq_date)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.get_merged_lutstretched_files_and_acquisition_dates:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return acq_dates, merged_lut_files
    
def get_merged_lutstretched_files_and_acquisition_dates_dynamic(parcel_id, crop, out_tif_folder_base, logfile):
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder        
    # merge_lut_folder = out_tif_folder + "_merged_lut_magic"
    merge_lut_folder = out_tif_folder + "_merged_lut_dynamic"
    merged_lut_files_pattern = merge_lut_folder + "/*.tif"
    merged_lut_files = glob(merged_lut_files_pattern)

    acq_dates = []

    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        acq_dates.append(acq_date)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.get_merged_lutstretched_files_and_acquisition_dates_dynamic:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return acq_dates, merged_lut_files    

def get_merged_ndvi_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base):
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder        
    merge_lut_folder = out_tif_folder + "_merged_ndvi"
    merged_lut_files_pattern = merge_lut_folder + "/*.tif"
    merged_lut_files = glob(merged_lut_files_pattern)

    acq_dates = []

    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        acq_dates.append(acq_date)
    return acq_dates, merged_lut_files
    
def get_merged_ndwi_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base):
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder        
    merge_lut_folder = out_tif_folder + "_merged_ndwi"
    merged_lut_files_pattern = merge_lut_folder + "/*.tif"
    merged_lut_files = glob(merged_lut_files_pattern)

    acq_dates = []

    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        acq_dates.append(acq_date)
    return acq_dates, merged_lut_files    
    
def get_merged_tif_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base):
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder        
    merge_lut_folder = out_tif_folder + "_merged"
    merged_lut_files_pattern = merge_lut_folder + "/*.tif"
    merged_lut_files = glob(merged_lut_files_pattern)

    acq_dates = []

    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        acq_dates.append(acq_date)
    return acq_dates, merged_lut_files
    
def get_merged_tif_files_and_acquisition_dates_in_dict(parcel_id, crop, out_tif_folder_base):
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder        
    merge_lut_folder = out_tif_folder + "_merged"
    merged_lut_files_pattern = merge_lut_folder + "/*.tif"
    merged_lut_files = glob(merged_lut_files_pattern)

    acq_dates_tif_files_dict = {}

    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        acq_dates_tif_files_dict[acq_date]=merged_lut_file
    return collections.OrderedDict(sorted(acq_dates_tif_files_dict.items()))
    
def run_ndvi_creation(parcel_id, crop, out_tif_folder_base, logfile):
    fout = open(logfile, 'a')
    start = time.time()
    # create ndvi image
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder    
    
    lut_bands=[1,2,3]

    merge_folder = out_tif_folder + "_merged"
    merge_ndvi_folder = out_tif_folder + "_merged_ndvi"

    if not os.path.exists(merge_ndvi_folder):
        os.makedirs(merge_ndvi_folder)

    merged_files_pattern = merge_folder + "/*.tif"
    merged_files = glob(merged_files_pattern)

    for merged_file in merged_files:
    #     print(merged_file)
        merged_file_base = os.path.basename(merged_file)
        merged_file_path = os.path.dirname(merged_file)
        tile_name = merged_file_base.split(".")[0] 
        #get acquisition date from tile name
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)

    #     print(tile_name)
        output = merge_ndvi_folder + "/" + tile_name + ".tif"

    #     here again: if the ndvi image image is already created we do not create it again
        if os.path.isfile(output):
            #       we already created the ndvi image for this date for this parcel so we skip it
            print(tile_name + " ndvi already created")
        else:
            print("Creating NDVI for tile: ", tile_name, end="")
            
            extract_utils.calculate_ndvi(merged_file, output)
            print("...done")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.run_ndvi_creation:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"NDVI created in: {time.time() - start} seconds")
    
def run_ndwi_creation(parcel_id, crop, out_tif_folder_base, logfile):
    fout = open(logfile, 'a')
    start = time.time()
    # create ndwi image
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder    
    
    lut_bands=[1,2,3]

    merge_folder = out_tif_folder + "_merged"
    merge_ndwi_folder = out_tif_folder + "_merged_ndwi"

    if not os.path.exists(merge_ndwi_folder):
        os.makedirs(merge_ndwi_folder)

    merged_files_pattern = merge_folder + "/*.tif"
    merged_files = glob(merged_files_pattern)

    for merged_file in merged_files:
    #     print(merged_file)
        merged_file_base = os.path.basename(merged_file)
        merged_file_path = os.path.dirname(merged_file)
        tile_name = merged_file_base.split(".")[0] 
        #get acquisition date from tile name
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)

    #     print(tile_name)
        output = merge_ndwi_folder + "/" + tile_name + ".tif"

    #     here again: if the ndwi image image is already created we do not create it again
        if os.path.isfile(output):
            #       we already created the ndwi image for this date for this parcel so we skip it
            print(tile_name + " ndwi already created")
        else:
            print("Creating NDWI for tile: ", tile_name, end="")
            
            extract_utils.calculate_ndwi(merged_file, output)
            print("...done")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.run_ndwi_creation:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"NDWI created in: {time.time() - start} seconds")    
    
def calculate_ndvi_statistics(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, parcel_id_column, logfile):
    fout = open(logfile, 'a')   
    start = time.time()
                                                                                              
    acq_dates, merged_ndvi_files = get_merged_ndvi_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base)                                                                                         

    chip_folder = str(parcel_id) + '_' + crop
    output_ndvi_folder = out_tif_folder_base + "/ndvi"
    output_ndvi_csv_file = output_ndvi_folder + "/" + chip_folder + "_ndvi.csv"

    if not os.path.exists(output_ndvi_folder):
        os.makedirs(output_ndvi_folder)

    first_line ="Field_ID,acq_date,ndvi_mean,ndvi_count,ndvi_std"
    print(first_line, file=open(output_ndvi_csv_file, "w"))

    for merged_ndvi_file in merged_ndvi_files:
        merged_ndvi_file_base = os.path.basename(merged_ndvi_file)
        merged_ndvi_file_path = os.path.dirname(merged_ndvi_file)
        tile_name = merged_ndvi_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        
        # print(merged_ndvi_file)
        ndvi_mean, ndvi_count, ndvi_std = extract_utils.extract_stats_for_one_parcel_geopandas_presel(merged_ndvi_file, parcel)
        
        # print(parcel_id, acq_date, ndvi_mean, ndvi_count, ndvi_std, sep=',')
        print(parcel_id, acq_date, ndvi_mean, ndvi_count, ndvi_std, sep=',',
                file=open(output_ndvi_csv_file, "a"))
 
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.calculate_ndvi_statistics:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"NDVI stats read in: {time.time() - start} seconds")

def calculate_ndwi_statistics(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, parcel_id_column, logfile):
    fout = open(logfile, 'a')   
    start = time.time()
                                                                                              
    acq_dates, merged_ndwi_files = get_merged_ndwi_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base)                                                                                         

    chip_folder = str(parcel_id) + '_' + crop
    output_ndwi_folder = out_tif_folder_base + "/ndwi"
    output_ndwi_csv_file = output_ndwi_folder + "/" + chip_folder + "_ndwi.csv"

    if not os.path.exists(output_ndwi_folder):
        os.makedirs(output_ndwi_folder)

    first_line ="Field_ID,acq_date,ndwi_mean,ndwi_count,ndwi_std"
    print(first_line, file=open(output_ndwi_csv_file, "w"))

    for merged_ndwi_file in merged_ndwi_files:
        merged_ndwi_file_base = os.path.basename(merged_ndwi_file)
        merged_ndwi_file_path = os.path.dirname(merged_ndwi_file)
        tile_name = merged_ndwi_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        
        # print(merged_ndwi_file)
        ndwi_mean, ndwi_count, ndwi_std = extract_utils.extract_stats_for_one_parcel_geopandas_presel(merged_ndwi_file, parcel)
        
        # print(parcel_id, acq_date, ndwi_mean, ndwi_count, ndwi_std, sep=',')
        print(parcel_id, acq_date, ndwi_mean, ndwi_count, ndwi_std, sep=',',
                file=open(output_ndwi_csv_file, "a"))
 
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.calculate_ndwi_statistics:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"ndwi stats read in: {time.time() - start} seconds")    

def calculate_bs_statistics(parcel_id, crop, out_tif_folder_base, parcel, logfile, polarisation, orbit_orientation):
    fout = open(logfile, 'a')   
    start = time.time()
                                                                                              
    chip_folder = str(parcel_id) + '_' + crop
    output_s1_bs_folder = out_tif_folder_base + "/s1_bs"
    output_s1_bs_csv_file = output_s1_bs_folder + "/" + chip_folder + "_s1bs_" + polarisation + "_" + orbit_orientation + ".csv"

    acquisition_dates_and_s1_bs_files_dict = plot_utils.get_acquisition_dates_and_s1_bs_files_dict(out_tif_folder_base + "/" + chip_folder + "_s1_bs", polarisation, orbit_orientation) 
    
    
    if not os.path.exists(output_s1_bs_folder):
        os.makedirs(output_s1_bs_folder)

    first_line ="Field_ID,acq_date,bs_mean,bs_count,bs_std"
    print(first_line, file=open(output_s1_bs_csv_file, "w"))
    

    for acq_date, s1_bs_file in acquisition_dates_and_s1_bs_files_dict.items(): 
        bs_mean, bs_count, bs_std = extract_utils.extract_stats_for_one_parcel_geopandas_presel_bs(s1_bs_file, parcel)
        
        if bs_mean != None:
            # print(parcel_id, acq_date, bs_mean, bs_count, bs_std, sep=',')
            print(parcel_id, acq_date, bs_mean, bs_count, bs_std, sep=',',
                    file=open(output_s1_bs_csv_file, "a"))
 
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.calculate_bs_statistics:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print("S1 BS_" + polarisation + "_" + orbit_orientation + f" stats read in: {time.time() - start} seconds")
    
def get_all_parcel_ids_from_parcel_shape(parcel_shp, parcel_id_column, crop_name_column):
    ds=ogr.Open(parcel_shp)
    lyr=ds.GetLayer()
    parcel_id_crop_list = []
    for feat in lyr:
        parcel_id = feat.GetField(parcel_id_column)
        crop_name = feat.GetField(crop_name_column)
        if crop_name is None:
            crop_name = ""
        parcel_id_crop_list.append((parcel_id,crop_name.replace(" ", "_")))
    parcel_id_crop_list = sorted(parcel_id_crop_list, key=getKey)            
    return parcel_id_crop_list

def getKey(item):
    return item[0]

# l = [[2, 3], [6, 7], [3, 34], [24, 64], [1, 43]]

# sorted(l, key=getKey)    
    
def does_ndvi_csv_exist(parcel_id, crop, out_tif_folder_base):    
    chip_folder = str(parcel_id) + '_' + crop
    output_ndvi_folder = out_tif_folder_base + "/ndvi"
    output_ndvi_csv_file = output_ndvi_folder + "/" + chip_folder + "_ndvi.csv"

    
    if os.path.isfile(output_ndvi_csv_file):
        return True
    else:
        return False
        
def does_ndvi_graph_exist(parcel_id, out_tif_folder_base):    
    output_ndvi_graph_folder = out_tif_folder_base + "/ndvi_graphs"
    output_ndvi_graph_file = output_ndvi_graph_folder + "/parcel_id_" + str(parcel_id) + "_NDVI.jpg"

    
    if os.path.isfile(output_ndvi_graph_file):
        return True
    else:
        return False
        
def run_get_and_download_s1_bs_imagettes(raw_chips_s1_batch_url, out_s1_bs_folder,
                                        search_window_start_date, search_window_end_date,
                                        lon, lat, username, password, chipsize, url_base, logfile): 
                                        
# list_of_s1_bs_imagettes, was_error_1 = download_utils.get_s1_bs_imagettes(raw_chips_s1_batch_url, lon, lat, start_date, end_date, username, password, chipsize)    
# download_utils.download_s1_bs_imagettes(url_base, list_of_s1_bs_imagettes, out_s1_bs_folder, username, password)                                    
                                        
    # run the batch chip extract query with the JSON input as POST
    # and get the response which contains the download folder of the extracted chips
    # and download the s1 backscatter imagettes
    fout = open(logfile, 'a')
    start = time.time()

    # we get and download the s1 bs images by month
    # search_window_start_date, search_window_end_date


# search_window_start_date = "2019-11-15"
# search_window_end_date = "2020-09-15"

    dt_search_window_start_date = plot_utils.get_date_from_string(search_window_start_date)
    dt_search_window_end_date = plot_utils.get_date_from_string(search_window_end_date)


# print(last_day_of_month(dt_search_window_start_date))
# print(add_one_month(dt_search_window_start_date))

    act_start_date = dt_search_window_start_date

    while act_start_date < dt_search_window_end_date:
        act_end_date = last_day_of_month(act_start_date)
        
        if act_start_date == dt_search_window_start_date:
            was_error_1 = True
            was_error_2 = True
            while was_error_1:
                list_of_s1_bs_imagettes, was_error_1 = download_utils.get_s1_bs_imagettes(raw_chips_s1_batch_url, lon, lat, str(act_start_date), str(act_end_date), username, password, chipsize)    
            while was_error_2:             
                was_error_2 = download_utils.download_s1_bs_imagettes(url_base, list_of_s1_bs_imagettes, out_s1_bs_folder, username, password)    

        elif act_end_date > dt_search_window_end_date:
            act_end_date = dt_search_window_end_date
            was_error_1 = True
            was_error_2 = True
            while was_error_1:
                list_of_s1_bs_imagettes, was_error_1 = download_utils.get_s1_bs_imagettes(raw_chips_s1_batch_url, lon, lat, str(act_start_date), str(act_end_date), username, password, chipsize)    
            while was_error_2:             
                was_error_2 = download_utils.download_s1_bs_imagettes(url_base, list_of_s1_bs_imagettes, out_s1_bs_folder, username, password)    

        else:
            was_error_1 = True
            was_error_2 = True
            while was_error_1:
                list_of_s1_bs_imagettes, was_error_1 = download_utils.get_s1_bs_imagettes(raw_chips_s1_batch_url, lon, lat, str(act_start_date), str(act_end_date), username, password, chipsize)    
            while was_error_2:             
                was_error_2 = download_utils.download_s1_bs_imagettes(url_base, list_of_s1_bs_imagettes, out_s1_bs_folder, username, password)    

        act_start_date = add_one_month(act_start_date)    
    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t\tbatch_utils.run_get_and_download_s1_bs_imagettes:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Got list of cloudfree bands and downloaded images: {time.time() - start} seconds")
    
def run_rescale_s1_bs_images(out_s1_bs_folder, out_s1_bs_folder_rescale):
    # we take all the downloaded s1 bs images for the given parcel and rescale them to uint16
    
    if not os.path.exists(out_s1_bs_folder_rescale):
        os.makedirs(out_s1_bs_folder_rescale)

    raw_files_pattern = out_s1_bs_folder + "/*.tif"
    raw_files = glob(raw_files_pattern)
    
    for raw_file in raw_files:
        raw_file_base = os.path.basename(raw_file)
        actdate = raw_file_base.split(".")[0]       

        #     print(tile_name)
        output = out_s1_bs_folder_rescale + "/" + actdate + ".tif"
        download_utils.rescale_s1_bs_image(raw_file, output)
        
def run_lut_stretch_one_band_s1_bs(out_s1_bs_folder_rescale, out_s1_bs_folder_rescale_lut, s1_bs_left_percent, s1_bs_right_percent):
    # we take all the downloaded s1 bs images for the given parcel and rescale them to uint16
    
    if not os.path.exists(out_s1_bs_folder_rescale_lut):
        os.makedirs(out_s1_bs_folder_rescale_lut)

    rescaled_files_pattern = out_s1_bs_folder_rescale + "/*.tif"
    rescaled_files = glob(rescaled_files_pattern)
    
    for rescaled_file in rescaled_files:
        rescaled_file_base = os.path.basename(rescaled_file)
        actdate = rescaled_file_base.split(".")[0] 
         

        print(actdate)
        output = out_s1_bs_folder_rescale_lut + "/" + actdate + ".tif"
        lut.lut_stretch_one_band_s1_bs(rescaled_file, output, s1_bs_left_percent, s1_bs_right_percent)
        

def add_one_month(orig_date):
    # advance year and month by one month
    new_year = orig_date.year
    new_month = orig_date.month + 1
    # note: in datetime.date, months go from 1 to 12
    if new_month > 12:
        new_year += 1
        new_month -= 12

    last_day_of_month = calendar.monthrange(new_year, new_month)[1]
    new_day = min(orig_date.day, last_day_of_month)

    return orig_date.replace(year=new_year, month=new_month, day=new_day)        
    
def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)    
    
def run_lut_stretch_dynamic(parcel_id, crop, out_tif_folder_base, left_percent, right_percent, lut_txt_file, logfile):
    # lut stretch
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder    
    
    lut_bands=[1,2,3]

    merge_folder = out_tif_folder + "_merged"
    # merge_lut_folder = out_tif_folder + "_merged_lut_magic"
    merge_lut_folder = out_tif_folder + "_merged_lut_dynamic"

    if not os.path.exists(merge_lut_folder):
        os.makedirs(merge_lut_folder)

    merged_files_pattern = merge_folder + "/*.tif"
    merged_files = glob(merged_files_pattern)

    for merged_file in merged_files:
    #     print(merged_file)
        merged_file_base = os.path.basename(merged_file)
        merged_file_path = os.path.dirname(merged_file)
        tile_name = merged_file_base.split(".")[0] 
        #get acquisition date from tile name
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)

    #     print(tile_name)
        output = merge_lut_folder + "/" + tile_name + ".tif"

    #     here again: if the lut stretched image is already created we do not create it again
        if os.path.isfile(output):
            #       we already created the lut stretched image for this date for this parcel so we skip it
            print(tile_name + " already created")
        else:
            print("LUT stretching tile: ", tile_name, end="")
            lut.writeMinMaxToFile(merged_file, acq_date, lut_bands, left_percent, right_percent, lut_txt_file, tile_name)
            # lut.lutStretchMagicLut(merged_file, output, lut_bands )
            lut.lutStretch(merged_file, output, left_percent, right_percent, lut_bands )
            print("...done")
    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.run_lut_stretch_dynamic:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"LUT stretch dynamic: {time.time() - start} seconds")    
    
def get_merged_dynamically_lutstretched_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base, logfile):
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    out_tif_folder = out_tif_folder_base + "/" + chip_folder        
    # merge_lut_folder = out_tif_folder + "_merged_lut_magic"
    merge_lut_folder = out_tif_folder + "_merged_lut_dynamic"
    merged_lut_files_pattern = merge_lut_folder + "/*.tif"
    merged_lut_files = glob(merged_lut_files_pattern)

    acq_dates = []

    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        acq_dates.append(acq_date)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tbatch_utils.get_merged_dynamically_lutstretched_files_and_acquisition_dates:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return acq_dates, merged_lut_files    