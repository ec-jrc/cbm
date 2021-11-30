#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Csaba Wirnhardt
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

from rasterio.windows import Window
import datetime
import download_utils, batch_utils
import time
import os
from matplotlib import pyplot
import rasterio
import rasterio.mask
from rasterio import plot
from glob import glob
import collections
import textwrap 


def get_year_months_dict(acq_dates):
    acq_dates.sort()
    year_months_dict = {}
    for acq_date in acq_dates:
        year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
        day = int(acq_date.split('-')[2])
        if not year_month in year_months_dict:
            year_months_dict[year_month] = []

        year_months_dict[year_month].append(day)
    return year_months_dict
    
def get_number_of_columns(acq_dates):
    acq_dates.sort()
    year_months = []
    year_months_dict = {}

    for acq_date in acq_dates:
        year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
        day = int(acq_date.split('-')[2])

        if year_month not in year_months:
            year_months.append(year_month)

        if not year_month in year_months_dict:
            year_months_dict[year_month] = []

        year_months_dict[year_month].append(day)

    # now check which year_month has the most days in it
    max_number_of_days = 0
    for key, value in year_months_dict.items():
        if len(value) >= max_number_of_days:
            max_number_of_days = len(value)
#     for key, value in year_months_dict.items():
#         print(key, value)
        
    return max_number_of_days
    
def get_current_col(acq_date,year_months_dict):
    # let's check the position of a given date in the monthly view grid
    act_year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
    act_day = int(acq_date.split('-')[2])
    act_col = year_months_dict[act_year_month].index(act_day) + 1

    return act_col

def get_window(parcel, src_image, buffer_size_meter, pixel_size_meter):
    parcel_bounds = parcel.bounds
    
#     get min and max coordinates of parcel in map coordinates
    minx = parcel_bounds['minx']
    maxx = parcel_bounds['maxx']
    miny = parcel_bounds['miny']
    maxy = parcel_bounds['maxy']
    
# Get pixel coordinates from map coordinates
    pmin_col, pmin_row = src_image.index(minx, maxy)
    pmax_col, pmax_row = src_image.index(maxx, miny)
    
# calculate parcel extent in pixels
    # in the new version of rasterio the src_image.index returns an int not a list
    # so we have to handle this
    if type(pmin_col) == list:
        # it is a list, old style
        # calculate parcel extent in pixels
        y_extent_pixels = pmax_col[0] - pmin_col[0]
        x_extent_pixels = pmax_row[0] - pmin_row[0]

        # translate buffer size around the parcel from meter to pixels
        buffer_size_pixel = int(round(buffer_size_meter / pixel_size_meter,0))

        y_offset_pixels = pmin_col[0] - buffer_size_pixel
        x_offset_pixels = pmin_row[0] - buffer_size_pixel    


    else:
        # it is not a list but integer, new style
        y_extent_pixels = pmax_col - pmin_col
        x_extent_pixels = pmax_row - pmin_row

        # translate buffer size around the parcel from meter to pixels
        buffer_size_pixel = int(round(buffer_size_meter / pixel_size_meter,0))

        y_offset_pixels = pmin_col - buffer_size_pixel
        x_offset_pixels = pmin_row - buffer_size_pixel
        
    win = Window(x_offset_pixels, y_offset_pixels, x_extent_pixels + 2*buffer_size_pixel + 1, y_extent_pixels + 2*buffer_size_pixel + 1)
    return win  

def get_current_list_of_textsts(first_year_month, number_of_year_months):
    textstrs_tuples = [
                       ("201701", "2017 JAN"),
                       ("201702", "2017 FEB"),
                       ("201703", "2017 MAR"),
                       ("201704", "2017 APR"),
                       ("201705", "2017 MAY"),
                       ("201706", "2017 JUN"),
                       ("201707", "2017 JUL"),
                       ("201708", "2017 AUG"),
                       ("201709", "2017 SEP"),
                       ("201710", "2017 OCT"),
                       ("201711", "2017 NOV"),
                       ("201712", "2017 DEC"),
                       ("201801", "2018 JAN"),
                       ("201802", "2018 FEB"),
                       ("201803", "2018 MAR"),
                       ("201804", "2018 APR"),
                       ("201805", "2018 MAY"),
                       ("201806", "2018 JUN"),
                       ("201807", "2018 JUL"),
                       ("201808", "2018 AUG"),
                       ("201809", "2018 SEP"),
                       ("201810", "2018 OCT"),
                       ("201811", "2018 NOV"),
                       ("201812", "2018 DEC"),
                       ("201901", "2019 JAN"),
                       ("201902", "2019 FEB"),
                       ("201903", "2019 MAR"),
                       ("201904", "2019 APR"),
                       ("201905", "2019 MAY"),
                       ("201906", "2019 JUN"),
                       ("201907", "2019 JUL"),
                       ("201908", "2019 AUG"),
                       ("201909", "2019 SEP"),
                       ("201910", "2019 OCT"),
                       ("201911", "2019 NOV"),
                       ("201912", "2019 DEC"),
                       ("202001", "2020 JAN"),
                       ("202002", "2020 FEB"),
                       ("202003", "2020 MAR"),
                       ("202004", "2020 APR"),
                       ("202005", "2020 MAY"),
                       ("202006", "2020 JUN"),
                       ("202007", "2020 JUL"),
                       ("202008", "2020 AUG"),
                       ("202009", "2020 SEP"),
                       ("202010", "2020 OCT"),
                       ("202011", "2020 NOV"),
                       ("202012", "2020 DEC"),
                       ("202101", "2021 JAN"),
                       ("202102", "2021 FEB"),
                       ("202103", "2021 MAR"),
                       ("202104", "2021 APR"),
                       ("202105", "2021 MAY"),
                       ("202106", "2021 JUN"),
                       ("202107", "2021 JUL"),
                       ("202108", "2021 AUG"),
                       ("202109", "2021 SEP"),
                       ("202110", "2021 OCT"),
                       ("202111", "2021 NOV"),
                       ("202112", "2021 DEC"),
                      ]

    # find the index of the first occurrence of first_year_month in textstrs_tuples
    # and return the rest secend elements of the tuples of the list

    i = 0
    first_year_month_index = i
    for textstrs_tuple in textstrs_tuples:
        if first_year_month == textstrs_tuple[0]:
            first_year_month_index = i
        i+=1

    current_textstrs = []
    for i in range(first_year_month_index, first_year_month_index + number_of_year_months):
        current_textstrs.append(textstrs_tuples[i][1])

    return current_textstrs
    
