# -*- coding: utf-8 -*-
# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : WIRNHARDT Csaba
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import requests
import pandas as pd
import datetime
import numpy as np
import os
from matplotlib import pyplot
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import calendar

def get_extracted_data_from_restful(ms, year, parcel_id, api_user, api_pass, tstype,
                                    ptype):
    was_error = False
    if ms == "be-wa":
        ms = "bewa"

    if ptype == "":
        url = "http://cap.users.creodias.eu/query/parcelTimeSeries?aoi=" + ms + "&year=" + str(year) + "&pid=" + str(parcel_id) + "&tstype=" + tstype + "&scl=True&ref=True"
    else:
        url = "http://cap.users.creodias.eu/query/parcelTimeSeries?aoi=" + ms + "&year=" + str(year) + "&pid=" + str(parcel_id) + "&ptype=" + ptype + "&tstype=" + tstype + "&scl=True&ref=True"
    print(url)
#    response = requests.get(url, auth=(api_user, api_pass))

    try:
        response = requests.get(url, auth=(api_user, api_pass))
        print(response)
        if response.status_code == 404 or response.status_code == 500:
            was_error = True
            df = pd.DataFrame()
        else:
            df = pd.read_json(response.text)
            if not df.empty:
                if tstype == "c6":
                    df['date_part']=df['date_part'].map(lambda e: datetime.datetime.fromtimestamp(e))
                    df['orbit'] = df['date_part'].apply(lambda s: 'D' if s.hour < 12 else 'A')
                    df['date'] = df['date_part'].apply(lambda s: s.date())

                if tstype == "bs":
                    df['date_part']=df['date_part'].map(lambda e: datetime.datetime.fromtimestamp(e))
                    df['orbit'] = df['date_part'].apply(lambda s: 'D' if s.hour < 12 else 'A')
                    df['date'] = df['date_part'].apply(lambda s: s.date())
                    # convert backscatters to decibels
                    # df['mean'] = df['mean'].map(lambda s: 10.0*np.log10(s))
            else:
                # create an Empty DataFrame object
                df = pd.DataFrame()
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

    if was_error:
        df = pd.DataFrame()
    return url, df, was_error


def get_extracted_data_from_db(host : str, port : str, dbname : str, user : str, password : str, sql_select : str) -> pd.DataFrame :

    """
    Summary :
        This function connects with the database and run the SQL query that is passed as a parameter.
        The query extracts time series of sentinel data formatted according to the marker detection tool requirements.
        A single, a subset or the whole set of parcels is retrieved according to the SQL based on the parameters set by the user.
        The result is stored in a dataframe and an index is set using the db id and the timestamp of the image.
        Database creadential are needed (that is different from Restful).
    Arguments :
        host - IP address of the database server
        port - port of the database (usually, 5432)
        dbname - name of the database where data is stored
        user - database user (with access privilege to the parcel, hist, sigs and metadata tables)
        password - database password
        sql_select -  sql query that retrive the desired data. It is passed as a parament by the function that calls get_extracted_data_from_db.
    Returns :
        A data frame with all sentinel data ready to be used by the preprocessing and marker detection modules.
    """
    # I connect with the db and check id the connection works fine
    conn = None
    try:
        conn = psycopg2.connect(host=host, port=port, dbname= dbname, user= user, password= password)
        print("Connection to DB established")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    # I execute the query and copy the data it in a panda dataframe that
    # I create with the same colums returned by the SQL statement
    cur = conn.cursor()
    cur.execute(sql_select)
    data_ts = cur.fetchall()
    col = []
    for x in cur.description:
      col.append(x[0])
    ts_db = pd.DataFrame(data=data_ts, columns = col)

    # I close the connection
    cur.close()
    conn.close()

    # I set the index (parcel id as in the db + datetime of the images)
    ts_db.set_index(['db_id', 'obstime'], inplace=True, verify_integrity=True)

    return ts_db


