#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Csaba Wirnhardt
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import json
import requests
import os
import fiona
from rasterstats import zonal_stats
from glob import glob
import gdal_merge as gm
import datetime
import time
import rasterio
import warnings
import batch_utils

def get_scl_imagettes(raw_chips_by_location_url, lon, lat, start_date, end_date, username, password, chipsize):
    list_of_scl_imagettes = []
    was_error = False
    wrong_credentials = False
    band = 'SCL'
    locurl = raw_chips_by_location_url + """?lon=\
""" + lon + """&lat=""" + lat + """&start_date=""" + start_date + """&end_date=""" + end_date + """&band=""" + band + """&chipsize=""" + chipsize
    # print(locurl)
    # Parse the response with the standard json module
    print(locurl)
    
    try:
        response = requests.get(locurl, auth = (username, password), timeout=180)
        print(response)
        if response.status_code == 404 or response.status_code == 401:
            if response.status_code == 401:
                print("Please, provide valid credentials to access the RESTFul server")
                wrong_credentials = True

                
            was_error = True
        else:
            list_of_scl_imagettes = json.loads(response.content)
        # print(list_of_scl_imagettes)
    except requests.exceptions.HTTPError as errh:
        was_error = True
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        was_error = True
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        was_error = True
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        was_error = True
        print ("OOps: Something Else",err)
    # else:
        # was_error = True
        # print("Something else happened, maybe 404 http error")
        
    
    
    return locurl, list_of_scl_imagettes, was_error, wrong_credentials
    
def get_scl_imagettes_l1c(raw_chips_by_location_url, lon, lat, start_date, end_date, username, password, chipsize):
    list_of_scl_imagettes = []
    was_error = False
    band = 'B08'
    locurl = raw_chips_by_location_url + """?lon=\
""" + lon + """&lat=""" + lat + """&start_date=""" + start_date + """&end_date=""" + end_date + """&band=""" + band + """&chipsize=""" + chipsize + """&plevel=LEVEL1C"""
    # print(locurl)
    # Parse the response with the standard json module
    print(locurl)
    
    try:
        response = requests.get(locurl, auth = (username, password), timeout=180)
        print(response)
        if response.status_code == 404:
            was_error = True
        else:
            list_of_scl_imagettes = json.loads(response.content)
        # print(list_of_scl_imagettes)
    except requests.exceptions.HTTPError as errh:
        was_error = True
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        was_error = True
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        was_error = True
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        was_error = True
        print ("OOps: Something Else",err)
    # else:
        # was_error = True
        # print("Something else happened, maybe 404 http error")
        
    
    
    return locurl, list_of_scl_imagettes, was_error    
    
def get_centroid_of_parcel(parcel_id, parcel, centroid_shift_degrees, logfile):
    warnings.simplefilter(action='ignore', category=FutureWarning)
    warnings.simplefilter(action='ignore', category=UserWarning)
    
    fout = open(logfile, 'a')
    start = time.time()
    # get centroid of parcel in wgs84 lat, lon
    # we need to convert the numpy dtype to python native datatype with .item() and then to string
    # lon = str(parcel.to_crs("EPSG:4326").centroid.x.item())
    # lat = str(parcel.to_crs("EPSG:4326").centroid.y.item())
    # lon = str(round(parcel.to_crs("EPSG:4326").centroid.x.item(),5))
    # lat = str(round(parcel.to_crs("EPSG:4326").centroid.y.item(),5))

    lon = str("{0:.5f}".format(round(parcel.to_crs("EPSG:4326").centroid.x.item(),5) + centroid_shift_degrees))
    lat = str("{0:.5f}".format(round(parcel.to_crs("EPSG:4326").centroid.y.item(),5) + centroid_shift_degrees))
    
    # lon = str("{0:.5f}".format(1.0210199999999998))
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tdownload_utils.get_centroid_of_parcel:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return lon, lat
    