def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

def get_date_from_string(d):
    dt = datetime.date(int(d.split('-')[0]), int(d.split('-')[1]), int(d.split('-')[2]))
    return dt
    
def get_number_of_rows(acq_dates):
    acq_dates.sort()
    dt_acq_dates = []
    for acq_date in acq_dates:
        dt_acq_date = get_date_from_string(acq_date)
        dt_acq_dates.append(dt_acq_date)

    #we need rows for the months where there is no acquisition at all
    #so we take the lowest and highest acquisition datee and calculate the difference in months
    #this will be the number of rows needed for the imagettes in the monthly view
    number_of_year_months = diff_month(max(dt_acq_dates), min(dt_acq_dates)) + 1
     
    return number_of_year_months
    
def get_current_row(curr_acq_date, acq_dates):
    acq_dates.sort()
    dt_acq_dates = []
    for acq_date in acq_dates:
        dt_acq_date = get_date_from_string(acq_date)
        dt_acq_dates.append(dt_acq_date)
    dt_curr_acq_date = get_date_from_string(curr_acq_date)
    curr_row = diff_month(dt_curr_acq_date, min(dt_acq_dates)) + 1
     
    return curr_row
    
def get_year_months_dict_for_weekly(tiles_to_download):
    year_month_dict = {}
    for tile_name in tiles_to_download:
        # let's go through the dates and make year_month from them
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
 
        # if we do not have a key for year_month yet we add one empty
        if not year_month in year_month_dict:
            year_month_dict[year_month] = {}
        day = int(acq_date.split('-')[2])
        
        # then we check the current date to see which week or half-week it falls into
        # and if there is no key in that sub-directory we add it to that
        if day >= 1 and day <= 7:
            if not 1 in year_month_dict[year_month]:
                year_month_dict[year_month][1] = acq_date
        elif day >= 8 and day <= 15:
            if not 2 in year_month_dict[year_month]:
                year_month_dict[year_month][2] = acq_date
        elif day >= 16 and day <= 23:
            if not 3 in year_month_dict[year_month]:
                year_month_dict[year_month][3] = acq_date
        elif day >= 24 and day <= 31:
            if not 4 in year_month_dict[year_month]:
                year_month_dict[year_month][4] = acq_date

    return year_month_dict

def get_weekly_column(acq_date, year_months_dict_weekly):
    # now check the position of a given date in the year_month/weeks nested dictionary
    weekly_column = 0 
    year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
    
    year_month_dict_current = year_months_dict_weekly[year_month]
    if acq_date in year_month_dict_current.values():
        weekly_column = list(year_month_dict_current.keys())[list(year_month_dict_current.values()).index(acq_date)]

    return weekly_column

def get_year_months_dict_for_half_weekly(tiles_to_download):
    year_month_dict = {}
    for tile_name in tiles_to_download:
        # let's go through the dates and make year_month from them
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
 
        # if we do not have a key for year_month yet we add one empty
        if not year_month in year_month_dict:
            year_month_dict[year_month] = {}
        day = int(acq_date.split('-')[2])
        
        # then we check the current date to see which week or half-week it falls into
        # and if there is no key in that sub-directory we add it to that
        if day >= 1 and day <= 3:
            if not 1 in year_month_dict[year_month]:
                year_month_dict[year_month][1] = acq_date
        elif day >= 4 and day <= 7:
            if not 2 in year_month_dict[year_month]:
                year_month_dict[year_month][2] = acq_date
        elif day >= 8 and day <= 11:
            if not 3 in year_month_dict[year_month]:
                year_month_dict[year_month][3] = acq_date
        elif day >= 12 and day <= 15:
            if not 4 in year_month_dict[year_month]:
                year_month_dict[year_month][4] = acq_date
        elif day >= 16 and day <= 19:
            if not 5 in year_month_dict[year_month]:
                year_month_dict[year_month][5] = acq_date
        elif day >= 20 and day <= 23:
            if not 6 in year_month_dict[year_month]:
                year_month_dict[year_month][6] = acq_date
        elif day >= 24 and day <= 27:
            if not 7 in year_month_dict[year_month]:
                year_month_dict[year_month][7] = acq_date
        elif day >= 28 and day <= 31:
            if not 8 in year_month_dict[year_month]:
                year_month_dict[year_month][8] = acq_date
    
    return year_month_dict
    
