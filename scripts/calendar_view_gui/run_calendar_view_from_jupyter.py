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
import download_utils, plot_utils, batch_utils, graph_utils, parcel_utils
import db_utils
import geopandas
import json
import datetime


def run_calendar_view(**kwargs):
    print(json.dumps(kwargs, indent=4))
    
### What to run parameters    
    #first column
    get_scl=kwargs.get("get_scl")    
    get_bands=kwargs.get("get_bands")
    merge_bands=kwargs.get("merge_bands")
    lut_stretch_magic=kwargs.get("lut_stretch_magic")
    cv_lut_magic=kwargs.get("cv_lut_magic")
    lut_stretch_dynamic=kwargs.get("lut_stretch_dynamic")
    cv_lut_dynamic=kwargs.get("cv_lut_dynamic")
    stats_band=kwargs.get("stats_band")
    graphs_band=kwargs.get("graphs_band")
    
    #second column
    create_ndvi=kwargs.get("create_ndvi")
    cv_ndvi=kwargs.get("cv_ndvi")
    stats_ndvi=kwargs.get("stats_ndvi")
    graphs_ndvi=kwargs.get("graphs_ndvi")
    create_bsi=kwargs.get("create_bsi")
    cv_bsi=kwargs.get("cv_bsi")
    stats_bsi=kwargs.get("stats_bsi")
    graphs_bsi=kwargs.get("graphs_bsi")
    cv_ndvi_hist=kwargs.get("cv_ndvi_hist")
    cv_red_nir_scatter=kwargs.get("cv_red_nir_scatter")

    #third column    
    get_coh=kwargs.get("get_coh")
    stats_coh=kwargs.get("stats_coh")
    graph_coh=kwargs.get("graph_coh")
    get_bs=kwargs.get("get_bs")
    cv_bs=kwargs.get("cv_bs")
    stats_bs=kwargs.get("stats_bs")
    graph_bs=kwargs.get("graph_bs")

### vector and output folder parameters
    vector_file_name=kwargs.get("vector_file_name")
    out_tif_folder_base=kwargs.get("out_tif_folder_base")
    
    parcel_id_column = kwargs.get("parcel_id_column")
    crop_name_column = kwargs.get("crop_name_column")
    list_of_parcel_ids_to_process=kwargs.get("list_of_parcel_ids_to_process")
    
    
### dates parameters    
    search_window_start_date=kwargs.get("search_window_start_date")
    search_window_end_date=kwargs.get("search_window_end_date")    
    index_graph_start_date=kwargs.get("index_graph_start_date")    
    index_graph_end_date=kwargs.get("index_graph_end_date") 

### other parameters    
    plot_title = kwargs.get("plot_title") 
    
    exclude_cirrus = kwargs.get("exclude_cirrus") 
    buffer_size_meter = kwargs.get("buffer_size_meter") 
    centroid_shift_degrees = kwargs.get("centroid_shift_degrees") 
    
    MS = kwargs.get("MS") 
    year = kwargs.get("year")
    
    api_user = kwargs.get("api_user")
    api_pass = kwargs.get("api_pass")
    ptype = kwargs.get("ptype")
    
  


    if not os.path.exists(out_tif_folder_base):
        os.makedirs(out_tif_folder_base)
    curr_time_stamp=datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    output_json_file = out_tif_folder_base + "/run_params_" + curr_time_stamp + ".json"

    with open(output_json_file, 'w') as fp:
        json.dump(kwargs, fp,  indent=4)
    
    # setting parameters that are used by the different functions below