def download_scl_imagettes(url_base, list_of_scl_imagettes, out_tif_folder, username, password):
    chips_list = list_of_scl_imagettes['chips']
    was_error = False
    
    for tif_name in chips_list:
        tif_base_name = tif_name.split("/")[3]
        acq_date_full = tif_base_name.split("_")[2]
        acq_date = acq_date_full[0:4] + "-" + acq_date_full[4:6] + "-" + acq_date_full[6:8]
        tif_url = url_base + tif_name
        tif_base_name = tif_name.split("/")[3]
        print("Downloading SCL image: " + tif_base_name, end="")
        out_tif_folder_date = out_tif_folder + "/" + acq_date
        if not os.path.exists(out_tif_folder_date):
            os.makedirs(out_tif_folder_date)
 
        output_tif_file = out_tif_folder_date + "/" + tif_base_name
        
        if os.path.isfile(output_tif_file):
    #       if we already downloaded the SCL imagette for this parcel we skip it
            print(output_tif_file + " already downloaded", end="")
        else:
            try:
                r = requests.get(tif_url,  auth = (username, password), timeout=180)
                # print(r)
                with open(output_tif_file, 'wb') as f:
                    f.write(r.content)    
            except requests.exceptions.HTTPError as errh:
                was_error = True
                print ("Http Error:",errh)
            except requests.exceptions.ConnectionError as errc:
                was_error = True
                print ("Error Connecting:",errc)
            except requests.exceptions.Timeout as errt:
                was_error = True
                print ("Timeout Error:",errt)
            except requests.exceptions.RequestException as err:
                was_error = True
                print ("OOps: Something Else",err)
           
        print("...done")
    return was_error      
        
def is_tile_cloudy(tif_file, vector_file_name, parcel_id_column, parcel_id, cloud_categories):
    warnings.simplefilter(action='ignore', category=UserWarning)
    is_cloudy = False
    
    parcel_stats = extract_stats_for_one_parcel_categorical(tif_file, vector_file_name, parcel_id_column, parcel_id)
    keys = [*parcel_stats]
    for key in keys:
        if key in cloud_categories:
            is_cloudy = True   
    return is_cloudy
    
def extract_stats_for_one_parcel_categorical(tif_file, vector_file_name, parcel_id_column, parcel_id):
    with fiona.open(vector_file_name) as src:
        filtered = filter(lambda f: f['properties'][parcel_id_column]==parcel_id, src)
        shapes = [feature["geometry"] for feature in filtered]
    
    scl_stats_for_parcel = zonal_stats(shapes,
                     tif_file,
                categorical=True)[0]
    return scl_stats_for_parcel
    
def get_band_imagettes(raw_chips_batch_url, lon, lat, tiles_to_download, bands, username, password, chipsize ):
    was_error = False
    response = None
    list_of_band_imagettes = {}
    post_dict = {}
    lon_float = round(float(lon),5)
    lat_float = round(float(lat),5)
    post_dict["lon"] = lon_float
    post_dict["lat"] = lat_float
    post_dict["tiles"] = tiles_to_download

    post_dict["bands"] = bands
    # we keep the same chipsize as in the SCL download, but change it to integer because in the 
    # SCL download request it was string
    post_dict["chipsize"] = int(chipsize)
    print(post_dict)
    try:
        response = requests.post(raw_chips_batch_url, json=post_dict, auth = (username, password), timeout=300)
        print(response)
        if response.status_code == 404:
            was_error = True
        else:
            list_of_band_imagettes = json.loads(response.content)
    except requests.exceptions.HTTPError as errh:
        was_error = True
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        was_error = True
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        was_error = True
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        was_error = True
        print ("OOps: Something Else",err)    
    
    
    
    return list_of_band_imagettes, was_error
    
def get_band_imagettes_l1c(raw_chips_batch_url, lon, lat, tiles_to_download, bands, username, password, chipsize ):
    was_error = False
    response = None
    list_of_band_imagettes = {}
    post_dict = {}
    lon_float = round(float(lon),5)
    lat_float = round(float(lat),5)
    post_dict["lon"] = lon_float
    post_dict["lat"] = lat_float
    post_dict["tiles"] = tiles_to_download

    post_dict["bands"] = bands
    # we keep the same chipsize as in the SCL download, but change it to integer because in the 
    # SCL download request it was string
    post_dict["chipsize"] = int(chipsize)
    post_dict["plevel"] = 'LEVEL1C'
    print(post_dict)
    try:
        response = requests.post(raw_chips_batch_url, json=post_dict, auth = (username, password), timeout=180)
        print(response)
        if response.status_code == 404:
            was_error = True
        else:
            list_of_band_imagettes = json.loads(response.content)
    except requests.exceptions.HTTPError as errh:
        was_error = True
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        was_error = True
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        was_error = True
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        was_error = True
        print ("OOps: Something Else",err)    
    
    
    
    return list_of_band_imagettes, was_error    
    