def get_half_weekly_column(acq_date, year_months_dict_half_weekly):
    # now check the position of a given date in the year_month/weeks nested dictionary
    half_weekly_column = 0 
    year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
    year_month_dict_current = year_months_dict_half_weekly[year_month]
    if acq_date in year_month_dict_current.values():
        half_weekly_column = list(year_month_dict_current.keys())[list(year_month_dict_current.values()).index(acq_date)]

    return half_weekly_column
    
def get_parcel_extent_ratio(parcel, buffer_size_meter):
    parcel = parcel.to_crs("EPSG:3857")
    parcel_bounds = parcel.bounds
    
#     get min and max coordinates of parcel in map coordinates
    minx = parcel_bounds['minx']
    maxx = parcel_bounds['maxx']
    miny = parcel_bounds['miny']
    maxy = parcel_bounds['maxy']
    
    x_extent_np = round(maxx - minx,0)
    y_extent_np = round(maxy - miny,0)
    
    x_extent = int(x_extent_np.item())
    y_extent = int(y_extent_np.item())
    # print("x_extent=",x_extent, " y_extent=", y_extent)

    x_extent_with_buffer = x_extent + 2*buffer_size_meter
    y_extent_with_buffer = y_extent + 2*buffer_size_meter

    y_per_x_extent = y_extent_with_buffer / x_extent_with_buffer
    return y_per_x_extent
    
def calendar_view_half_weekly_more_param(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, 
                                            parcel_id_column, buffer_size_meter, vector_color, logfile, jpg_resolution, acq_dates, merged_lut_files):   
    ###############################################################
    # calendar_view_visualization half weekly display
    ############################################################### 
    fout = open(logfile, 'a')
    start = time.time()

    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     
    
    output_jpg_folder = out_tif_folder_base + "/overview_jpg_half_weekly"
    pixel_size_meter = 10


    if not os.path.exists(output_jpg_folder):
        os.makedirs(output_jpg_folder)

    year_months_dict = get_year_months_dict(acq_dates)
    # year_months_dict_half_weekly = get_year_months_dict_for_half_weekly(tiles_to_download)
    # we can avoid using tiles_to_download
    year_months_dict_half_weekly = get_year_months_dict_for_half_weekly_from_acq_dates(acq_dates)    
    
    
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = get_number_of_rows(acq_dates)
    num_rows = number_of_year_months + 1
    num_cols = 9
    textstrs = get_current_list_of_textsts(str(first_year_month), number_of_year_months)
    parcel_extent_ratio = get_parcel_extent_ratio(parcel, buffer_size_meter)
    fig_size_x = 16
    fig_size_y = fig_size_x * (number_of_year_months / (num_cols-1)) * parcel_extent_ratio
    print("parcel extent ratio= ", parcel_extent_ratio) 

    fig, a = pyplot.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    vector_filename_base = os.path.basename(vector_file_name)
      
    # if crop name is too long wrap it to more lines
    # Wrap this text. 
    wrapper = textwrap.TextWrapper(width=20) 
    word_list = wrapper.wrap(text=crop) 
    
    info_text = vector_filename_base + "\n" + parcel_id_column + "=" + str(parcel_id) + "\n"
    
    # Print each line. 
    for element in word_list: 
        info_text += element + "\n"

    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=8,
                    verticalalignment='center', horizontalalignment='center', wrap=True)

    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        act_col = get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = get_current_row(acq_date, acq_dates)
        
        if act_col > 0:
            src_image = rasterio.open(merged_lut_file)
            parcel = parcel.to_crs(src_image.crs)
            win = get_window(parcel, src_image, buffer_size_meter, pixel_size_meter)
            
#            if win.col_off >= src_image.width or win.row_off >= src_image.height:
            if win.col_off >= src_image.width \
                or win.row_off >= src_image.height \
                or win.col_off < 0 \
                or win.row_off < 0:
                print("Image does not intersect with the parcel")
            else:
                toPlot = src_image.read(window=win)  
                a[act_row][act_col].set_title(acq_date, verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})
                rasterio.plot.show(toPlot, ax=a[act_row][act_col], transform=src_image.window_transform(win)) 
                parcel.plot(ax=a[act_row][act_col], facecolor='none', edgecolor=vector_color) 

    output_jpg_file = output_jpg_folder + "/" + chip_folder + "_buff" + str(buffer_size_meter) + "m_" + vector_color + ".jpg"
    fig.savefig(output_jpg_file, dpi=jpg_resolution, bbox_inches='tight')  
    pyplot.close(fig)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tplot_utils.calendar_view_half_weekly_more_param:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Calendar view: {time.time() - start} seconds")
    return fig, a
    
