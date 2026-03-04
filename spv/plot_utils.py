#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Csaba Wirnhardt
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

# test dobryma

import numpy as np

from matplotlib import pyplot
pyplot.ioff()

def get_year_months_dict(acq_dates):
    acq_dates.sort()
    year_months_dict = {}
    for date in acq_dates:
        
        acq_date = np.datetime_as_string(date, unit='D')
        
        year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
        day = int(acq_date.split('-')[2])
        if not year_month in year_months_dict:
            year_months_dict[year_month] = []

        year_months_dict[year_month].append(day)
    return year_months_dict

def diff_month(d1, d2):
    mdiff = (d1.astype('datetime64[Y]').astype(int) - d2.astype('datetime64[Y]').astype(int)) * 12 \
          + (d1.astype('datetime64[M]').astype(int) - d2.astype('datetime64[M]').astype(int)) % 12
          
    return mdiff

def get_number_of_rows(acq_dates):
    #we need rows for the months where there is no acquisition at all
    #so we take the lowest and highest acquisition datee and calculate the difference in months
    #this will be the number of rows needed for the imagettes in the monthly view
    number_of_year_months = diff_month(max(acq_dates), min(acq_dates)) + 1
     
    return number_of_year_months

def get_year_months_dict_for_half_weekly(dates):
    
    year_month_dict = {}
    
    for date in dates:
        
        # let's go through the dates and make year_month from them
        # convert the date into a string
        acq_date = np.datetime_as_string(date, unit='D')
        
        # turn the string into a number with year (x100) and the month
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
    
def get_current_list_of_months(first_year_month, number_of_year_months):
    """
    Summary that provides a list of strings with the years and months to be
    add on top of the temporal plots

    Parameters
    ----------
    first_year_month : TYPE
        DESCRIPTION.
    number_of_year_months : TYPE
        DESCRIPTION.

    Returns
    -------
    current_textstrs : TYPE
        DESCRIPTION.

    """    
    month_list = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", \
                  "SEP", "OCT", "NOV", "DEC"]
        
    year = int(first_year_month[:4])
    month = int(first_year_month[4:]) - 1
    
    current_textstrs = []
    for ii in range(number_of_year_months) :
        current_textstrs.append(f'{year}\n{month_list[month]}')
        
        month += 1
        year += int(month / 12)
        month %= 12
        
    return current_textstrs

def get_half_weekly_column(date, year_months_dict_half_weekly):
    
    acq_date = np.datetime_as_string(date, unit='D')
    
    # now check the position of a given date in the year_month/weeks nested dictionary
    half_weekly_column = 0 
    
    year_month = int(acq_date.split('-')[0] + acq_date.split('-')[1])
    year_month_dict_current = year_months_dict_half_weekly[year_month]
    
    if acq_date in year_month_dict_current.values():
        half_weekly_column = list(year_month_dict_current.keys())[list(year_month_dict_current.values()).index(acq_date)]

    return half_weekly_column

def get_current_row(curr_acq_date, acq_dates):
    
    curr_row = diff_month(curr_acq_date, min(acq_dates)) + 1
     
    return curr_row

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

def stretch_and_stack(band_red, band_green, band_blue, lut) :
    
    stretch = lut[list(lut.keys())[0]]
    red_norm = (band_red - stretch[0]) / (stretch[1] - stretch[0])
    red_norm[red_norm < 0] = 0
    red_norm[red_norm > 1] = 1
    red_norm = (255 * red_norm).astype(np.uint8)
    
    stretch = lut[list(lut.keys())[1]]
    green_norm = (band_green - stretch[0]) / (stretch[1] - stretch[0])
    green_norm[green_norm < 0] = 0
    green_norm[green_norm > 1] = 1
    green_norm = (255 * green_norm).astype(np.uint8)

    stretch = lut[list(lut.keys())[2]]
    blue_norm = (band_blue - stretch[0]) / (stretch[1] - stretch[0])
    blue_norm[blue_norm < 0] = 0
    blue_norm[blue_norm > 1] = 1
    blue_norm = (255 * blue_norm).astype(np.uint8)
    
    return np.dstack((red_norm, green_norm, blue_norm))  