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
    # print(requrl.format(api_url, aoi, year, pid))
    response = requests.get(requrl.format(api_url, aoi, year, lon, lat),
                            auth=(api_user, api_pass))
    if debug:
        print(requrl.format(api_url, aoi, year, lon, lat), response)
    return response.content


def parcel_by_id(aoi, year, pid, ptype=None, geom=False,
                 wgs84=False, debug=False):
    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/parcelById?aoi={}&year={}&pid={}"""
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
         quiet=True):
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
        if not quiet:
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
                if not quiet:
                    print(f"Downloading {c.split('/')[-1]}")
                with open(outf, "wb") as handle:
                    for chunk in res.iter_content(chunk_size=512):
                        if chunk:  # filter out keep-alive new chunks
                            handle.write(chunk)
        if not quiet:
            print(
                f"Images for band '{band}', for the selected dates are downloaded.")

    if not quiet:
        print("\n------Total time------")
        print(
            f"Total time required for {len(bands)} bands: {time.time() - start} seconds.")


def clouds(geom):
    import glob
    import json
    import rasterio
    from osgeo import osr
    from rasterstats import zonal_stats
    # Check whether our parcel is cloud free

    # We should have a list of GeoTIFFs ending with .SCL.tif
    tiflist = glob.glob('*.SCL.tif')

    for t in tiflist:
        with rasterio.open(t) as src:
            affine = src.transform
            CRS = src.crs
            data = src.read(1)

        # Reproject the parcel geometry in the image crs
        imageCRS = int(str(CRS).split(':')[-1])

        # Cross check with the projection of the geometry
        # This needs to be done for each image, because the parcel could be in
        # a straddle between (UTM) zones
        geomCRS = int(geom.GetSpatialReference().GetAuthorityCode(None))

        if geomCRS != imageCRS:
            target = osr.SpatialReference()
            target.ImportFromEPSG(imageCRS)
            source = osr.SpatialReference()
            source.ImportFromEPSG(geomCRS)
            transform = osr.CoordinateTransformation(source, target)
            geom.Transform(transform)

        # Format as a feature collection (with only 1 feature)
        # and extract the histogram
        features = {"type": "FeatureCollection",
                    "features": [{"type": "feature",
                                  "geometry": json.loads(geom.ExportToJson()),
                                  "properties": {"pid": pid}}]}
        zs = zonal_stats(features, data, affine=affine, prefix="",
                         nodata=0, categorical=True, geojson_out=True)

        # This has only one record
        properties = zs[0].get('properties')

        # pid was used as a dummy key to make sure the histogram
        # values are in 'properties'
        del properties['pid']

        histogram = {int(float(k)): v for k, v in properties.items()}
        # print(t, histogram)


def get_options():
    api_url, api_user, api_pass = config.credentials('api')
    requrl = """{}/query/options"""
    response = requests.get(requrl.format(api_url),
                            auth=(api_user, api_pass))
    return response.content


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
    # print(f"{api_url}/query/backgroundByLocation?{requrl}&tms={tms}&raw")
    response = requests.get(
        f"{api_url}/query/backgroundByLocation?{requrl}&tms={tms}&raw",
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
                    f"{api_url}/query/backgroundByLocation?{requrl}&tms={tms}&raw", response)
            return response
        else:
            if debug:
                print(
                    f"{api_url}/query/backgroundByLocation?{requrl}&tms={tms}&raw", response)
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