def calendar_view_half_weekly_more_param_dynamic(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, 
                                            parcel_id_column, buffer_size_meter, vector_color, logfile, jpg_resolution, acq_dates, merged_lut_files):   
    ###############################################################
    # calendar_view_visualization half weekly display
    ############################################################### 
    fout = open(logfile, 'a')
    start = time.time()

    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     

    output_jpg_folder = out_tif_folder_base + "/overview_jpg_half_weekly_dyn"
    pixel_size_meter = 10

    if not os.path.exists(output_jpg_folder):
        os.makedirs(output_jpg_folder)

    year_months_dict = get_year_months_dict(acq_dates)
    year_months_dict_half_weekly = get_year_months_dict_for_half_weekly(tiles_to_download)
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = get_number_of_rows(acq_dates)
    num_rows = number_of_year_months + 1
    num_cols = 9
    textstrs = get_current_list_of_textsts(str(first_year_month), number_of_year_months)
    parcel_extent_ratio = get_parcel_extent_ratio(parcel, buffer_size_meter)
    fig_size_x = 16
    fig_size_y = fig_size_x * (number_of_year_months / (num_cols-1)) * parcel_extent_ratio
    print("parcel extent ratio= ", parcel_extent_ratio) 

    fig, a = pyplot.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    vector_filename_base = os.path.basename(vector_file_name)
    info_text = vector_filename_base + "\n" + parcel_id_column + "=" + str(parcel_id) + "\n" + crop
    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=10,
                    verticalalignment='center', horizontalalignment='center')
        
    for merged_lut_file in merged_lut_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        act_col = get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = get_current_row(acq_date, acq_dates)
        
        if act_col > 0:
            src_image = rasterio.open(merged_lut_file)
            parcel = parcel.to_crs(src_image.crs)
            win = get_window(parcel, src_image, buffer_size_meter, pixel_size_meter)
            toPlot = src_image.read(window=win)  
            a[act_row][act_col].set_title(acq_date, verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})
            rasterio.plot.show(toPlot, ax=a[act_row][act_col], transform=src_image.window_transform(win)) 
            parcel.plot(ax=a[act_row][act_col], facecolor='none', edgecolor=vector_color) 

    output_jpg_file = output_jpg_folder + "/" + chip_folder + "_buff" + str(buffer_size_meter) + "m_" + vector_color + ".jpg"
    fig.savefig(output_jpg_file, dpi=jpg_resolution, bbox_inches='tight')  
    pyplot.close(fig)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tplot_utils.calendar_view_half_weekly_more_param:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Calendar view: {time.time() - start} seconds")
    return fig, a    

def calendar_view_half_weekly_more_param_ndvi(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, 
                                            parcel_id_column, buffer_size_meter, vector_color, logfile, jpg_resolution, acq_dates, merged_ndvi_files):   
    ###############################################################
    # calendar_view_visualization half weekly display
    ############################################################### 
    fout = open(logfile, 'a')
    start = time.time()

    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     
    
    output_jpg_folder = out_tif_folder_base + "/overview_jpg_half_weekly_ndvi"
    pixel_size_meter = 10

    if not os.path.exists(output_jpg_folder):
        os.makedirs(output_jpg_folder)

    year_months_dict = get_year_months_dict(acq_dates)
    year_months_dict_half_weekly = get_year_months_dict_for_half_weekly(tiles_to_download)
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = get_number_of_rows(acq_dates)
    num_rows = number_of_year_months + 1
    num_cols = 9
    textstrs = get_current_list_of_textsts(str(first_year_month), number_of_year_months)
    parcel_extent_ratio = get_parcel_extent_ratio(parcel, buffer_size_meter)
    fig_size_x = 16
    fig_size_y = fig_size_x * (number_of_year_months / (num_cols-1)) * parcel_extent_ratio
    print("parcel extent ratio= ", parcel_extent_ratio) 

    fig, a = pyplot.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    vector_filename_base = os.path.basename(vector_file_name)
    info_text = vector_filename_base + "\n" + parcel_id_column + "=" + str(parcel_id) + "\n" + crop
    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=10,
                    verticalalignment='center', horizontalalignment='center')

    for merged_lut_file in merged_ndvi_files:
        merged_lut_file_base = os.path.basename(merged_lut_file)
        merged_lut_file_path = os.path.dirname(merged_lut_file)
        tile_name = merged_lut_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        act_col = get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = get_current_row(acq_date, acq_dates)
        
        if act_col > 0:
            src_image = rasterio.open(merged_lut_file)
            parcel = parcel.to_crs(src_image.crs)
            win = get_window(parcel, src_image, buffer_size_meter, pixel_size_meter)
            toPlot = src_image.read(window=win)  
            a[act_row][act_col].set_title(acq_date, verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})

            rasterio.plot.show(toPlot, ax=a[act_row][act_col], transform=src_image.window_transform(win), 
                                         cmap='RdYlGn',
                                         vmin=0, 
                                         vmax=1)

            
            parcel.plot(ax=a[act_row][act_col], facecolor='none', edgecolor=vector_color) 

    output_jpg_file = output_jpg_folder + "/" + chip_folder + "_buff" + str(buffer_size_meter) + "m_" + vector_color + ".jpg"
    fig.savefig(output_jpg_file, dpi=jpg_resolution, bbox_inches='tight')  
    pyplot.close(fig)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tplot_utils.calendar_view_half_weekly_more_param:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Calendar view: {time.time() - start} seconds")
    return fig, a