def get_parcel_data_from_restful(ms, year, parcel_id, api_user, api_pass, ptype):
    was_error = False
    if ms == "be-wa":
        ms = "bewa"
    if ptype == "":
        url = "http://cap.users.creodias.eu/query/parcelById?aoi=" + ms + "&year=" + str(year) + "&pid=" + str(parcel_id) + "&withGeometry=True"
    else:
        url = "http://cap.users.creodias.eu/query/parcelById?aoi=" + ms + "&year=" + str(year) + "&pid=" + str(parcel_id) + "&ptype=" + ptype + "&withGeometry=True"

    print(url)
    try:
        response = requests.get(url, auth=(api_user, api_pass))
        print(response)
        if response.status_code == 404 or response.status_code == 500:
            was_error = True
            df = pd.DataFrame()
        else:
            df = pd.read_json(response.text)
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

    if was_error:
        df = pd.DataFrame()

    return url, df, was_error

def get_cloudyness(cloud_stats, cloud_categories):
    is_cloudy = False
    cloudy_pixels = 0
    total_pixels = 0
    keys = [*cloud_stats]
    for key in keys:
        if int(key) in cloud_categories:
            is_cloudy = True
            cloudy_pixels += cloud_stats[key]
            total_pixels += cloud_stats[key]
        else:
            total_pixels += cloud_stats[key]
    if total_pixels > 0:
#        cloud_percent = int(round(cloudy_pixels / total_pixels *100,0))
        cloud_percent = round(cloudy_pixels / total_pixels *100,4)
    else:
        cloud_percent = None
    return is_cloudy, cloud_percent

def get_utm_number_from_reference(ref):
    return int(ref.split('_')[5][1:3])

def calculate_ndvi_std_from_band_mean_and_std(red_mean,nir_mean,red_std,nir_std):
    ndvi_std = 2 * np.sqrt((nir_mean*red_std)**2 +
                           (red_mean*nir_std)**2) / (nir_mean + red_mean)**2
    return ndvi_std

def calculate_ndvi_and_cloud_percent_for_the_parcel(df_ext, cloud_categories):
    # we make a copy first of the dataframe passed to this function to avoid changing the original
    # dataframe
    df = df_ext.copy()
    # Convert the epoch timestamp to a datetime
    df['date_part']=df['date_part'].map(lambda e: datetime.datetime.fromtimestamp(e))
    df['cloud_pct'] = df['hist'].apply(lambda s: get_cloudyness(s, cloud_categories)[1])
    bands = ['B04', 'B08']
    # Check if extraction exists for these bands 4 and 8 for NDVI calculation, otherwise quit
    length_of_band0 = len(df[df['band']==bands[0]])
    length_of_band1 = len(df[df['band']==bands[1]])
    if length_of_band0>0 and length_of_band1>0:
         # Treat each band separately.
        df0 = df[df['band']==bands[0]][['date_part', 'mean', 'count', 'std', 'cloud_pct', 'reference']]
        df1 = df[df['band']==bands[1]][['date_part', 'mean', 'count', 'std', 'cloud_pct', 'reference']]
        # Merge back into one DataFrame based on reference that should be unique
        dff = pd.merge(df0, df1, on = 'reference', suffixes = (bands[0], bands[1]))
        dff['ndvi'] = (dff[f"mean{bands[1]}"]-dff[f"mean{bands[0]}"])/(dff[f"mean{bands[1]}"]+dff[f"mean{bands[0]}"])
        dff['utm_number'] = dff['reference'].apply(lambda s: get_utm_number_from_reference(s))

        dff['ndvi_std'] = dff.apply(lambda x: calculate_ndvi_std_from_band_mean_and_std(x.meanB04,x.meanB08,x.stdB04,x.stdB08), axis=1)

        pd.set_option('precision', 3)
        pd.set_eng_float_format(accuracy=3)
        return dff
    else:
        return pd.DataFrame()

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

