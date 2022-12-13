#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import io
import requests
from os.path import join, normpath, isfile

from cbm.utils import config


def get_options(debug=False):
    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/info"""
    response = requests.get(requrl.format(api_url), auth=(api_user, api_pass))
    if debug:
        print(requrl.format(api_url), response)
    return response.content


def parcel_by_loc(aoi, year, lon, lat, ptype=None,
                  geom=False, wgs84=False, debug=False):

    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/parcelByLocation?aoi={}&year={}&lon={}&lat={}"""
    if geom is True:
        requrl = f"{requrl}&withGeometry=True"
    if ptype not in [None, '']:
        requrl = f"{requrl}&ptype={ptype}"
    if wgs84 is True:
        requrl = f"{requrl}&wgs84={wgs84}"
    # print(requrl.format(api_url, aoi, year, lon, lat))
    response = requests.get(requrl.format(api_url, aoi, year, lon, lat),
                            auth=(api_user, api_pass))
    if debug:
        print(requrl.format(api_url, aoi, year, lon, lat), response)
    return response.content


def parcel_by_id(aoi, year, pid, ptype=None, geom=False,
                 wgs84=False, debug=False):
    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/parcelByID?aoi={}&year={}&pid={}"""
    if geom is True:
        requrl = f"{requrl}&withGeometry=True"
    if ptype not in [None, '']:
        requrl = f"{requrl}&ptype={ptype}"
    if wgs84 is True:
        requrl = f"{requrl}&wgs84={wgs84}"
    # print(requrl.format(api_url, aoi, year, pid))
    response = requests.get(requrl.format(api_url, aoi, year, pid),
                            auth=(api_user, api_pass))
    if debug:
        print(requrl.format(api_url, aoi, year, pid), response)
    return response.content


def parcel_by_polygon(aoi, year, polygon, ptype=None, geom=False,
                      wgs84=False, only_ids=True, debug=False):

    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/parcelsByPolygon?aoi={}&year={}&polygon={}"""
    if geom is True:
        requrl = f"{requrl}&withGeometry=True"
    if only_ids is True:
        requrl = f"{requrl}&only_ids=True"
    if ptype not in [None, '']:
        requrl = f"{requrl}&ptype={ptype}"
    if wgs84 is True:
        requrl = f"{requrl}&wgs84={wgs84}"
    response = requests.get(requrl.format(api_url, aoi, year, polygon),
                            auth=(api_user, api_pass))
    if debug:
        print(requrl.format(api_url, aoi, year, polygon), response)
    return response.content


def parcel_peers(aoi, year, pid, distance=1000.0,
                 maxPeers=10, ptype=None, debug=False):
    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/parcelPeers?aoi={}&year={}&pid={}&distance={}&max={}"""
    if ptype not in [None, '']:
        requrl = f"{requrl}&ptype={ptype}"
    response = requests.get(requrl.format(api_url, aoi, year, pid, distance,
                                          maxPeers), auth=(api_user, api_pass))
    if debug:
        print(requrl.format(api_url, aoi, year, pid, distance, maxPeers),
              response)
    return response.content


def parcel_ts(aoi, year, pid, tstype='s2', ptype=None, band='', debug=False):

    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/parcelTimeSeries?aoi={}&year={}&pid={}&tstype={}"""
    if ptype not in [None, '']:
        requrl = f"{requrl}&ptype={ptype}"
    if band not in [None, '']:
        requrl = f"{requrl}&band={band}"
    response = requests.get(requrl.format(api_url, aoi, year,
                                          pid, tstype, band),
                            auth=(api_user, api_pass))
    if debug:
        print(requrl.format(api_url, aoi, year, pid, tstype, band), response)
    return response.content