def download_band_imagettes(url_base, list_of_band_imagettes, out_tif_folder, username, password):
    # download the band tifs that were generated with the batch chip extract request
    was_error = False
    chips_list = list_of_band_imagettes['chips']
    for tif_name in chips_list:
        tif_base_name = tif_name.split("/")[3]
        acq_date_full = tif_base_name.split("_")[2]
        acq_date = acq_date_full[0:4] + "-" + acq_date_full[4:6] + "-" + acq_date_full[6:8]
        tif_url = url_base + tif_name
        print("Downloading band image: " + tif_base_name, end="")
        out_tif_folder_date = out_tif_folder + "/" + acq_date
        if not os.path.exists(out_tif_folder_date):
            os.makedirs(out_tif_folder_date)

        output_tif_file = out_tif_folder_date + "/" + tif_base_name

        if os.path.isfile(output_tif_file):
    #       if we already downloaded the band imagette for this parcel we skip it
            print(" already downloaded ", end="")
        else:
            try:
                r = requests.get(tif_url, auth = (username, password), timeout=180)
                with open(output_tif_file, 'wb') as f:
                    f.write(r.content)
                    
            except requests.exceptions.HTTPError as errh:
                was_error = True
                print ("Http Error:",errh)
            except requests.exceptions.ConnectionError as errc:
                was_error = True
                print ("Error Connecting:",errc)
            except requests.exceptions.Timeout as errt:
                was_error = True
                print ("Timeout Error:",errt)
            except requests.exceptions.RequestException as err:
                was_error = True
                print ("OOps: Something Else",err)
        print("...done")
    return was_error

def merge_bands(parcel_id, crop, out_tif_folder_base):
    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     
    
    out_tif_folder = out_tif_folder_base + "/" + chip_folder
    downloaded_band04_files_pattern = out_tif_folder + "/*/*.B04.tif"
    downloaded_band04_files = glob(downloaded_band04_files_pattern)

    out_merge_folder = out_tif_folder + "_merged"
    if not os.path.exists(out_merge_folder):
        os.makedirs(out_merge_folder)

    for downloaded_band04_file in downloaded_band04_files:
        band04_file_base = os.path.basename(downloaded_band04_file)
        band_file_path = os.path.dirname(downloaded_band04_file)
        tile_name = band04_file_base.split(".")[0] 
        
        #get acquisition date from tile name
        acq_date_full = tile_name.split("_")[2]
        acq_date = acq_date_full[0:4] + "-" + acq_date_full[4:6] + "-" + acq_date_full[6:8]

    #     check if the other bands are also available for this tile
        if os.path.isfile(band_file_path + "/" + tile_name + ".B08.tif") and \
            os.path.isfile(band_file_path + "/" + tile_name + ".B11.tif"):
            #we can merge these bands
            out_merge = out_merge_folder + "/" + tile_name + ".tif"
            print(out_merge)
            if not os.path.isfile(out_merge):
                # e:\MS\ES\Catalunia2019\raster\chips\343130\2019-05-01\B08.tif
                band08 = band_file_path + "/" + tile_name + ".B08.tif"
                band11 = band_file_path + "/" + tile_name + ".B11.tif"
                band04 = band_file_path + "/" + tile_name + ".B04.tif"

                gm.main(['', '-o', out_merge, '-ot', 'Int16', '-separate', band08, band11, band04]) 

