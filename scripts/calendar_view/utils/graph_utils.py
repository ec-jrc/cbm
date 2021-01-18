#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Csaba Wirnhardt
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import pandas as pd
import matplotlib.dates as mdates
from matplotlib import pyplot
import matplotlib.ticker as ticker
import datetime
import calendar
import os
import time
import numpy as np

def get_ndvi_profiles_from_csv(csv_file):
    ndvi_profile = pd.read_csv(csv_file) 
    return ndvi_profile

def display_ndvi_profiles_old_old(csv_file, plotTitle, cropName, outputFolder, 
                                           addErrorBars = False):
    """
    this function plots the NDVI profile for parcelNumber and saves the figures to the outputFolder
    """
    ndvi_profile = pd.read_csv(csv_file) 
    # rename the column names from 'mean' to more meaningful names
    pProfiles = pProfiles.rename(columns={'mean': 'S2 NDVI'})
    # pProfiles = pProfiles.rename(columns={'to_date': 'date'})

    # plot the time series
    ax0 = plt.gca()

    if not pProfiles.empty:
        if addErrorBars:
            pProfiles.plot(kind='line', marker='+', x='date',y='S2 NDVI', yerr='std', color = 'blue', ax=ax0, capsize=4,
                      ecolor='grey', barsabove = 'True')   
        else:
            pProfiles.plot(kind='line', marker='+', x='date',y='S2 NDVI', color = 'blue', ax=ax0)

    # format the graph a little bit
    plt.ylabel('NDVI')
    plt.title(plotTitle + ", Parcel id: " + str(parcelNumber) + " " + cropName)
    ax0.set_ylim([0,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
#     ax = plt.axes()        
    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # horizontal lines

    fig = plt.gcf()
    fig.autofmt_xdate() # Rotation
    fig.set_size_inches(13, 7)

    ax0.set_xlim([datetime.date(2019, 3, 1), datetime.date(2019, 8, 30)])

    ax0.text(0.09, 0.9, 
        'MAR',
        verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
        color='blue', fontsize=15)
    ax0.text(0.25, 0.9, 
        'APR',
        verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
        color='blue', fontsize=15)
    ax0.text(0.42, 0.9, 
        'MAY',
        verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
        color='blue', fontsize=15)
    ax0.text(0.59, 0.9, 
        'JUN',
        verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
        color='blue', fontsize=15)
    ax0.text(0.75, 0.9, 
        'JUL',
        verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
        color='blue', fontsize=15)
    ax0.text(0.91, 0.9, 
        'AUG',
        verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
        color='blue', fontsize=15)

    # plt.show()
    
    # save the figure to a jpg file
    fig.savefig(outputFolder + '/parcel_id_' + str(parcelNumber) + '_NDVI.jpg')    

def get_current_list_of_months(first_year_month, number_of_year_months):
    textstrs_tuples = [
                       ("201701", "2017\nJAN"),
                       ("201702", "2017\nFEB"),
                       ("201703", "2017\nMAR"),
                       ("201704", "2017\nAPR"),
                       ("201705", "2017\nMAY"),
                       ("201706", "2017\nJUN"),
                       ("201707", "2017\nJUL"),
                       ("201708", "2017\nAUG"),
                       ("201709", "2017\nSEP"),
                       ("201710", "2017\nOCT"),
                       ("201711", "2017\nNOV"),
                       ("201712", "2017\nDEC"),
                       ("201801", "2018\nJAN"),
                       ("201802", "2018\nFEB"),
                       ("201803", "2018\nMAR"),
                       ("201804", "2018\nAPR"),
                       ("201805", "2018\nMAY"),
                       ("201806", "2018\nJUN"),
                       ("201807", "2018\nJUL"),
                       ("201808", "2018\nAUG"),
                       ("201809", "2018\nSEP"),
                       ("201810", "2018\nOCT"),
                       ("201811", "2018\nNOV"),
                       ("201812", "2018\nDEC"),
                       ("201901", "2019\nJAN"),
                       ("201902", "2019\nFEB"),
                       ("201903", "2019\nMAR"),
                       ("201904", "2019\nAPR"),
                       ("201905", "2019\nMAY"),
                       ("201906", "2019\nJUN"),
                       ("201907", "2019\nJUL"),
                       ("201908", "2019\nAUG"),
                       ("201909", "2019\nSEP"),
                       ("201910", "2019\nOCT"),
                       ("201911", "2019\nNOV"),
                       ("201912", "2019\nDEC"),
                       ("202001", "2020\nJAN"),
                       ("202002", "2020\nFEB"),
                       ("202003", "2020\nMAR"),
                       ("202004", "2020\nAPR"),
                       ("202005", "2020\nMAY"),
                       ("202006", "2020\nJUN"),
                       ("202007", "2020\nJUL"),
                       ("202008", "2020\nAUG"),
                       ("202009", "2020\nSEP"),
                       ("202010", "2020\nOCT"),
                       ("202011", "2020\nNOV"),
                       ("202012", "2020\nDEC"),
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
    
def display_ndvi_profiles(parcel_id, crop, plot_title, out_tif_folder_base, logfile,
                                           add_error_bars = False):                                         
    """
    this function plots the NDVI profile and saves the figures to the outputFolder
    """  
    y_tick_spacing = 0.1
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    ndvi_folder = out_tif_folder_base + "/ndvi"
    ndvi_csv_file = ndvi_folder + "/" + chip_folder + "_ndvi.csv"
    output_graph_folder = out_tif_folder_base + "/ndvi_graphs"
    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)
    ndvi_profile = pd.read_csv(ndvi_csv_file)
    

    ndvi_profile['acq_date'] = pd.to_datetime(ndvi_profile.acq_date)
    ndvi_profile = ndvi_profile.sort_values(by=['acq_date'])
    # rename the column names from 'ndvi_mean' to more meaningful name
    ndvi_profile = ndvi_profile.rename(columns={'ndvi_mean': 'S2 NDVI'})
    ndvi_profile = ndvi_profile.rename(columns={'acq_date': 'date'})    
        
    # print(ndvi_profile)
    # print(ndvi_profile['S2 NDVI'].dtypes)
    # print(ndvi_profile['ndvi_std'].dtypes)
    # print("valami")
    # return
    # print("akarmi")
    # check if there are real NDVI values and stdev values in the dataframe 
    # (for very small parcels the values in the csv can be None which evaluates as object in 
    # the dataframe, insted of dtype float64
    if not ndvi_profile['S2 NDVI'].dtypes == "float64" or \
        not ndvi_profile['ndvi_std'].dtypes == "float64":
        return    
    

    # plot the time series
    ax0 = pyplot.gca()

    if not ndvi_profile.empty:
        if add_error_bars:
            ndvi_profile.plot(kind='line', marker='+', x='date',y='S2 NDVI', yerr='ndvi_std', color = 'blue', ax=ax0, 
                              capsize=4, ecolor='grey', barsabove = 'True')   
        else:
            ndvi_profile.plot(kind='line', marker='+', x='date',y='S2 NDVI', color = 'blue', ax=ax0)

    # format the graph a little bit
    pyplot.ylabel('NDVI')
    parcelNumber = ndvi_profile.iloc[0]['Field_ID']
    pyplot.title(plot_title + ", Parcel id: " + str(parcelNumber) + " " + crop)
    ax0.set_ylim([0,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
         
    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # vertical lines

    fig = pyplot.gcf()
    fig.autofmt_xdate() # Rotation
    fig_size_x = 13
    fig_size_y = 7
    fig.set_size_inches(fig_size_x, fig_size_y)
    
    min_month = min(ndvi_profile['date']).date().month
    min_year = min(ndvi_profile['date']).date().year
    
    max_month = max(ndvi_profile['date']).date().month
    max_year = max(ndvi_profile['date']).date().year
    
    number_of_months = diff_month(max(ndvi_profile['date']).date(), min(ndvi_profile['date']).date()) + 1
    ax0.set_xlim([datetime.date(min_year, min_month, 1), 
                  datetime.date(max_year, max_month,
                                calendar.monthrange(max_year, max_month)[1])])
    
    min_year_month = str(min_year) + ('0' + str(min_month))[-2:]
#     start_x = 0.045
    step_x = 1/number_of_months
    start_x = step_x/2 # positions are in graph coordinate system between 0 and 1
                                     # so first year_month label is at half the size of the widht of
                                     # one month
            

    loc_y = 0.915
    
    current_year_month_text = get_current_list_of_months(min_year_month, number_of_months)
    
    for current_year_month_index in range (0, number_of_months):
        t = current_year_month_text[current_year_month_index]
        loc_x = start_x + (current_year_month_index) * step_x
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
                color='blue', fontsize=13)



    ax0.yaxis.set_major_locator(ticker.MultipleLocator(y_tick_spacing))

                
    # save the figure to a jpg file
    fig.savefig(output_graph_folder + '/parcel_id_' + str(parcel_id) + '_NDVI.jpg') 
    pyplot.close(fig)    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\traph_utils.display_ndvi_profiles:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return ndvi_profile
    
def display_ndwi_profiles(parcel_id, crop, plot_title, out_tif_folder_base, logfile,
                                           add_error_bars = False):                                         
    """
    this function plots the ndwi profile and saves the figures to the outputFolder
    """  
    y_tick_spacing = 0.1
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    ndwi_folder = out_tif_folder_base + "/ndwi"
    ndwi_csv_file = ndwi_folder + "/" + chip_folder + "_ndwi.csv"
    output_graph_folder = out_tif_folder_base + "/ndwi_graphs"
    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)
    ndwi_profile = pd.read_csv(ndwi_csv_file)
    

    ndwi_profile['acq_date'] = pd.to_datetime(ndwi_profile.acq_date)
    ndwi_profile = ndwi_profile.sort_values(by=['acq_date'])
    # rename the column names from 'ndwi_mean' to more meaningful name
    ndwi_profile = ndwi_profile.rename(columns={'ndwi_mean': 'S2 NDWI'})
    ndwi_profile = ndwi_profile.rename(columns={'acq_date': 'date'})    
        
    # print(ndwi_profile)
    # print(ndwi_profile['S2 ndwi'].dtypes)
    # print(ndwi_profile['ndwi_std'].dtypes)
    # print("valami")
    # return
    # print("akarmi")
    # check if there are real ndwi values and stdev values in the dataframe 
    # (for very small parcels the values in the csv can be None which evaluates as object in 
    # the dataframe, insted of dtype float64
    if not ndwi_profile['S2 NDWI'].dtypes == "float64" or \
        not ndwi_profile['ndwi_std'].dtypes == "float64":
        return    
    

    # plot the time series
    ax0 = pyplot.gca()

    if not ndwi_profile.empty:
        if add_error_bars:
            ndwi_profile.plot(kind='line', marker='+', x='date',y='S2 NDWI', yerr='ndwi_std', color = 'blue', ax=ax0, 
                              capsize=4, ecolor='grey', barsabove = 'True')   
        else:
            ndwi_profile.plot(kind='line', marker='+', x='date',y='S2 NDWI', color = 'blue', ax=ax0)

    # format the graph a little bit
    pyplot.ylabel('NDWI')
    parcelNumber = ndwi_profile.iloc[0]['Field_ID']
    pyplot.title(plot_title + ", Parcel id: " + str(parcelNumber) + " " + crop)
    ax0.set_ylim([-1,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
         
    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # vertical lines

    fig = pyplot.gcf()
    fig.autofmt_xdate() # Rotation
    fig_size_x = 13
    fig_size_y = 7
    fig.set_size_inches(fig_size_x, fig_size_y)
    
    min_month = min(ndwi_profile['date']).date().month
    min_year = min(ndwi_profile['date']).date().year
    
    max_month = max(ndwi_profile['date']).date().month
    max_year = max(ndwi_profile['date']).date().year
    
    number_of_months = diff_month(max(ndwi_profile['date']).date(), min(ndwi_profile['date']).date()) + 1
    ax0.set_xlim([datetime.date(min_year, min_month, 1), 
                  datetime.date(max_year, max_month,
                                calendar.monthrange(max_year, max_month)[1])])
    
    min_year_month = str(min_year) + ('0' + str(min_month))[-2:]
#     start_x = 0.045
    step_x = 1/number_of_months
    start_x = step_x/2 # positions are in graph coordinate system between 0 and 1
                                     # so first year_month label is at half the size of the widht of
                                     # one month
            

    loc_y = 0.915
    
    current_year_month_text = get_current_list_of_months(min_year_month, number_of_months)
    
    for current_year_month_index in range (0, number_of_months):
        t = current_year_month_text[current_year_month_index]
        loc_x = start_x + (current_year_month_index) * step_x
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
                color='blue', fontsize=13)

    ax0.yaxis.set_major_locator(ticker.MultipleLocator(y_tick_spacing))                
    # save the figure to a jpg file
    fig.savefig(output_graph_folder + '/parcel_id_' + str(parcel_id) + '_ndwi.jpg') 
    pyplot.close(fig)    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\traph_utils.display_ndwi_profiles:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return ndwi_profile    

def display_ndvi_profiles_with_mean_profile_of_the_crop(parcel_id, crop, plot_title, out_tif_folder_base, logfile,
                                           add_error_bars = False):                                         
    """
    this function plots the NDVI profile and saves the figures to the outputFolder
    """  
    mean_profile_folder = "c:/Users/Csaba/ownCloud/GTCAP/cbm_qa/be_fl/notebooks/output_csv_selected_v02"
    
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    ndvi_folder = out_tif_folder_base + "/ndvi"
    ndvi_csv_file = ndvi_folder + "/" + chip_folder + "_ndvi.csv"
    mean_ndvi_csv_file = mean_profile_folder + "/" + crop  #+ ".csv"
    output_graph_folder = out_tif_folder_base + "/ndvi_graphs_with_mean"
    
    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)
    ndvi_profile = pd.read_csv(ndvi_csv_file)

    

    ndvi_profile['acq_date'] = pd.to_datetime(ndvi_profile.acq_date)
    ndvi_profile = ndvi_profile.sort_values(by=['acq_date'])
    # rename the column names from 'ndvi_mean' to more meaningful name
    ndvi_profile = ndvi_profile.rename(columns={'ndvi_mean': 'S2 NDVI'})
    ndvi_profile = ndvi_profile.rename(columns={'acq_date': 'date'})    

    mean_ndvi_csv_file_exists = False
    if os.path.isfile(mean_ndvi_csv_file):
        mean_ndvi_csv_file_exists = True
        mean_ndvi_profile = pd.read_csv(mean_ndvi_csv_file)    
        mean_ndvi_profile['acq_date'] = pd.to_datetime(mean_ndvi_profile.acq_date)
        mean_ndvi_profile = mean_ndvi_profile.sort_values(by=['acq_date'])
        # rename the column names from 'ndvi_mean' to more meaningful name
        mean_ndvi_profile = mean_ndvi_profile.rename(columns={'ndvi_mean': 'S2 NDVI mean'})
        mean_ndvi_profile = mean_ndvi_profile.rename(columns={'acq_date': 'date'})    
        
    # print(ndvi_profile)
    # print(ndvi_profile['S2 NDVI'].dtypes)
    # print(ndvi_profile['ndvi_std'].dtypes)
    # print("valami")
    # return
    # print("akarmi")
    # check if there are real NDVI values and stdev values in the dataframe 
    # (for very small parcels the values in the csv can be None which evaluates as object in 
    # the dataframe, insted of dtype float64
    if not ndvi_profile['S2 NDVI'].dtypes == "float64" or \
        not ndvi_profile['ndvi_std'].dtypes == "float64":
        return    
    

    # plot the time series
    ax0 = pyplot.gca()

    if not ndvi_profile.empty:
        if add_error_bars:
            ndvi_profile.plot(kind='line', marker='+', x='date',y='S2 NDVI', yerr='ndvi_std', color = 'blue', ax=ax0, 
                              capsize=4, ecolor='grey', barsabove = 'True')   
        else:
            
            ndvi_profile.plot(kind='line', marker='+', x='date',y='S2 NDVI', color = 'blue', ax=ax0)
            if mean_ndvi_csv_file_exists:
                mean_ndvi_profile.plot(kind='line', marker='+', x='date',y='S2 NDVI mean', color = 'red', ax=ax0)

    # format the graph a little bit
    pyplot.ylabel('NDVI')
    parcelNumber = ndvi_profile.iloc[0]['Field_ID']
    pyplot.title(plot_title + ", Parcel id: " + str(parcelNumber) + " " + crop)
    ax0.set_ylim([0,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
         
    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # vertical lines

    fig = pyplot.gcf()
    fig.autofmt_xdate() # Rotation
    fig_size_x = 13
    fig_size_y = 7
    fig.set_size_inches(fig_size_x, fig_size_y)
    
    min_month = min(ndvi_profile['date']).date().month
    min_year = min(ndvi_profile['date']).date().year
    
    max_month = max(ndvi_profile['date']).date().month
    max_year = max(ndvi_profile['date']).date().year
    
    number_of_months = diff_month(max(ndvi_profile['date']).date(), min(ndvi_profile['date']).date()) + 1
    ax0.set_xlim([datetime.date(min_year, min_month, 1), 
                  datetime.date(max_year, max_month,
                                calendar.monthrange(max_year, max_month)[1])])
    
    min_year_month = str(min_year) + ('0' + str(min_month))[-2:]
#     start_x = 0.045
    step_x = 1/number_of_months
    start_x = step_x/2 # positions are in graph coordinate system between 0 and 1
                                     # so first year_month label is at half the size of the widht of
                                     # one month
            

    loc_y = 0.915
    
    current_year_month_text = get_current_list_of_months(min_year_month, number_of_months)
    
    for current_year_month_index in range (0, number_of_months):
        t = current_year_month_text[current_year_month_index]
        loc_x = start_x + (current_year_month_index) * step_x
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
                color='blue', fontsize=13)

    # save the figure to a jpg file
    fig.savefig(output_graph_folder + '/parcel_id_' + str(parcel_id) + '_NDVI.jpg') 
    pyplot.close(fig)    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\graph_utils.display_ndvi_profiles_with_mean_profile_of_the_crop:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return ndvi_profile
    
def display_ndvi_profiles_with_mean_profile_of_the_crop_with_std(parcel_id, crop, plot_title, out_tif_folder_base, 
                                                                 logfile, mean_profile_folder,
                                                                 add_error_bars = False,
                                                                 mean_color = 'green', current_color = 'magenta'):                                         
    """
    this function plots the NDVI profile and saves the figures to the outputFolder
    """  
    # mean_profile_folder = "c:/Users/Csaba/ownCloud/GTCAP/cbm_qa/be_fl/notebooks/output_csv_selected_v02"
    
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    ndvi_folder = out_tif_folder_base + "/ndvi"
    ndvi_csv_file = ndvi_folder + "/" + chip_folder + "_ndvi.csv"

    mean_ndvi_csv_file = mean_profile_folder + "/" + crop + ".csv"
    output_graph_folder = out_tif_folder_base + "/ndvi_graphs_with_mean"
    
    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)
    ndvi_profile = pd.read_csv(ndvi_csv_file)
    
    

    ndvi_profile['acq_date'] = pd.to_datetime(ndvi_profile.acq_date)
    ndvi_profile = ndvi_profile.sort_values(by=['acq_date'])
    # rename the column names from 'ndvi_mean' to more meaningful name
    ndvi_profile = ndvi_profile.rename(columns={'ndvi_mean': 'S2 NDVI'})
    ndvi_profile = ndvi_profile.rename(columns={'acq_date': 'date'})    

    mean_ndvi_csv_file_exists = False
    if os.path.isfile(mean_ndvi_csv_file):
        mean_ndvi_csv_file_exists = True
        mean_ndvi_profile = pd.read_csv(mean_ndvi_csv_file)    
        mean_ndvi_profile['acq_date'] = pd.to_datetime(mean_ndvi_profile.acq_date)
        mean_ndvi_profile = mean_ndvi_profile.sort_values(by=['acq_date'])
        # rename the column names from 'ndvi_mean' to more meaningful name
        mean_ndvi_profile = mean_ndvi_profile.rename(columns={'ndvi_mean': 'S2 NDVI mean'})
        mean_ndvi_profile = mean_ndvi_profile.rename(columns={'acq_date': 'date'})    
        
#     print(mean_ndvi_profile)
    # print(ndvi_profile['S2 NDVI'].dtypes)
    # print(ndvi_profile['ndvi_std'].dtypes)
    # print("valami")
    # return
    # print("akarmi")
    # check if there are real NDVI values and stdev values in the dataframe 
    # (for very small parcels the values in the csv can be None which evaluates as object in 
    # the dataframe, insted of dtype float64
    if not ndvi_profile['S2 NDVI'].dtypes == "float64" or \
        not ndvi_profile['ndvi_std'].dtypes == "float64":
        return    
    

    # plot the time series
    ax0 = pyplot.gca()

    if not ndvi_profile.empty:
        if add_error_bars:
            ndvi_profile.plot(kind='line', marker='+', x='date',y='S2 NDVI', yerr='ndvi_std', color = current_color, ax=ax0, 
                              capsize=4, ecolor='magenta', barsabove = 'True')   
        else:
            
            ndvi_profile.plot(kind='line', marker='+', x='date',y='S2 NDVI', color = current_color, ax=ax0)
            
        if mean_ndvi_csv_file_exists:
            mean_ndvi_profile.plot(kind='line', marker='+', x='date',y='S2 NDVI mean', color = mean_color, ax=ax0)

#                 ax.plot(x, y_est, '-')
#                 mean_ndvi_profile.plot.fill_between('date', 'S2 NDVI mean' - 'ndvi_std', 'S2 NDVI mean' + 'ndvi_std', alpha=0.2)
            pyplot.fill_between(mean_ndvi_profile['date'], 
                                                  mean_ndvi_profile['S2 NDVI mean']-mean_ndvi_profile['ndvi_stdev'], 
                                                  mean_ndvi_profile['S2 NDVI mean']+mean_ndvi_profile['ndvi_stdev'],
                                                  alpha=0.2, color = mean_color)

    
    
    # format the graph a little bit
    pyplot.ylabel('NDVI')
    parcelNumber = ndvi_profile.iloc[0]['Field_ID']
    pyplot.title(plot_title + ", Parcel id: " + str(parcelNumber) + " " + crop)
    ax0.set_ylim([0,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
         
    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # vertical lines

    fig = pyplot.gcf()
    fig.autofmt_xdate() # Rotation
    fig_size_x = 13
    fig_size_y = 7
    fig.set_size_inches(fig_size_x, fig_size_y)
    
    min_month = min(ndvi_profile['date']).date().month
    min_year = min(ndvi_profile['date']).date().year
    
    max_month = max(ndvi_profile['date']).date().month
    max_year = max(ndvi_profile['date']).date().year
    
    number_of_months = diff_month(max(ndvi_profile['date']).date(), min(ndvi_profile['date']).date()) + 1
    ax0.set_xlim([datetime.date(min_year, min_month, 1), 
                  datetime.date(max_year, max_month,
                                calendar.monthrange(max_year, max_month)[1])])
    
    min_year_month = str(min_year) + ('0' + str(min_month))[-2:]
#     start_x = 0.045
    step_x = 1/number_of_months
    start_x = step_x/2 # positions are in graph coordinate system between 0 and 1
                                     # so first year_month label is at half the size of the widht of
                                     # one month
            

    loc_y = 0.915
    
    current_year_month_text = get_current_list_of_months(min_year_month, number_of_months)
    
    for current_year_month_index in range (0, number_of_months):
        t = current_year_month_text[current_year_month_index]
        loc_x = start_x + (current_year_month_index) * step_x
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
                color='blue', fontsize=13)

    # save the figure to a jpg file
    fig.savefig(output_graph_folder + '/parcel_id_' + str(parcel_id) + '_NDVI.jpg') 
    pyplot.close(fig)    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\graph_utils.display_ndvi_profiles_with_mean_profile_of_the_crop:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return ndvi_profile


def display_s1_bs_profiles(parcel_id, crop, plot_title, out_tif_folder_base, logfile,
                                           add_error_bars, polarisation, orbit_orientation):                                         
    """
    this function plots the NDVI profile and saves the figures to the outputFolder
    """  
    y_tick_spacing = 0.1
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    s1_bs_folder = out_tif_folder_base + "/s1_bs"
    s1_bs_csv_file = s1_bs_folder + "/" + chip_folder + "_s1bs_" + polarisation + "_" + orbit_orientation + ".csv"
    output_graph_folder = out_tif_folder_base + "/s1_bs_graphs_" + polarisation + "_" + orbit_orientation
    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)
    s1_bs_profile = pd.read_csv(s1_bs_csv_file)
    

    s1_bs_profile['acq_date'] = pd.to_datetime(s1_bs_profile.acq_date)
    s1_bs_profile = s1_bs_profile.sort_values(by=['acq_date'])
    # rename the column names from 'ndvi_mean' to more meaningful name
    s1_bs_profile = s1_bs_profile.rename(columns={'bs_mean': 'S1 BS'})
    s1_bs_profile = s1_bs_profile.rename(columns={'acq_date': 'date'})    
        
    # print(s1_bs_profile)
    # print(s1_bs_profile['S2 NDVI'].dtypes)
    # print(s1_bs_profile['ndvi_std'].dtypes)
    # print("valami")
    # return
    # print("akarmi")
    # check if there are real NDVI values and stdev values in the dataframe 
    # (for very small parcels the values in the csv can be None which evaluates as object in 
    # the dataframe, insted of dtype float64
    if not s1_bs_profile['S1 BS'].dtypes == "float64" or \
        not s1_bs_profile['bs_std'].dtypes == "float64":
        return    
    

    # plot the time series
    ax0 = pyplot.gca()

    if not s1_bs_profile.empty:
        if add_error_bars:
            s1_bs_profile.plot(kind='line', marker='+', x='date',y='S1 BS', yerr='bs_std', color = 'blue', ax=ax0, 
                              capsize=4, ecolor='grey', barsabove = 'True')   
        else:
            s1_bs_profile.plot(kind='line', marker='+', x='date',y='S1 BS', color = 'blue', ax=ax0)

    # format the graph a little bit
    pyplot.ylabel('Backscatter')
    # pyplot.ylabel(r'Backscattering coefficient, $\gamma\degree$ (dB)')
    parcelNumber = s1_bs_profile.iloc[0]['Field_ID']
    pyplot.title(plot_title + ", Parcel id: " + str(parcelNumber) + " " + crop)
    ax0.set_ylim([0,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
         
    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # vertical lines

    fig = pyplot.gcf()
    fig.autofmt_xdate() # Rotation
    fig_size_x = 13
    fig_size_y = 7
    fig.set_size_inches(fig_size_x, fig_size_y)
    
    min_month = min(s1_bs_profile['date']).date().month
    min_year = min(s1_bs_profile['date']).date().year
    
    max_month = max(s1_bs_profile['date']).date().month
    max_year = max(s1_bs_profile['date']).date().year
    
    number_of_months = diff_month(max(s1_bs_profile['date']).date(), min(s1_bs_profile['date']).date()) + 1
    ax0.set_xlim([datetime.date(min_year, min_month, 1), 
                  datetime.date(max_year, max_month,
                                calendar.monthrange(max_year, max_month)[1])])
    
    min_year_month = str(min_year) + ('0' + str(min_month))[-2:]
#     start_x = 0.045
    step_x = 1/number_of_months
    start_x = step_x/2 # positions are in graph coordinate system between 0 and 1
                                     # so first year_month label is at half the size of the widht of
                                     # one month
            

    loc_y = 0.915
    
    current_year_month_text = get_current_list_of_months(min_year_month, number_of_months)
    
    for current_year_month_index in range (0, number_of_months):
        t = current_year_month_text[current_year_month_index]
        loc_x = start_x + (current_year_month_index) * step_x
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
                color='blue', fontsize=13)



    ax0.yaxis.set_major_locator(ticker.MultipleLocator(y_tick_spacing))

                
    # save the figure to a jpg file
    fig.savefig(output_graph_folder + '/parcel_id_' + str(parcel_id) + '_NDVI.jpg') 
    pyplot.close(fig)    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tgraph_utils.display_s1_bs_profiles:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return s1_bs_profile

def display_s1_bs_profiles_together(parcel_id, crop, plot_title, out_tif_folder_base, logfile,
                                           add_error_bars):                                         
    """
    this function plots the Sentinel-1 backscatter profile and saves the figures to the output_graph_folder
    """  
    # polarisation, orbit_orientation
    
    
    # y_tick_spacing = 0.1
    fout = open(logfile, 'a')
    start = time.time()
    chip_folder = str(parcel_id) + '_' + crop
    s1_bs_folder = out_tif_folder_base + "/s1_bs"
    output_graph_folder = out_tif_folder_base + "/s1_bs_graphs_together"
    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)    
    
    polarisations = ["VV", "VH"]
    orbit_orientations = ["D", "A"]
    # polarisation = "VV"
    # orbit_orientation = "D"
    for polarisation in polarisations:
        for orbit_orientation in orbit_orientations:
        
            s1_bs_csv_file = s1_bs_folder + "/" + chip_folder + "_s1bs_" + polarisation + "_" + orbit_orientation + ".csv"
            s1_bs_profile = pd.read_csv(s1_bs_csv_file)

            s1_bs_profile['acq_date'] = pd.to_datetime(s1_bs_profile.acq_date)
            s1_bs_profile = s1_bs_profile.sort_values(by=['acq_date'])
            # rename the column names from 'ndvi_mean' to more meaningful name
            profile_name = 'S1 BS ' + polarisation + " " + orbit_orientation
            s1_bs_profile = s1_bs_profile.rename(columns={'bs_mean': profile_name})
            s1_bs_profile = s1_bs_profile.rename(columns={'acq_date': 'date'})   

            s1_bs_profile[profile_name] = s1_bs_profile[profile_name].map(lambda s: 10.0*np.log10(s))
            

            # check if there are real NDVI values and stdev values in the dataframe 
            # (for very small parcels the values in the csv can be None which evaluates as object in 
            # the dataframe, insted of dtype float64
            if not s1_bs_profile[profile_name].dtypes == "float64" or \
                not s1_bs_profile['bs_std'].dtypes == "float64":
                return    

            # plot the time series
            ax0 = pyplot.gca()

            if not s1_bs_profile.empty:
                if add_error_bars:
                    s1_bs_profile.plot(kind='line', marker='+', x='date',y=profile_name, yerr='bs_std', ax=ax0, 
                                      capsize=4, ecolor='grey', barsabove = 'True')   
                else:
                    s1_bs_profile.plot(kind='line', marker='+', x='date',y=profile_name, ax=ax0)

    # format the graph a little bit

    pyplot.ylabel(r'Backscattering coefficient, $\gamma\degree$ (dB)')
    parcelNumber = s1_bs_profile.iloc[0]['Field_ID']
    pyplot.title(plot_title + ", Parcel id: " + str(parcelNumber) + " " + crop)
    # # ax0.set_ylim([0,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    # ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    # years_fmt = mdates.DateFormatter('%Y')

    # ax0.xaxis.set_major_formatter(years_fmt)
         
    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # vertical lines

    fig = pyplot.gcf()
    # fig.autofmt_xdate() # Rotation
    fig_size_x = 13
    fig_size_y = 7
    fig.set_size_inches(fig_size_x, fig_size_y)

    min_month = min(s1_bs_profile['date']).date().month
    min_year = min(s1_bs_profile['date']).date().year

    max_month = max(s1_bs_profile['date']).date().month
    max_year = max(s1_bs_profile['date']).date().year

    number_of_months = diff_month(max(s1_bs_profile['date']).date(), min(s1_bs_profile['date']).date()) + 1
    

    ax0.set_xlim([datetime.date(min_year, min_month, 1), 
                  datetime.date(max_year, max_month,
                                calendar.monthrange(max_year, max_month)[1])])

    min_year_month = str(min_year) + ('0' + str(min_month))[-2:]
    #     start_x = 0.045
    step_x = 1/number_of_months
    start_x = step_x/2 # positions are in graph coordinate system between 0 and 1
                                     # so first year_month label is at half the size of the widht of
                                     # one month
            

    loc_y = 0.915

    current_year_month_text = get_current_list_of_months(min_year_month, number_of_months)

    for current_year_month_index in range (0, number_of_months):
        t = current_year_month_text[current_year_month_index]
        loc_x = start_x + (current_year_month_index) * step_x
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
                color='blue', fontsize=13)



    # ax0.yaxis.set_major_locator(ticker.MultipleLocator(y_tick_spacing))

                
    # save the figure to a jpg file
    fig.savefig(output_graph_folder + '/parcel_id_' + str(parcel_id) + '_BS.jpg') 
    pyplot.close(fig)    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\t", parcel_id,  "\tgraph_utils.display_s1_bs_profiles:\t", "{0:.3f}".format(time.time() - start), file=fout)
    fout.close()
    return s1_bs_profile    
    # csv_file = "e:/chips/nour2019_new01/ndvi/188779_NON-EFA_ALFALFA_ndvi.csv"

# p = get_ndvi_profiles_from_csv(csv_file)
# print(p)