#    and are still hard-coded
    username = 'JRC_D5'
    password = 'djB2_e'
    url_base = "http://185.178.85.226"
    if exclude_cirrus:
        cloud_categories = [0,1,3,8,9,10,11] # exclude 10 which is thin cirrus
    else:
        cloud_categories = [0,1,3,8,9,11]
    
    if stats_band:
        bands =  ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]
    elif create_bsi:
        bands = ["B04", "B08", "B11", "B02"]
    else:
        bands = ["B04", "B08", "B11"]
    
    raw_chips_by_location_url = url_base + "/query/rawChipByLocation"
    raw_chips_batch_url = url_base + "/query/rawChipsBatch"
    raw_chips_s1_batch_url = url_base + "/query/rawS1ChipsBatch"
    
    # histogram cut at both ends for dynamic LUT stretching
    left_percent = 1
    right_percent = 1
    s1_bs_left_percent = 1
    s1_bs_right_percent = 4
    
    lut_txt_file = out_tif_folder_base + "/lut.txt"
    logfile = out_tif_folder_base + "/log.txt"
    
    search_split_days = 30
    #built in maximum number of tiles that can be requested is 36
    #but that by separate bands, so if we have 3 bands the max
    #number of tiles we can request at one go is 36/3=12
    max_number_of_tiles_per_request = int(36 / len(bands))
    
    vector_color = "yellow"
    
    jpg_resolution = 100
    
    output_s1_bs_calendar_view_folder = out_tif_folder_base + "/s1_bs_calendar_view"
    
    if not os.path.exists(out_tif_folder_base):
        os.makedirs(out_tif_folder_base)
        

    # get all parcels in a geopandas dataframe from the ESRI shapefile
    parcels = geopandas.read_file(vector_file_name)

        
    for fid in list_of_parcel_ids_to_process:
        parcel = parcels[parcels[parcel_id_column]==fid]
        parcel_area_ha = parcel_utils.get_parcel_area_ha_2decimals_str(parcel)
        parcel_id = fid
        crop = parcel[crop_name_column].values[0]
        
        print(parcel_id, crop, parcel_area_ha)
        
        # convert parcel_id to a string that can be used as filename           
        parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
        chip_folder = str(parcel_id_as_filename) + '_' + crop     
        
        out_s1_bs_folder = out_tif_folder_base + "/" + chip_folder + "_s1_bs"
        out_s1_coh6_folder = out_tif_folder_base + "/" + chip_folder + "_s1_coh6"
        out_s1_bs_folder_rescale = out_tif_folder_base + "/" + chip_folder + "_s1_bs_rescale"
        out_s1_bs_folder_rescale_lut = out_tif_folder_base + "/" + chip_folder + "_s1_bs_rescale_lut"        
                
        # parcel = batch_utils.select_parcel(vector_file_name, parcel_id_column, parcel_id, logfile)
        
        chipsize = str(int(download_utils.get_max_parcel_extent_in_meters(parcel) + buffer_size_meter)+ buffer_size_meter*2+50)
        lon, lat = download_utils.get_centroid_of_parcel(parcel_id, parcel, centroid_shift_degrees, logfile)
        
        