def merge_4_bands(parcel_id, crop, out_tif_folder_base):
    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     
    
    out_tif_folder = out_tif_folder_base + "/" + chip_folder
    downloaded_band04_files_pattern = out_tif_folder + "/*/*.B04.tif"
    downloaded_band04_files = glob(downloaded_band04_files_pattern)

    out_merge_folder = out_tif_folder + "_merged_4bands"
    if not os.path.exists(out_merge_folder):
        os.makedirs(out_merge_folder)

    for downloaded_band04_file in downloaded_band04_files:
        band04_file_base = os.path.basename(downloaded_band04_file)
        band_file_path = os.path.dirname(downloaded_band04_file)
        tile_name = band04_file_base.split(".")[0] 
        
        #get acquisition date from tile name
        acq_date_full = tile_name.split("_")[2]
        acq_date = acq_date_full[0:4] + "-" + acq_date_full[4:6] + "-" + acq_date_full[6:8]

    #     check if the other bands are also available for this tile
        if os.path.isfile(band_file_path + "/" + tile_name + ".B02.tif") and \
            os.path.isfile(band_file_path + "/" + tile_name + ".B03.tif") and \
            os.path.isfile(band_file_path + "/" + tile_name + ".B08.tif"):
            #we can merge these bands
            out_merge = out_merge_folder + "/" + tile_name + ".tif"
            print(out_merge)
            if not os.path.isfile(out_merge):
                # e:\MS\ES\Catalunia2019\raster\chips\343130\2019-05-01\B08.tif
                band02 = band_file_path + "/" + tile_name + ".B02.tif"
                band03 = band_file_path + "/" + tile_name + ".B03.tif"
                band04 = band_file_path + "/" + tile_name + ".B04.tif"
                band08 = band_file_path + "/" + tile_name + ".B08.tif"

               

                gm.main(['', '-o', out_merge, '-ot', 'Int16', '-separate', band02, band03, band04, band08]) 
                
def get_acquisition_date_from_tile_name(tile_name):
    #get acquisition date from tile name
    acq_date_full = tile_name.split("_")[2]
    acq_date = acq_date_full[0:4] + "-" + acq_date_full[4:6] + "-" + acq_date_full[6:8]
    return acq_date
    
def get_date_from_string(d):
    dt = datetime.date(int(d.split('-')[0]), int(d.split('-')[1]), int(d.split('-')[2]))
    return dt

def split_date_range(search_window_start_date, search_window_end_date, search_split_days):
    dt_search_window_start_date = get_date_from_string(search_window_start_date)
    dt_search_window_end_date = get_date_from_string(search_window_end_date)

    # split date range between start date and end date by a given number of days so that
    # we can launch the rawChipByLocation query split by month as the max number of chips
    # that it can return is 24 at the moment
    date_ranges = []

    current_start_date = dt_search_window_start_date
    current_end_date = current_start_date + datetime.timedelta(days=search_split_days -1)
    date_ranges.append((str(current_start_date),str(current_end_date) ))

    while (current_end_date < dt_search_window_end_date - datetime.timedelta(days=search_split_days)):
        current_start_date = current_start_date + datetime.timedelta(days=search_split_days)
        current_end_date = current_start_date + datetime.timedelta(days=search_split_days -1)
        date_ranges.append((str(current_start_date),str(current_end_date) ))

    current_start_date = current_start_date + datetime.timedelta(days=search_split_days)
    current_end_date = dt_search_window_end_date
    date_ranges.append((str(current_start_date),str(current_end_date) ))
    return date_ranges
    
def is_tile_cloudy_geopandas(tif_file, parcel, cloud_categories):
    warnings.simplefilter(action='ignore', category=FutureWarning)
    is_cloudy = False
    
    src_image = rasterio.open(tif_file)
    parcel = parcel.to_crs(src_image.crs)
    
    parcel_stats = extract_stats_for_one_parcel_categorical_geopandas_presel(tif_file, parcel)
    keys = [*parcel_stats]
    for key in keys:
        if key in cloud_categories:
            is_cloudy = True   
    return is_cloudy
   
def extract_stats_for_one_parcel_categorical_geopandas_presel(tif_file, parcel):
    warnings.simplefilter(action='ignore', category=UserWarning)
    scl_stats_for_parcel = zonal_stats(parcel,
                     tif_file,
                categorical=True)[0]   
    return scl_stats_for_parcel
    
def get_max_parcel_extent_in_meters(parcel):
    warnings.simplefilter(action='ignore', category=FutureWarning)
    #reproject parcel to EPSG:3857 to make sure we get the extent in meters
    parcel = parcel.to_crs("EPSG:3857")
    parcel_bounds = parcel.bounds
    
#     get min and max coordinates of parcel in map coordinates
    minx = parcel_bounds['minx']
    maxx = parcel_bounds['maxx']
    miny = parcel_bounds['miny']
    maxy = parcel_bounds['maxy']

    x_extent = maxx - minx
    y_extent = maxy - miny
    max_parcel_extent_meters = round(max(x_extent.to_list()[0],y_extent.to_list()[0])/10,0)*10
    
    return max_parcel_extent_meters 