def plot_histogram_for_one_parcel(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, 
                                            parcel_id_column, logfile, jpg_resolution):   
   
    
    
    fout = open(logfile, 'a')
    start = time.time()
    cmap = pyplot.get_cmap('RdYlGn')
    
    acq_dates, merged_ndvi_files = batch_utils.get_merged_ndvi_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base)   

    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     

    output_hist_folder = out_tif_folder_base + "/overview_hist_half_weekly"

    if not os.path.exists(output_hist_folder):
        os.makedirs(output_hist_folder)
        
    output_hist_file = output_hist_folder + "/" + chip_folder  + ".jpg"
    if os.path.isfile(output_hist_file):
        print("histogram overview already created:" + output_hist_file)
        return

    year_months_dict = get_year_months_dict(acq_dates)
    year_months_dict_half_weekly = get_year_months_dict_for_half_weekly(tiles_to_download)
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = get_number_of_rows(acq_dates)
    num_rows = number_of_year_months + 1
    num_cols = 9
    textstrs = get_current_list_of_textsts(str(first_year_month), number_of_year_months)

    fig_size_x = 16
    fig_size_y = fig_size_x * (num_rows / num_cols)

    fig, a = pyplot.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()
            
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    vector_filename_base = os.path.basename(vector_file_name)
    info_text = vector_filename_base + "\n" + parcel_id_column + "=" + str(parcel_id) + "\n" + crop
    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=10,
                    verticalalignment='center', horizontalalignment='center')
        
    for merged_ndvi_file in merged_ndvi_files:
        merged_ndvi_file_base = os.path.basename(merged_ndvi_file)
        merged_ndvi_file_path = os.path.dirname(merged_ndvi_file)
        tile_name = merged_ndvi_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        act_col = get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = get_current_row(acq_date, acq_dates)
        
        if act_col > 0:
            with rasterio.open(merged_ndvi_file) as src_image:
            
                src_image = rasterio.open(merged_ndvi_file)
                parcel = parcel.to_crs(src_image.crs)
                a[act_row][act_col].set_title(acq_date, verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})
                a[act_row][act_col].set_axis_on()
                data, transform = rasterio.mask.mask(src_image, parcel.geometry, crop=True)
                nbins = 99
                N, bins, patches = a[act_row][act_col].hist(data[0,:,:], nbins, range=[0.01, 1.0])
                for p in patches:
                    for i in range(len(p)):
                        p[i].set_color(cmap(float(i)/nbins))        

    pyplot.tight_layout()        
    fig.savefig(output_hist_file, dpi=jpg_resolution)  
    pyplot.close(fig)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tplot_utils.plot_histogram_for_one_parcel:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Histogram view: {time.time() - start} seconds")
    return fig, a
    
def plot_scatter_for_one_parcel_fixed_scale_cumulative(parcel_id, crop, out_tif_folder_base, tiles_to_download, parcel, vector_file_name, 
                                            parcel_id_column, logfile, jpg_resolution):   
    
    fout = open(logfile, 'a')
    start = time.time()
    
    acq_dates, merged_tif_files = batch_utils.get_merged_tif_files_and_acquisition_dates(parcel_id, crop, out_tif_folder_base)   

    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     

    output_scatter_folder = out_tif_folder_base + "/overview_scatter_half_weekly_fixed_scale_cumulative"

    if not os.path.exists(output_scatter_folder):
        os.makedirs(output_scatter_folder)
        
    output_scatter_file = output_scatter_folder + "/" + chip_folder  + ".jpg"
    if os.path.isfile(output_scatter_file):
        print("scatterplot overview already created:" + output_scatter_file)
        return

    year_months_dict = get_year_months_dict(acq_dates)
    year_months_dict_half_weekly = get_year_months_dict_for_half_weekly(tiles_to_download)
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = get_number_of_rows(acq_dates)
    num_rows = number_of_year_months + 1
    num_cols = 9
    textstrs = get_current_list_of_textsts(str(first_year_month), number_of_year_months)

    fig_size_x = 16
    fig_size_y = fig_size_x * (num_rows / num_cols)

    fig, a = pyplot.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()
            
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    vector_filename_base = os.path.basename(vector_file_name)
    info_text = vector_filename_base + "\n" + parcel_id_column + "=" + str(parcel_id) + "\n" + crop
    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=10,
                    verticalalignment='center', horizontalalignment='center')
        
    acquisition_dates_and_merged_tif_files_dict = batch_utils.get_merged_tif_files_and_acquisition_dates_in_dict(parcel_id, crop, out_tif_folder_base)
    
    date_index = 0
    red = []
    nir = []

    for acq_date, merged_tif_file in acquisition_dates_and_merged_tif_files_dict.items():
        # acquisition dates here are already sorted so we can go through them and create the cumulative scatter plots
        # of bands
  
        merged_tif_file_base = os.path.basename(merged_tif_file)
        merged_tif_file_path = os.path.dirname(merged_tif_file)
        tile_name = merged_tif_file_base.split(".")[0]
        
        act_col = get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = get_current_row(acq_date, acq_dates)
        
        if act_col > 0:
            with rasterio.open(merged_tif_file) as src_image:
            
                src_image = rasterio.open(merged_tif_file)
                parcel = parcel.to_crs(src_image.crs)
                a[act_row][act_col].set_title(acq_date, verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})
                a[act_row][act_col].set_axis_on()
                src_image_masked, transform = rasterio.mask.mask(src_image, parcel.geometry, crop=True)
                               
                red.append(src_image_masked[0,:])
                nir.append(src_image_masked[2,:])
                
                if date_index == 0:
                    # for the first date we display only that date with red
                    a[act_row][act_col].scatter(nir[date_index],red[date_index], marker = "x", s = 1, c="red")
                else:
                    # for the other dates we display all the old dates with blue and the current date with red
                    for old_date_index in range (0,date_index):
                        a[act_row][act_col].scatter(nir[old_date_index],red[old_date_index], marker = "x", s=1,c="blue")
                    a[act_row][act_col].scatter(nir[date_index],red[date_index], marker = "x", s=1,c="red")
                 
                xmin = 1
                ymin = 1
                xmax = 6000
                ymax = 6000
                
                a[act_row][act_col].set(xlim=(xmin, xmax), ylim=(ymin, ymax))
            date_index += 1 

    pyplot.tight_layout()        
    fig.savefig(output_scatter_file, dpi=jpg_resolution)  
    pyplot.close(fig)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tplot_utils.plot_scatter_for_one_parcel_fixed_scale_cumulative:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Cumulative scatter plot: {time.time() - start} seconds")
    return fig, a
    