def display_ndvi_profiles(x_start_date, x_end_date, ndvi_profile, parcel_id, crop, plot_title,
                         output_graph_folder, logfile, jpg_filename,
                         add_error_bars = False, save_figures = False, fixed_date_range = False):
    y_tick_spacing = 0.1
    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)

    # plot the time series
    ax0 = pyplot.gca()
    if not ndvi_profile.empty:
        if add_error_bars:
            ndvi_profile.plot(kind='line', marker='+', x='dateB08', y='ndvi', label='S2 NDVI', yerr='ndvi_std', color = 'blue', ax=ax0, capsize=4, ecolor='grey', barsabove = 'True')
        else:
            ndvi_profile.plot(kind='line', marker='+', x='dateB08', y='ndvi', label='S2 NDVI', color = 'blue', ax=ax0)

    # format the graph a little bit
    pyplot.ylabel('NDVI')
    pyplot.title(plot_title + ", Parcel id: " + str(parcel_id) + " " + crop)
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

    if fixed_date_range:
        x_start_date_date = datetime.datetime.strptime(x_start_date, '%Y-%m-%d').date()
        x_end_date_date = datetime.datetime.strptime(x_end_date, '%Y-%m-%d').date()
        min_month = x_start_date_date.month
        min_year = x_start_date_date.year
        max_month = x_end_date_date.month
        max_year = x_end_date_date.year
        number_of_months = diff_month(x_end_date_date, x_start_date_date) + 1
    else:
        min_month = min(ndvi_profile['acq_date']).date().month
        min_year = min(ndvi_profile['acq_date']).date().year
        max_month = max(ndvi_profile['acq_date']).date().month
        max_year = max(ndvi_profile['acq_date']).date().year
        number_of_months = diff_month(max(ndvi_profile['acq_date']).date(), min(ndvi_profile['acq_date']).date()) + 1

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
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes, color='blue', fontsize=13)

    ax0.yaxis.set_major_locator(ticker.MultipleLocator(y_tick_spacing))

    # save the figure to a jpg file
    if save_figures:
        fig.savefig(output_graph_folder + '/' + jpg_filename )
        print("NDVI graph saved to file: " + output_graph_folder + '/' + jpg_filename )
        pyplot.close(fig)
        return(output_graph_folder + '/' + jpg_filename)

def get_clean_cloudfree_unique_s2_data(ts, cloud_categories):
    if not ts.empty:
        ts_clean = calculate_ndvi_and_cloud_percent_for_the_parcel(ts, cloud_categories)
        if ts_clean.empty:
            print("No clean, cloudfree data returned by function calculate_ndvi_and_cloud_percent_for_the_parcel", end =" ")
            print("in function get_clean_cloudfree_unique_s2_data")
            # we return an empty dataframe
            return pd.DataFrame()
        else:
            ts_clean['dateB04'] = ts_clean['date_partB04'].apply(lambda s: s.date())
            ts_clean['dateB08'] = ts_clean['date_partB08'].apply(lambda s: s.date())
            ts_clean = ts_clean.sort_values(by=['dateB04'])

        #                 The idea here is that we consider a date cloudfree only if in any UTM tile
        #                 it is cloudfree - this is a conservative approach: if after the processing
        #                 the image in any UTM there is a chance that it is cloudy we leave it out
            # first we calculate the maximum of the could percent for each date
            ts_clean_max_cc = ts_clean.groupby(['dateB04']).max()

            # then we select the dates where the max of the cloud percent is still 0
            # we create a list of these absolutely cloudfree dates
            cloudfree_dates = ts_clean_max_cc[ts_clean_max_cc['cloud_pctB04']==0].index.tolist()

            # then we create a dataframe with leaving in it only the cloudfree dates
            ts_clean_cloudfree = ts_clean[ts_clean['dateB04'].isin(cloudfree_dates)]

            # there can be still 2 calculated values per date (eg both UTM are cloudfree)
            # we calculate the max of NDVI and pixel count
            ts_clean_cloudfree_unique = ts_clean_cloudfree.groupby(['dateB04']).max()
            return ts_clean_cloudfree_unique

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
                    ("202101", "2021\nJAN"),
                    ("202102", "2021\nFEB"),
                    ("202103", "2021\nMAR"),
                    ("202104", "2021\nAPR"),
                    ("202105", "2021\nMAY"),
                    ("202106", "2021\nJUN"),
                    ("202107", "2021\nJUL"),
                    ("202108", "2021\nAUG"),
                    ("202109", "2021\nSEP"),
                    ("202110", "2021\nOCT"),
                    ("202111", "2021\nNOV"),
                    ("202112", "2021\nDEC"),
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



