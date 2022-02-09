#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import os.path
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


def rcbl(parcel, start_date, end_date, bands, chipsize, filespath,
         debug=False):
    """Get parcel raw chip images from RESTful API by location"""
    import os
    import os.path
    import pandas as pd
    from osgeo import osr, ogr
    import time
    start = time.time()
    api_url, api_user, api_pass = config.credentials('api')

    for band in bands:
        requrl = """{}/query/rawChipByLocation?lon={}&lat={}&start_date={}&end_date={}"""
        if band is not None:
            requrl = f"{requrl}&band={band}"
        if chipsize is not None:
            requrl = f"{requrl}&chipsize={chipsize}"

        # Create a valid geometry from the returned JSON withGeometry
        geom = ogr.CreateGeometryFromJson(parcel.get('geom')[0])
        source = osr.SpatialReference()
        source.ImportFromEPSG(parcel.get('srid')[0])

        # Assign this projection to the geometry
        geom.AssignSpatialReference(source)
        target = osr.SpatialReference()
        target.ImportFromEPSG(4326)
        transform = osr.CoordinateTransformation(source, target)

        # And get the lon, lat for its centroid, so that we can center the chips
        # on the parcel
        centroid = geom.Centroid()
        centroid.Transform(transform)

        # Use pid for next request
        # pid = parcel['pid'][0]
        # cropname = parcel['cropname'][0]

        # Set up the rawChip request
        cen_x, cen_y = str(centroid.GetX()), str(centroid.GetY())

        response = requests.get(requrl.format(api_url, cen_y, cen_x, start_date,
                                              end_date, band, chipsize),
                                auth=(api_user, api_pass))
        if debug:
            print("Request url:", requrl.format(
                api_url, cen_y, cen_x, start_date, end_date, band, chipsize))
            print("Geom:", geom)
            print("Source:", source, ", Target:", target)
            print("Centroid", centroid)
            print("Response:", response)
        # Directly create a pandas DataFrame from the json response
        df = pd.read_json(response.content)
        os.makedirs(filespath, exist_ok=True)
        df_file = normpath(join(filespath, f'images_list.{band}.csv'))
        df.to_csv(df_file, index=True, header=True)
        # print(f"The response table is saved to: {df_file}")

        # Download the GeoTIFFs that were just created in the user cache
        for c in df.chips:
            url = f"{api_url}{c}"
            outf = normpath(join(filespath, c.split('/')[-1]))
            if not isfile(outf):
                res = requests.get(url, stream=True)
                if debug:
                    print(f"Downloading {c.split('/')[-1]}")
                with open(outf, "wb") as handle:
                    for chunk in res.iter_content(chunk_size=512):
                        if chunk:  # filter out keep-alive new chunks
                            handle.write(chunk)
        if debug:
            print(
                f"Images for band '{band}', for the selected dates are downloaded.")

    if debug:
        print("\n------Total time------")
        print(
            f"Total time required for {len(bands)} bands: {time.time() - start} seconds.")


def background(lon, lat, chipsize=512, extend=512, tms='Google',
               bg_path='', debug=False):
    # aoi='undefined', year='', pid='0000', quiet=True):
    """Download the background image.

    Examples:
        background(lon, lat, 512, 512, 'Google', 'temp/test.tif', True)

    Arguments:
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        bk_file, the name of the output file (str).
    """

    # Get the api credentials
    api_url, api_user, api_pass = config.credentials('api')

    # The url to get the background image
    requrl = f"lon={lon}&lat={lat}&chipsize={chipsize}&extend={extend}"
    # print(f"{api_url}/query/backgroundByLocation?{requrl}&tms={tms}&iformat=tif")
    response = requests.get(
        f"{api_url}/query/backgroundByLocation?{requrl}&tms={tms}&iformat=tif",
        auth=(api_user, api_pass))
    # print(response)

    # Try to get the image link from the html response
    try:
        img_url = response.content.decode("utf-8")
        # print(type(img_url), img_url)
        if img_url == '{}':
            if debug:
                print("Image not found...")
                print(
                    f"{api_url}/query/backgroundByLocation?{requrl}&tms={tms}&iformat=tif", response)
            return response
        else:
            if debug:
                print(
                    f"{api_url}/query/backgroundByLocation?{requrl}&tms={tms}&iformat=tif", response)
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