def get_acquisition_date_from_s1_bs_filename(s1_bs_filename):    
    acq_date = s1_bs_filename[0:4] + "-" + s1_bs_filename[4:6] + "-" + s1_bs_filename[6:8]
    return acq_date
    
def get_acquisition_dates_and_s1_bs_lut_files_dict(out_s1_bs_folder_rescale_lut, polarisation = "VV", orbit_orientation ="D"):

    s1_bs_lut_files_pattern = out_s1_bs_folder_rescale_lut + "/*" + polarisation + "_" + orbit_orientation + ".tif"
    s1_bs_lut_files = glob(s1_bs_lut_files_pattern)

    acq_dates_tif_files_dict = {}

    for s1_bs_lut_file in s1_bs_lut_files:
        s1_bs_lut_file_base = os.path.basename(s1_bs_lut_file)
        s1_bs_lut_file_path = os.path.dirname(s1_bs_lut_file)
        s1_bs_filename = s1_bs_lut_file_base.split(".")[0]
        acq_date = get_acquisition_date_from_s1_bs_filename(s1_bs_filename)
        acq_dates_tif_files_dict[acq_date]=s1_bs_lut_file
    return collections.OrderedDict(sorted(acq_dates_tif_files_dict.items()))   

def get_acquisition_dates_and_s1_bs_files_dict(out_s1_bs_folder, polarisation = "VV", orbit_orientation ="D"):

    s1_bs_files_pattern = out_s1_bs_folder + "/*" + polarisation + "_" + orbit_orientation + ".tif"
    s1_bs_files = glob(s1_bs_files_pattern)

    acq_dates_tif_files_dict = {}

    for s1_bs_file in s1_bs_files:
        s1_bs_file_base = os.path.basename(s1_bs_file)
        s1_bs_file_path = os.path.dirname(s1_bs_file)
        s1_bs_filename = s1_bs_file_base.split(".")[0]
        acq_date = get_acquisition_date_from_s1_bs_filename(s1_bs_filename)
        acq_dates_tif_files_dict[acq_date]=s1_bs_file
    return collections.OrderedDict(sorted(acq_dates_tif_files_dict.items()))   

def get_image_files(image_folder, logfile):
    fout = open(logfile, 'a')
    start = time.time()
    
    image_files_pattern = image_folder + "/*.tif"
    image_files = glob(image_files_pattern)
    acq_dates_image_files_dict = {}
    
    for image_file in image_files:
        image_file_base = os.path.basename(image_file)
        image_file_path = os.path.dirname(image_file)
        tile_name = image_file_base.split(".")[0]
        acq_date = download_utils.get_acquisition_date_from_tile_name(tile_name)
        acq_dates_image_files_dict[acq_date]=image_file
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t\t\tget_image_files:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return collections.OrderedDict(sorted(acq_dates_image_files_dict.items()))  
    
def get_year_months_dict_for_half_weekly_from_acq_dates(acq_dates):
    year_month_dict = {}
    for acq_date in acq_dates:
        # let's go throught the dates and make year_month from them
        year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])

 
        # if we do not have a key for year_month yet we add one empty
        if not year_month in year_month_dict:
            year_month_dict[year_month] = {}
        day = int(acq_date.split('-')[2])
        
        # then we check the current date to see which week or half-week it falls into
        # and if there is no key in that sub-directory we add it to that
        if day >= 1 and day <= 3:
            if not 1 in year_month_dict[year_month]:
                year_month_dict[year_month][1] = acq_date
        elif day >= 4 and day <= 7:
            if not 2 in year_month_dict[year_month]:
                year_month_dict[year_month][2] = acq_date
        elif day >= 8 and day <= 11:
            if not 3 in year_month_dict[year_month]:
                year_month_dict[year_month][3] = acq_date
        elif day >= 12 and day <= 15:
            if not 4 in year_month_dict[year_month]:
                year_month_dict[year_month][4] = acq_date
        elif day >= 16 and day <= 19:
            if not 5 in year_month_dict[year_month]:
                year_month_dict[year_month][5] = acq_date
        elif day >= 20 and day <= 23:
            if not 6 in year_month_dict[year_month]:
                year_month_dict[year_month][6] = acq_date
        elif day >= 24 and day <= 27:
            if not 7 in year_month_dict[year_month]:
                year_month_dict[year_month][7] = acq_date
        elif day >= 28 and day <= 31:
            if not 8 in year_month_dict[year_month]:
                year_month_dict[year_month][8] = acq_date
    
    return year_month_dict
    