def parcel_wts(aoi, year, pid, ptype=None, debug=False):

    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/weatherTimeSeries?aoi={}&year={}&pid={}"""
    if ptype not in [None, '']:
        requrl = f"{requrl}&ptype={ptype}"
    response = requests.get(requrl.format(api_url, aoi, year, pid),
                            auth=(api_user, api_pass))
    if debug:
        print(requrl.format(api_url, aoi, year, pid), response)
    return response.content


def cbl(lon, lat, start_date, end_date, bands=None, lut=None, chipsize=None):
    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/chipsByLocation?lon={}&lat={}&start_date={}&end_date={}"""
    band = '_'.join(bands)
    if band is not None:
        requrl = f"{requrl}&band={band}"
    if chipsize is not None:
        requrl = f"{requrl}&chipsize={chipsize}"
    if lut != '':
        requrl = f"{requrl}&lut={lut}"
    # print(requrl.format(api_url, lon, lat, start_date, end_date))
    response = requests.get(requrl.format(api_url, lon, lat,
                                          start_date, end_date),
                            auth=(api_user, api_pass))
    return response


def rcbl(clon, clat, start_date, end_date,
         bands, chipsize, filespath, debug=False):
    """Get parcel raw chip images from RESTful API by location"""
    import os
    import os.path
    import pandas as pd
    import time
    start = time.time()
    api_url, api_user, api_pass = config.credentials('api')

    for band in bands:
        requrl = """{}/query/rawChipByLocation?lon={}&lat={}&start_date={}&end_date={}"""
        if band is not None:
            requrl = f"{requrl}&band={band}"
        if chipsize is not None:
            requrl = f"{requrl}&chipsize={chipsize}"

        response = requests.get(requrl.format(api_url, clon, clat, start_date,
                                              end_date, band, chipsize),
                                auth=(api_user, api_pass)).content
        if debug:
            print("Request url:", requrl.format(
                api_url, clon, clat, start_date, end_date, band, chipsize))
            print("Response:", response)
        # Create a pandas DataFrame from the json response
        df = pd.read_json(io.StringIO(response.decode('utf-8')))
        os.makedirs(filespath, exist_ok=True)

        # Download the GeoTIFFs that were just created in the user cache
        for c in df.chips:
            url = f"{api_url}{c}"
            outf = normpath(join(filespath, c.split('/')[-1]))
            res = requests.get(url, stream=True)
            if debug:
                print(f"Downloading {c.split('/')[-1]}")
            with open(outf, "wb") as handle:
                for chunk in res.iter_content(chunk_size=512):
                    if chunk:  # filter out keep-alive new chunks
                        handle.write(chunk)

        # Sore DataFrame to file
        df_file = normpath(join(filespath, f'images_list.{band}.csv'))
        if isfile(df_file):
            df_old = pd.read_csv(df_file, index_col=[0])
            # df = pd.concat([df, df_old], ignore_index=True)
            df = df.append(df_old, ignore_index=True)
            df = df.drop_duplicates(subset=['chips'])
        df = df.sort_values(by="dates")
        df = df.reset_index(drop=True)
        df.to_csv(df_file, index=True, header=True)
        if debug:
            print(f"Downloaded Images for '{band}'.")
            print(f"The response table is saved to: {df_file}")

    if debug:
        print("\n------Total time------")
        print(f"Total time required for {len(bands)}",
              f"bands: {time.time() - start} seconds.")


def background(lon, lat, chipsize=512, extend=512, tms='Google',
               bg_path='', debug=False):
    """Download the background image.

    Examples:
        background(lon, lat, 512, 512, 'Google', 'temp/test.tif', True)

    Arguments:
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        bg_path, the path of the output file (str).
    """
    # Make the request
    api_url, api_user, api_pass = config.credentials('api')
    params = f"&chipsize={chipsize}&extend={extend}&tms={tms}&iformat=tif"
    requrl = f"{api_url}/query/backgroundByLocation?lon={lon}&lat={lat}{params}"
    response = requests.get(requrl, auth=(api_user, api_pass))

    # Try to download the image
    try:
        img_url = response.content.decode("utf-8")
        if img_url == '{}':
            if debug:
                print("Image not found...")
                print(requrl, response)
            return response
        else:
            if debug:
                print(requrl, response)
            res = requests.get(img_url, stream=True)
            image_name = img_url.split('/')[-1].lower()
            bg_file = normpath(join(bg_path, image_name))

            with open(bg_file, "wb") as handle:
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        handle.write(chunk)
            return bg_file
    except AttributeError as err:
        return err