def get_s1_bs_imagettes(raw_chips_s1_batch_url, lon, lat, start_date, end_date, username, password, chipsize):
    
    print("getting S1 images from: " + start_date + " to: " + end_date)
    start_and_end_dates = []
    start_and_end_dates.append(start_date)
    start_and_end_dates.append(end_date)
    was_error = False
    response = None
    list_of_s1_bs_imagettes = {}
    post_dict = {}
    lon_float = round(float(lon),5)
    lat_float = round(float(lat),5)
    
    
    post_dict["lon"] = lon_float
    post_dict["lat"] = lat_float
    post_dict["dates"] = start_and_end_dates

    post_dict["plevel"] = 'CARD-BS' 
    # we keep the same chipsize as in the SCL download, but change it to integer because in the 
    # SCL download request it was string
    post_dict["chipsize"] = int(chipsize)
    try:
        print("trying to get s1 bs images with timeout 180 sec")
        print(post_dict)
        response = requests.post(raw_chips_s1_batch_url, json=post_dict, auth = (username, password), timeout=180)
        print("this is after the request")
        list_of_s1_bs_imagettes = json.loads(response.content)
        print(list_of_s1_bs_imagettes)
    except requests.exceptions.HTTPError as errh:
        was_error = True
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        was_error = True
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        was_error = True
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        was_error = True
        print ("OOps: Something Else",err)    
    
    
    
    return list_of_s1_bs_imagettes, was_error  

def get_s1_coh6_imagettes(raw_chips_s1_batch_url, lon, lat, start_date, end_date, username, password, chipsize):
    
    print("getting S1 COH6 images from: " + start_date + " to: " + end_date)
    start_and_end_dates = []
    start_and_end_dates.append(start_date)
    start_and_end_dates.append(end_date)
    was_error = False
    response = None
    list_of_s1_coh6_imagettes = {}
    post_dict = {}
    lon_float = round(float(lon),5)
    lat_float = round(float(lat),5)
    
    
    post_dict["lon"] = lon_float
    post_dict["lat"] = lat_float
    post_dict["dates"] = start_and_end_dates

    post_dict["plevel"] = 'CARD-COH6' 
    # we keep the same chipsize as in the SCL download, but change it to integer because in the 
    # SCL download request it was string
    post_dict["chipsize"] = int(chipsize)
    try:
        print("trying to get s1 coh6 images with timeout 180 sec")
        print(post_dict)
        response = requests.post(raw_chips_s1_batch_url, json=post_dict, auth = (username, password), timeout=180)
        print("this is after the request")
        
        # check if response.content is a valid json string
        if validate_JSON(response.content):
            list_of_s1_coh6_imagettes = json.loads(response.content)
            print(list_of_s1_coh6_imagettes)
        else:
            print("response.content is not a valid JSON string")
            print("this is response.content")
            print(response.content)
    except requests.exceptions.HTTPError as errh:
        was_error = True
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        was_error = True
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        was_error = True
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        was_error = True
        print ("OOps: Something Else",err)    
    
    
    
    return list_of_s1_coh6_imagettes, was_error     
    
def download_s1_bs_imagettes(url_base, list_of_s1_bs_imagettes, out_s1_bs_folder, username, password):
    # download the band tifs that were generated with the batch chip extract request
    was_error = False
    chips_list = list_of_s1_bs_imagettes['chips']
    date_list = list_of_s1_bs_imagettes['dates']
    # 20200402T055753_VH
    i = 0
    for act_date in date_list:
        acq_date = act_date[0:4] + "-" + act_date[4:6] + "-" + act_date[6:8]
        acq_hour = act_date[9:11]
        acq_hour_int = int(acq_hour)
        
        if acq_hour_int >=0 and acq_hour_int < 12:
            orbit_orientation = "D"
        elif acq_hour_int >=12 and acq_hour_int <=23:
            orbit_orientation = "A"
        else:
            orbit_orientation = "F"
        print(act_date, acq_date, acq_hour, orbit_orientation, chips_list[i])   
        tif_url = url_base + chips_list[i]
        print(tif_url)
        print("Downloading S1 BS image: " + act_date, end="")
       
        if not os.path.exists(out_s1_bs_folder):
            os.makedirs(out_s1_bs_folder)

        output_tif_file = out_s1_bs_folder + "/" + act_date + "_" + orbit_orientation + ".tif"

        if os.path.isfile(output_tif_file):
    #       if we already downloaded the band imagette for this parcel we skip it
            print(" already downloaded ", end="")
        else:
            try:
                r = requests.get(tif_url, auth = (username, password), timeout=180)
                with open(output_tif_file, 'wb') as f:
                    f.write(r.content)
                    
            except requests.exceptions.HTTPError as errh:
                was_error = True
                print ("Http Error:",errh)
            except requests.exceptions.ConnectionError as errc:
                was_error = True
                print ("Error Connecting:",errc)
            except requests.exceptions.Timeout as errt:
                was_error = True
                print ("Timeout Error:",errt)
            except requests.exceptions.RequestException as err:
                was_error = True
                print ("OOps: Something Else",err)
        print("...done")
        i += 1
    return was_error
    