def calendar_view_s1_bs_imagettes(parcel_id, crop, out_s1_bs_folder_rescale_lut, parcel, vector_file_name, 
                                            parcel_id_column, buffer_size_meter, vector_color, logfile, jpg_resolution, output_s1_bs_calendar_view_folder, polarisation, orbit_orientation):   
    ###############################################################
    # calendar_view_visualization half weekly display
    ############################################################### 
    fout = open(logfile, 'a')
    start = time.time()
    # polarisation = "VV"
    acquisition_dates_and_s1_bs_lut_files_dict = get_acquisition_dates_and_s1_bs_lut_files_dict(out_s1_bs_folder_rescale_lut, polarisation, orbit_orientation)
    
    acq_dates = list(acquisition_dates_and_s1_bs_lut_files_dict.keys())
    
    if len(acq_dates)==0:
        return

    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     

    pixel_size_meter = 10

    if not os.path.exists(output_s1_bs_calendar_view_folder):
        os.makedirs(output_s1_bs_calendar_view_folder)

    year_months_dict = get_year_months_dict(acq_dates)
    year_months_dict_half_weekly = get_year_months_dict_for_half_weekly_from_acq_dates(acq_dates)
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = get_number_of_rows(acq_dates)
    num_rows = number_of_year_months + 1
    num_cols = 9
    textstrs = get_current_list_of_textsts(str(first_year_month), number_of_year_months)
    parcel_extent_ratio = get_parcel_extent_ratio(parcel, buffer_size_meter)
    fig_size_x = 16
    fig_size_y = fig_size_x * (number_of_year_months / (num_cols-1)) * parcel_extent_ratio
    print("parcel extent ratio= ", parcel_extent_ratio) 

    fig, a = pyplot.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    vector_filename_base = os.path.basename(vector_file_name)
    info_text = vector_filename_base + "\n" + parcel_id_column + "=" + str(parcel_id) + "\n" + crop
    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=10,
                    verticalalignment='center', horizontalalignment='center')
        
    for acq_date, s1_bs_lut_file in acquisition_dates_and_s1_bs_lut_files_dict.items():    
        act_col = get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = get_current_row(acq_date, acq_dates)
        
        if act_col > 0:
            src_image = rasterio.open(s1_bs_lut_file)
            parcel = parcel.to_crs(src_image.crs)
            win = get_window(parcel, src_image, buffer_size_meter, pixel_size_meter)
            #print(win)
            toPlot = src_image.read(window=win)    
            a[act_row][act_col].set_title(acq_date, verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})
            print(s1_bs_lut_file)
            rasterio.plot.show(toPlot, ax=a[act_row][act_col], transform=src_image.window_transform(win), cmap='Greys_r', interpolation='none') 
            parcel.plot(ax=a[act_row][act_col], facecolor='none', edgecolor=vector_color) 


    output_jpg_file = output_s1_bs_calendar_view_folder + "/" + chip_folder + "_buff" + str(buffer_size_meter) + "m_" + vector_color + "_" + polarisation + "_" + orbit_orientation + ".jpg"
    fig.savefig(output_jpg_file, dpi=jpg_resolution, bbox_inches='tight')  
    pyplot.close(fig)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tplot_utils.calendar_view_s1_bs_imagettes:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Calendar view: {time.time() - start} seconds")
    return fig, a