def plot_graph(ms,detection_type,year,ts_clean_cloudfree_unique,crop,out_base_folder,
               parcel_id, add_error_bars, save_figures, fixed_date_range):

    parcel_id_as_filename = convert_string_to_filename(parcel_id)

    if ms == "pt":
        detection_type="green_cover_detection"
    output_graph_folder = out_base_folder + "/" + ms.upper() + "/" + detection_type + "/ndvi_graphs/all_parcels"
    logfile = "ndvi_test.log"

    x_start_date = str(year) + "-01-01"
    x_end_date = str(year) + "-12-31"

    plot_title = ms.upper() + " " + str(year) + " from RESTful"
    ndvi_profile_filtered = ts_clean_cloudfree_unique

    if not ndvi_profile_filtered.empty:
        # sort by date
        ndvi_profile_filtered = ndvi_profile_filtered.sort_values(by=['dateB08'])

        # select the parcel from the geopandas dataframe based on the fid_int column
        # and get real parcel id and crop name and other attributes if needed
        jpg_filename = str(parcel_id_as_filename) + ".jpg"
        saved_figure = display_ndvi_profiles(x_start_date, x_end_date, ndvi_profile_filtered, parcel_id, crop, plot_title,
                                                     output_graph_folder, logfile, jpg_filename,
                                                     add_error_bars, save_figures, fixed_date_range)
        return saved_figure

def convert_string_to_filename(input_string):
    invalid = '<>:"/\|?* '
    if type(input_string) == str:
        for char in invalid:
            input_string = input_string.replace(char, '-')
    else:
        input_string = str(input_string)
    return input_string

def get_crop_name_and_area(ms,year,parcel_id,api_user, api_pass, ptype):

    was_error = True
    while was_error:
        url, parcel_data, was_error = get_parcel_data_from_restful(ms, year, parcel_id, api_user, api_pass, ptype)

    if len(parcel_data):
        crop = parcel_data['cropname'][0]
        area = parcel_data['area'][0]
        parcel_area_ha = area / 10000
        parcel_area_ha_str = str(round(parcel_area_ha,2))
    else:
        crop = ""
        parcel_area_ha_str = ""
    return crop, parcel_area_ha_str, url

def save_ndvi_profile_to_csv(ts_clean_cloudfree_unique, out_csv_folder, parcel_id, crop):
    if not os.path.exists(out_csv_folder):
        os.makedirs(out_csv_folder)
    parcel_id_as_filename = convert_string_to_filename(parcel_id)
    output_df = ts_clean_cloudfree_unique.filter(items=['dateB08', 'ndvi','ndvi_std','countB08'])
    output_df.reset_index(drop=True, inplace=True)
    output_df.rename({'dateB08': 'date', 'countB08':'count'}, axis=1, inplace=True)
    output_df['parcel_id']=parcel_id
    output_df['crop']=crop
    output_df = output_df[[ 'parcel_id','date', 'ndvi', 'ndvi_std', 'count','crop']]
    out_csv_file = out_csv_folder + "/" + str(parcel_id_as_filename) + ".csv"
    output_df.to_csv(out_csv_file, index=False)

def save_radar_profile_to_csv(radar_profile_filtered, out_csv_folder, parcel_id, crop):
    if not os.path.exists(out_csv_folder):
        os.makedirs(out_csv_folder)
    parcel_id_as_filename = convert_string_to_filename(parcel_id)
#    parcel_id,date,ndvi,ndvi_std,count,crop
    # parcel_id,date,meanVV,meanVH,orbit
    output_df = radar_profile_filtered.filter(items=['date', 'band','orbit','mean'])
    output_df['parcel_id']=parcel_id
    output_df['crop']=crop
    output_df = output_df[[ 'parcel_id','date', 'band', 'mean', 'orbit','crop']]
    out_csv_file = out_csv_folder + "/" + str(parcel_id_as_filename) + ".csv"
    output_df.to_csv(out_csv_file, index=False)