def download_s1_coh6_imagettes(url_base, list_of_s1_coh6_imagettes, out_s1_coh6_folder, username, password):
    # download the band tifs that were generated with the batch chip extract request
    was_error = False
    chips_list = list_of_s1_coh6_imagettes['chips']
    date_list = list_of_s1_coh6_imagettes['dates']
    # 20200402T055753_VH
    i = 0
    for act_date in date_list:
        acq_date = act_date[0:4] + "-" + act_date[4:6] + "-" + act_date[6:8]
        acq_hour = act_date[9:11]
        acq_hour_int = int(acq_hour)
        
        if acq_hour_int >=0 and acq_hour_int < 12:
            orbit_orientation = "D"
        elif acq_hour_int >=12 and acq_hour_int <=23:
            orbit_orientation = "A"
        else:
            orbit_orientation = "F"
        print(act_date, acq_date, acq_hour, orbit_orientation, chips_list[i])   
        tif_url = url_base + chips_list[i]
        print(tif_url)
        print("Downloading S1 COH6 image: " + act_date, end="")
       
        if not os.path.exists(out_s1_coh6_folder):
            os.makedirs(out_s1_coh6_folder)

        output_tif_file = out_s1_coh6_folder + "/" + act_date + "_" + orbit_orientation + ".tif"

        if os.path.isfile(output_tif_file):
    #       if we already downloaded the band imagette for this parcel we skip it
            print(" already downloaded ", end="")
        else:
            try:
                r = requests.get(tif_url, auth = (username, password), timeout=180)
                with open(output_tif_file, 'wb') as f:
                    f.write(r.content)
                    
            except requests.exceptions.HTTPError as errh:
                was_error = True
                print ("Http Error:",errh)
            except requests.exceptions.ConnectionError as errc:
                was_error = True
                print ("Error Connecting:",errc)
            except requests.exceptions.Timeout as errt:
                was_error = True
                print ("Timeout Error:",errt)
            except requests.exceptions.RequestException as err:
                was_error = True
                print ("OOps: Something Else",err)
        print("...done")
        i += 1
    return was_error    
    
def rescale_s1_bs_image(tifFileName, output):
    # rescale raw Sentinel-1 backscatter image from float to uint16 by multiplying it with 10000
    # tifFileName = "e:/chips/be_fl_for_s1_comparison_07/1__/s1_bs/20200402T055753_VH.tif"
    # output = "e:/chips/be_fl_for_s1_comparison_07/1__/s1_bs/20200402T055753_VH_x1000.tif"

    # Register GDAL format drivers and configuration options with a
    # context manager.

    # At the end of the ``with rasterio.Env()`` block, context
    # manager exits and all drivers are de-registered.

    with rasterio.Env():
        with rasterio.open(tifFileName) as src:
            srcx10000 = src.read(1)*10000


            # Write an array as a raster band to a new 8-bit file. For
            # the new file's profile, we start with the profile of the source
            profile = src.profile

        # And then change the band count to 1, set the
        # dtype to uint8, and specify LZW compression.
        profile.update(
            dtype=rasterio.uint16,
            count=1,
            compress='lzw')

        with rasterio.open(output, 'w', **profile) as dst:
            dst.write(srcx10000.astype(rasterio.uint16), 1)
    
def validate_JSON(json_data):
    try:
        json.loads(json_data)
    except ValueError as err:
        return False
    return True