def calendar_view_half_weekly_more_param_index(parcel_id, crop, out_tif_folder_base, 
                                                 parcel, vector_file_name, 
                                                 buffer_size_meter, vector_color, logfile, jpg_resolution, index_name):   
    ###############################################################
    # calendar_view_visualization half weekly display
    ############################################################### 
    fout = open(logfile, 'a')
    start = time.time()
    
    
    acquisition_dates_and_index_files_dict = batch_utils.get_index_files_and_acquisition_dates_in_dict(parcel_id, crop, out_tif_folder_base, index_name)  
    acq_dates = list(acquisition_dates_and_index_files_dict.keys())
    # print(acq_dates)

    # convert parcel_id to a string that can be used as filename           
    parcel_id_as_filename = batch_utils.convert_string_to_filename(parcel_id)
    chip_folder = str(parcel_id_as_filename) + '_' + crop     

    output_jpg_folder = out_tif_folder_base + "/overview_jpg_half_weekly_" + index_name
    pixel_size_meter = 10

    if not os.path.exists(output_jpg_folder):
        os.makedirs(output_jpg_folder)
        
    year_months_dict = get_year_months_dict(acq_dates)        
    year_months_dict_half_weekly = get_year_months_dict_for_half_weekly_from_acq_dates(acq_dates)    
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = get_number_of_rows(acq_dates)
    num_rows = number_of_year_months + 1
    num_cols = 9
    textstrs = get_current_list_of_textsts(str(first_year_month), number_of_year_months)
    parcel_extent_ratio = get_parcel_extent_ratio(parcel, buffer_size_meter)
    fig_size_x = 16
    fig_size_y = fig_size_x * (number_of_year_months / (num_cols-1)) * parcel_extent_ratio
    print("parcel extent ratio= ", parcel_extent_ratio) 

    fig, a = pyplot.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    vector_filename_base = os.path.basename(vector_file_name)
    info_text = vector_filename_base + "\n" + str(parcel_id) + "\n" + crop
    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=10,
                    verticalalignment='center', horizontalalignment='center')

    for acq_date, index_file in acquisition_dates_and_index_files_dict.items():    
        act_col = get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = get_current_row(acq_date, acq_dates)
        
        if act_col > 0:
            src_image = rasterio.open(index_file)
            parcel = parcel.to_crs(src_image.crs)
            win = get_window(parcel, src_image, buffer_size_meter, pixel_size_meter)
            toPlot = src_image.read(window=win)  
            a[act_row][act_col].set_title(acq_date, verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})

            rasterio.plot.show(toPlot, ax=a[act_row][act_col], transform=src_image.window_transform(win), 
                                         cmap='RdYlGn_r',
                                         vmin=-1, 
                                         vmax=0.3)

            
            parcel.plot(ax=a[act_row][act_col], facecolor='none', edgecolor=vector_color) 

    output_jpg_file = output_jpg_folder + "/" + chip_folder + "_buff" + str(buffer_size_meter) + "m_" + vector_color + ".jpg"
    fig.savefig(output_jpg_file, dpi=jpg_resolution, bbox_inches='tight')  
    pyplot.close(fig)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tplot_utils.calendar_view_half_weekly_more_param_index:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Calendar view: {time.time() - start} seconds")
    return fig, a

def calendar_view_half_weekly_generic(image_files, parcel, buffer_size_meter, output_jpg_file, 
                                      vector_color, jpg_resolution, 
                                      calendar_view_start_date,  calendar_view_end_date, logfile):
    ###############################################################
    # calendar_view_visualization half weekly display
    ############################################################### 
    fout = open(logfile, 'a')
    start = time.time()
    pixel_size_meter = 10

    #Let's filter acquisition dates between calendar_view_start_date and calendar_view_end_date
    #plus add these two dates if they are not there so that we stretch the display between
    #theese two dates (even if there are no acquisition) - this will standardize 
    #the display vetical extent
    calendar_view_start_date_date = datetime.datetime.strptime(calendar_view_start_date, '%Y-%m-%d').date()
    calendar_view_end_date_date = datetime.datetime.strptime(calendar_view_end_date, '%Y-%m-%d').date()
    image_files_filtered = {}
    for key, value in image_files.items():
        current_acq_date = datetime.datetime.strptime(key, '%Y-%m-%d').date()
        if  current_acq_date >= calendar_view_start_date_date and \
            current_acq_date <= calendar_view_end_date_date:
            image_files_filtered[key] = value
    acq_dates = [*image_files_filtered] 
    if calendar_view_start_date not in acq_dates:
        acq_dates.append(calendar_view_start_date)
        
    if calendar_view_end_date not in acq_dates:
        acq_dates.append(calendar_view_end_date)    
        
    acq_dates.sort()    
    
    year_months_dict = get_year_months_dict(acq_dates)
    year_months_dict_half_weekly = get_year_months_dict_for_half_weekly_from_acq_dates(acq_dates)    
    
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = get_number_of_rows(acq_dates)
    num_rows = number_of_year_months + 1
    num_cols = 9
    textstrs = get_current_list_of_textsts(str(first_year_month), number_of_year_months)
    parcel_extent_ratio = get_parcel_extent_ratio(parcel, buffer_size_meter)
    fig_size_x = 16
    fig_size_y = fig_size_x * (number_of_year_months / (num_cols-1)) * parcel_extent_ratio
    fig, a = pyplot.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1

    for acq_date, image_file in image_files_filtered.items():  
        act_col = get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = get_current_row(acq_date, acq_dates)
        
        print(acq_date, act_col, act_row, image_file)
        
        if act_col > 0:
            src_image = rasterio.open(image_file)
            parcel = parcel.to_crs(src_image.crs)
            win = get_window(parcel, src_image, buffer_size_meter, pixel_size_meter)
            toPlot = src_image.read(window=win)  
            a[act_row][act_col].set_title(acq_date, verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})
            rasterio.plot.show(toPlot, ax=a[act_row][act_col], transform=src_image.window_transform(win)) 
            parcel.plot(ax=a[act_row][act_col], facecolor='none', edgecolor=vector_color) 

    fig.savefig(output_jpg_file, dpi=jpg_resolution, bbox_inches='tight')  
    pyplot.close(fig)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t\tplot_utils.calendar_view_generic:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    print(f"Calendar view: {time.time() - start} seconds")
    return fig, a