def plot_radar_data_orbits_together(output_graph_folder, radar_profile_filtered,
                                           plot_title, fixed_date_range, x_start_date, x_end_date,
                                           parcel_id, separate_orbits, crop, save_figures):

    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)

    # plot the time series
    ax0 = pyplot.gca()

    if not separate_orbits:
        radar_profile_filtered[(radar_profile_filtered["band"]=="VVc")].plot(kind='line', marker='+', x='date',y='mean', label='VV', color = 'lightblue', ax=ax0)
        radar_profile_filtered[(radar_profile_filtered["band"]=="VHc")].plot(kind='line', marker='+', x='date',y='mean', label='VH', color = 'orange', ax=ax0)
    else:
        radar_profile_filtered[(radar_profile_filtered["orbit"]=="D") & (radar_profile_filtered["band"]=="VVc")].plot(kind='line', marker='+', x='date',y='mean', label='VV Desc', ax=ax0)
        radar_profile_filtered[(radar_profile_filtered["orbit"]=="A") & (radar_profile_filtered["band"]=="VVc")].plot(kind='line', marker='+', x='date',y='mean', label='VV Asc', ax=ax0)

        radar_profile_filtered[(radar_profile_filtered["orbit"]=="D") & (radar_profile_filtered["band"]=="VHc")].plot(kind='line', marker='+', x='date',y='mean', label='VH Desc', ax=ax0)
        radar_profile_filtered[(radar_profile_filtered["orbit"]=="A") & (radar_profile_filtered["band"]=="VHc")].plot(kind='line', marker='+', x='date',y='mean', label='VH Asc', ax=ax0)

    # format the graph a little bit
    # we check the first meanVV value and if it is positive we assume it is coherence

    pyplot.ylabel(r'Coherence')


#    pyplot.ylabel(r'Backscattering coefficient, $\gamma\degree$ (dB)')

    pyplot.title(plot_title + ", Parcel id: " + str(parcel_id) + " " + crop)
    # ax0.set_ylim([-0.3,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # vertical lines

    fig = pyplot.gcf()
    fig.autofmt_xdate() # Rotation
    fig_size_x = 13
    fig_size_y = 7
    fig.set_size_inches(fig_size_x, fig_size_y)


    if fixed_date_range:
        x_start_date_date = datetime.datetime.strptime(x_start_date, '%Y-%m-%d').date()
        x_end_date_date = datetime.datetime.strptime(x_end_date, '%Y-%m-%d').date()
        min_month = x_start_date_date.month
        min_year = x_start_date_date.year
        max_month = x_end_date_date.month
        max_year = x_end_date_date.year
        number_of_months = diff_month(x_end_date_date, x_start_date_date) + 1
    else:
        min_month = min(radar_profile_filtered['date']).date().month
        min_year = min(radar_profile_filtered['date']).date().year
        max_month = max(radar_profile_filtered['date']).date().month
        max_year = max(radar_profile_filtered['date']).date().year
        number_of_months = diff_month(max(radar_profile_filtered['date']).date(), min(radar_profile_filtered['date']).date()) + 1

    ax0.set_xlim([datetime.date(min_year, min_month, 1),
                  datetime.date(max_year, max_month,
                                calendar.monthrange(max_year, max_month)[1])])

    min_year_month = str(min_year) + ('0' + str(min_month))[-2:]
    step_x = 1/number_of_months
    start_x = step_x/2               # positions are in graph coordinate system between 0 and 1
                                     # so first year_month label is at half the size of the widht of
                                     # one month
    loc_y = 0.915
    current_year_month_text = get_current_list_of_months(min_year_month, number_of_months)
    for current_year_month_index in range (0, number_of_months):
        t = current_year_month_text[current_year_month_index]
        loc_x = start_x + (current_year_month_index) * step_x
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
                color='blue', fontsize=13)
    ax0.legend()
    ax0.set_ylim([0,1])

#     handles, labels = ax0.get_legend_handles_labels()
#     order = [0,2,1,3]
#     pyplot.legend([handles[idx] for idx in order],[labels[idx] for idx in order])

    # save the figure to a jpg file
    if save_figures:
        parcel_id_as_filename = convert_string_to_filename(parcel_id)
        jpg_filename = str(parcel_id_as_filename) + ".jpg"
        fig.savefig(output_graph_folder + '/' + jpg_filename )
        pyplot.close(fig)
        print("COH6 graph saved to file: " + output_graph_folder + '/' + jpg_filename )
        return(output_graph_folder + '/' + jpg_filename)