#         #Get and downlod Scene Classification Layer imagettes
        if get_scl:
            batch_utils.run_get_scl_imagettes(parcel, parcel_id, crop, out_tif_folder_base, 
                                     search_window_start_date, search_window_end_date, search_split_days,
                                     raw_chips_by_location_url, username, password, chipsize,
                                     url_base, lon, lat, logfile
                                    )
        
         #create a list of tiles to be downloaded (based on cloud cover inside the parcel) only if necessary
        if  get_bands or \
            cv_lut_magic or \
            cv_lut_dynamic or \
            cv_ndvi or \
            stats_ndvi or \
            cv_ndvi_hist or \
            cv_red_nir_scatter:

            if get_scl:
                tiles_to_download = batch_utils.create_list_of_tiles_to_be_downloaded(parcel, parcel_id, crop, out_tif_folder_base, 
                                                                                   cloud_categories, logfile)
            else:
                tstype = "s2"    
                tiles_to_download = db_utils.create_list_of_tiles_to_be_downloaded_from_RESTful(MS, year, parcel_id, 
                                                        search_window_start_date, search_window_end_date,
                                                        cloud_categories, api_user, api_pass, tstype, ptype)                

                if tiles_to_download == None or len(tiles_to_download) == 0:
                    print("No histogram data in the database, we need to download the SCL files " \
                          "and calculate statistics from those")
                    batch_utils.run_get_scl_imagettes(parcel, parcel_id, crop, out_tif_folder_base, 
                             search_window_start_date, search_window_end_date, search_split_days,
                             raw_chips_by_location_url, username, password, chipsize,
                             url_base, lon, lat, logfile
                            )
                    tiles_to_download = batch_utils.create_list_of_tiles_to_be_downloaded(parcel, parcel_id, crop, out_tif_folder_base, 
                                                                   cloud_categories, logfile)

                else:    
                    print(tiles_to_download)                
                
        
         #Get and download band imagettes
        if get_bands:
             batch_utils.run_get_and_download_band_imagettes(max_number_of_tiles_per_request, tiles_to_download, 
                                                         raw_chips_batch_url,
                                                 lon, lat, bands, username, password, chipsize, url_base, 
                                                 parcel_id, crop, out_tif_folder_base, logfile)
        
         #merge downloaded bands
        if merge_bands:
            batch_utils.run_merge_bands(parcel_id, crop, out_tif_folder_base, logfile)
        
         #Create LUT stretched images with fixed stretching        
        if lut_stretch_magic:
            batch_utils.run_lut_stretch(parcel_id, crop, out_tif_folder_base, left_percent, right_percent, lut_txt_file, logfile)




 
        if cv_lut_magic:
            #Get list of fix LUT stretched images
            acq_dates, merged_lut_files = batch_utils.get_merged_lutstretched_files_and_acquisition_dates(parcel_id, crop, 
                                                                                                       out_tif_folder_base,
                                                                                                       logfile)
             #Create calendar view of fix LUT stretched imagettes
            vector_color = "yellow"
            fig, a = plot_utils.calendar_view_half_weekly_more_param(parcel_id, crop, out_tif_folder_base, 
                                                                  tiles_to_download, parcel, vector_file_name, 
                                                                  parcel_id_column, buffer_size_meter, vector_color, logfile, 
                                                                  jpg_resolution, acq_dates, merged_lut_files)
                                                
        #Create LUT stretched images with dynamic stretching
        if lut_stretch_dynamic:
            batch_utils.run_lut_stretch_dynamic(parcel_id, crop, out_tif_folder_base, left_percent, right_percent, 
                                                lut_txt_file, logfile)

                                                
        if cv_lut_dynamic:
            #Get list of dynamic LUT stretched images
            acq_dates, merged_lut_files = batch_utils.get_merged_lutstretched_files_and_acquisition_dates_dynamic(parcel_id, crop, 
                                                                                                         out_tif_folder_base,
                                                                                                         logfile)
             #Create calendar view of dynamic LUT stretched imagettes
            vector_color = "yellow"
            fig, a = plot_utils.calendar_view_half_weekly_more_param_dynamic(parcel_id, crop, out_tif_folder_base, 
                                                                  tiles_to_download, parcel, vector_file_name, 
                                                                  parcel_id_column, buffer_size_meter, vector_color, logfile, 
                                                                  jpg_resolution, acq_dates, merged_lut_files)
        
        #Create NDVI imagettes
        if create_ndvi:
            batch_utils.run_ndvi_creation(parcel_id, crop, out_tif_folder_base, logfile)
        
        if cv_ndvi:
            #Get list of ndvi imagettes
            acq_dates, merged_ndvi_files = batch_utils.get_merged_ndvi_files_and_acquisition_dates(parcel_id, crop, 
                                                                                                   out_tif_folder_base)   
        
             #Calendar view of NDVI imagettes
            vector_color = "black"
            fig, a = plot_utils.calendar_view_half_weekly_more_param_ndvi(parcel_id, crop, out_tif_folder_base, 
                                                                  tiles_to_download, parcel, vector_file_name, 
                                                                  parcel_id_column, buffer_size_meter, vector_color, 
                                                                  logfile, jpg_resolution, acq_dates, merged_ndvi_files)                                                
        
        #Calculate NDVI statistics, output to csv files
        if stats_ndvi:
            batch_utils.calculate_ndvi_statistics(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, 
                                                  vector_file_name, parcel_id_column, logfile)
        
        #Plot NDVI profile graph
        if graphs_ndvi:
            graph_utils.display_ndvi_profiles(parcel_id, crop, plot_title, out_tif_folder_base, logfile, 
                                              add_error_bars = True)   

            graph_utils.display_ndvi_profiles_with_fixed_date_range(parcel_id, crop, plot_title, out_tif_folder_base, logfile, 
                                            index_graph_start_date, index_graph_end_date, 
                                            parcel_area_ha, add_error_bars = True)                                              
        
        #Calendar view of NDVI histograms
        if cv_ndvi_hist:
            plot_utils.plot_histogram_for_one_parcel(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, 
                                                     vector_file_name, parcel_id_column, logfile, jpg_resolution)
                                            
        #Calendar view of Red-NIR scatter plots
        if cv_red_nir_scatter:
            plot_utils.plot_scatter_for_one_parcel_fixed_scale_cumulative(parcel_id, crop, out_tif_folder_base, 
                                                                          tiles_to_download, parcel, vector_file_name, 
                                                                          parcel_id_column, logfile, jpg_resolution)
        
        # Calculate extra indices
        if create_bsi:
            index_name = "bare_soil_index"        
            acq_dates_band_names_tif_files_list = batch_utils.get_acq_dates_band_names_tif_files_list(parcel_id, crop, 
                                                                                                      out_tif_folder_base)
            batch_utils.create_index_images(parcel_id, crop, out_tif_folder_base, acq_dates_band_names_tif_files_list, index_name)
        
        #Calculate Index statistics, output to csv files
        if stats_bsi:
            batch_utils.calculate_index_statistics(parcel_id, crop, out_tif_folder_base, parcel, logfile, index_name)
        
        #Plot Index profile graph
        if graphs_bsi:
            add_error_bars=True
            graph_utils.display_index_profiles_with_fixed_date_range(parcel_id, crop, plot_title, out_tif_folder_base, 
                                                                     logfile, index_graph_start_date, index_graph_end_date,
                                                                     index_name, add_error_bars)                                               
        
        
        #Calendar view of Index imagettes
        if cv_bsi:
            vector_color = "black"
            fig, a = plot_utils.calendar_view_half_weekly_more_param_index(parcel_id, crop, out_tif_folder_base, 
                                                                  parcel, vector_file_name, 
                                                                  buffer_size_meter, vector_color, logfile, jpg_resolution, 
                                                                  index_name)
        
        #Calculate band statistics, output to csv file
        if stats_band:
            #first check if crop name with spaces was used as folder name
            batch_utils.calculate_band_statistics(parcel_id, crop, out_tif_folder_base, parcel)
            #then check with spaces replaced with underscore
            crop_with_underscore = crop.replace(" ", "_")
            batch_utils.calculate_band_statistics(parcel_id, crop_with_underscore, out_tif_folder_base, parcel)   
        
        if graphs_band:
            graph_utils.display_band_profiles_with_fixed_date_range(parcel_id, index_graph_start_date, 
                                                                    index_graph_end_date, plot_title, out_tif_folder_base)        
    
        if get_coh:        
            batch_utils.run_get_and_download_s1_coh6_imagettes(raw_chips_s1_batch_url, out_s1_coh6_folder,
                                                               search_window_start_date, search_window_end_date,
                                                               lon, lat, username, password, chipsize, url_base, logfile)    
        
        polarisations = ["VV", "VH"]
        orbit_orientations = ["D", "A"]
        vector_color = "yellow"
        if stats_coh:
            for polarisation in polarisations:
                for orbit_orientation in orbit_orientations:
                    batch_utils.calculate_coh6_statistics(parcel_id, crop, out_tif_folder_base, parcel, logfile, 
                                                          polarisation, orbit_orientation)

        if graph_coh:
            add_error_bars = False
            graph_utils.display_s1_coh6_profiles_together(parcel_id, crop, plot_title, out_tif_folder_base, logfile, add_error_bars)
            graph_utils.display_s1_coh6_profiles_together_with_fixed_date_range(parcel_id, crop, plot_title, 
                                                                                out_tif_folder_base, logfile,
                                                                                index_graph_start_date, index_graph_end_date,
                                                                                parcel_area_ha,
                                                                                add_error_bars = False)
          
        if get_bs:
            batch_utils.run_get_and_download_s1_bs_imagettes(raw_chips_s1_batch_url, out_s1_bs_folder,
                                                             search_window_start_date, search_window_end_date,
                                                             lon, lat, username, password, chipsize, url_base, logfile)    
        
        if cv_bs:
            batch_utils.run_rescale_s1_bs_images(out_s1_bs_folder, out_s1_bs_folder_rescale)
            batch_utils.run_lut_stretch_one_band_s1_bs(out_s1_bs_folder_rescale, out_s1_bs_folder_rescale_lut, s1_bs_left_percent, 
                                                       s1_bs_right_percent)       

            for polarisation in polarisations:
                for orbit_orientation in orbit_orientations:
                    plot_utils.calendar_view_s1_bs_imagettes(parcel_id, crop, out_s1_bs_folder_rescale_lut, parcel, 
                                                             vector_file_name, parcel_id_column, buffer_size_meter, 
                                                             vector_color, logfile, jpg_resolution, 
                                                             output_s1_bs_calendar_view_folder, polarisation, orbit_orientation)

        if stats_bs:
            for polarisation in polarisations:
                for orbit_orientation in orbit_orientations:
                    batch_utils.calculate_bs_statistics(parcel_id, crop, out_tif_folder_base, parcel, logfile, polarisation, 
                                                        orbit_orientation)

        if graph_bs:
            add_error_bars = False
            graph_utils.display_s1_bs_profiles_together(parcel_id, crop, plot_title, out_tif_folder_base, logfile, add_error_bars)
            
        