def plot_radar_bs_data_orbits_together(output_graph_folder, radar_profile_filtered,
                                           plot_title, fixed_date_range, x_start_date, x_end_date,
                                           parcel_id, separate_orbits, crop, save_figures):


    if not os.path.exists(output_graph_folder):
        os.makedirs(output_graph_folder)

    # plot the time series
    ax0 = pyplot.gca()

    if not separate_orbits:
        radar_profile_filtered[(radar_profile_filtered["band"]=="VVb")].plot(kind='line', marker='+', x='date',y='mean', label='VV', color = 'lightblue', ax=ax0)
        radar_profile_filtered[(radar_profile_filtered["band"]=="VHb")].plot(kind='line', marker='+', x='date',y='mean', label='VH', color = 'orange', ax=ax0)
    else:
        radar_profile_filtered[(radar_profile_filtered["orbit"]=="D") & (radar_profile_filtered["band"]=="VVb")].plot(kind='line', marker='+', x='date',y='mean', label='VV Desc', ax=ax0)
        radar_profile_filtered[(radar_profile_filtered["orbit"]=="A") & (radar_profile_filtered["band"]=="VVb")].plot(kind='line', marker='+', x='date',y='mean', label='VV Asc', ax=ax0)

        radar_profile_filtered[(radar_profile_filtered["orbit"]=="D") & (radar_profile_filtered["band"]=="VHb")].plot(kind='line', marker='+', x='date',y='mean', label='VH Desc', ax=ax0)
        radar_profile_filtered[(radar_profile_filtered["orbit"]=="A") & (radar_profile_filtered["band"]=="VHb")].plot(kind='line', marker='+', x='date',y='mean', label='VH Asc', ax=ax0)

    # format the graph a little bit
    # we check the first meanVV value and if it is positive we assume it is coherence



    pyplot.ylabel(r'Backscattering coefficient, $\gamma\degree$ (dB)')

    pyplot.title(plot_title + ", Parcel id: " + str(parcel_id) + " " + crop)
    # ax0.set_ylim([-0.3,1])
    ax0.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    ax0.xaxis.grid() # horizontal lines
    ax0.yaxis.grid() # vertical lines

    fig = pyplot.gcf()
    fig.autofmt_xdate() # Rotation
    fig_size_x = 13
    fig_size_y = 7
    fig.set_size_inches(fig_size_x, fig_size_y)


    if fixed_date_range:
        x_start_date_date = datetime.datetime.strptime(x_start_date, '%Y-%m-%d').date()
        x_end_date_date = datetime.datetime.strptime(x_end_date, '%Y-%m-%d').date()
        min_month = x_start_date_date.month
        min_year = x_start_date_date.year
        max_month = x_end_date_date.month
        max_year = x_end_date_date.year
        number_of_months = diff_month(x_end_date_date, x_start_date_date) + 1
    else:
        min_month = min(radar_profile_filtered['date']).date().month
        min_year = min(radar_profile_filtered['date']).date().year
        max_month = max(radar_profile_filtered['date']).date().month
        max_year = max(radar_profile_filtered['date']).date().year
        number_of_months = diff_month(max(radar_profile_filtered['date']).date(), min(radar_profile_filtered['date']).date()) + 1

    ax0.set_xlim([datetime.date(min_year, min_month, 1),
                  datetime.date(max_year, max_month,
                                calendar.monthrange(max_year, max_month)[1])])

    min_year_month = str(min_year) + ('0' + str(min_month))[-2:]
    step_x = 1/number_of_months
    start_x = step_x/2               # positions are in graph coordinate system between 0 and 1
                                     # so first year_month label is at half the size of the widht of
                                     # one month
    loc_y = 0.915
    current_year_month_text = get_current_list_of_months(min_year_month, number_of_months)
    for current_year_month_index in range (0, number_of_months):
        t = current_year_month_text[current_year_month_index]
        loc_x = start_x + (current_year_month_index) * step_x
        ax0.text(loc_x, loc_y, t, verticalalignment='bottom', horizontalalignment='center', transform=ax0.transAxes,
                color='blue', fontsize=13)
    ax0.legend()
#    ax0.set_ylim([0,1])

#     handles, labels = ax0.get_legend_handles_labels()
#     order = [0,2,1,3]
#     pyplot.legend([handles[idx] for idx in order],[labels[idx] for idx in order])

    # save the figure to a jpg file
    if save_figures:
        parcel_id_as_filename = convert_string_to_filename(parcel_id)
        jpg_filename = str(parcel_id_as_filename) + ".jpg"
        fig.savefig(output_graph_folder + '/' + jpg_filename )
        pyplot.close(fig)
        print("COH6 graph saved to file: " + output_graph_folder + '/' + jpg_filename )
        return(output_graph_folder + '/' + jpg_filename)
