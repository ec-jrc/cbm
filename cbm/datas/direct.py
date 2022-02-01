#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from cbm.datas import db
from cbm.utils import config
import json


def parcel_by_loc(aoi, year, lon, lat, geom=False):
    values = config.read()
    db = int(values['dataset'][aoi]['db'])
    data = db.getParcelByLocation(aoi, lon, lat, geom, db)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]), [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]), [list(i) for i in zip(*data[1:])])))


def parcel_by_id(aoi, year, pid, geom=False):
    values = config.read()
    db = int(values['dataset'][aoi]['db'])
    data = db.getParcelByID(aoi, year, pid, geom, db)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]), [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]), [list(i) for i in zip(*data[1:])])))


def parcel_by_polygon(aoi, year, polygon, geom=False, only_ids=True):
    values = config.read()
    db = int(values['dataset'][aoi]['db'])
    data = db.getParcelsByPolygon(aoi, polygon, geom, only_ids, db)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]), [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]), [list(i) for i in zip(*data[1:])])))


def parcel_ts(aoi, year, pid, tstype, band=None):
    values = config.read()
    db = int(values['dataset'][aoi]['db'])
    data = db.getParcelTimeSeries(aoi, year, pid, tstype, band, db)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]), [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]), [list(i) for i in zip(*data[1:])])))

    return response


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
#     print(requrl.format(api_url, lon, lat, start_date, end_date))
    response = requests.get(requrl.format(api_url, lon, lat,
                                          start_date, end_date),
                            auth=(api_user, api_pass))
    return response


def rcbl(parcel, start_date, end_date, bands, chipsize, filespath):
    import os
    import sys
    import time
    import rasterio
    import numpy as np
    from pandas import DataFrame
    from osgeo import ogr, osr
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from cbm.datas import object_storage

    start = time.time()
    pid = parcel['pid'][0]
    reference_list = db.getS2frames(pid, start_date, end_date)
    df_polygon = db.getPolygonCentroid(pid)
    json_centroid = json.loads(df_polygon['center'][0])
    # json_polygon = json.loads(df_polygon['polygon'][0])
    parcel_center = json_centroid['coordinates']

    # Download tile images for the parcels.
    # By default the parcels SRID will be used for the target_EPSG.
    # Note the SRID in some cases may not be included in the osr
    # SpatialReference list in those cases a EPSG must be entered below.
    # target_EPSG = 32662
    target_EPSG = db.getSRID('es2019')
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    target = osr.SpatialReference()
    target.ImportFromEPSG(target_EPSG)
    transform = osr.CoordinateTransformation(source, target)
    point = ogr.CreateGeometryFromWkt(
        f"POINT ({parcel_center[1]} {parcel_center[0]})")
    # print("Coordinates before the transform :", point)
    point.Transform(transform)
    # print("Coordinates after the transform  :", point)

    # Size of the chip is 128 times the pixel resolution
    dx = chipsize

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(point.GetX() - dx / 2, point.GetY() + dx / 2)
    ring.AddPoint(point.GetX() - dx / 2, point.GetY() - dx / 2)
    ring.AddPoint(point.GetX() + dx / 2, point.GetY() - dx / 2)
    ring.AddPoint(point.GetX() + dx / 2, point.GetY() + dx / 2)
    ring.AddPoint(point.GetX() - dx / 2, point.GetY() + dx / 2)

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    features = [json.loads(poly.ExportToJson())]

    os.makedirs(os.path.dirname(filespath), exist_ok=True)

    for reference in reference_list:
        ref_img = reference.replace('.SAFE', '')
        s3path, file_info = object_storage.get_file_location(reference)
        dict_list = object_storage.list_files(s3path)
        flist = [file['Key'] for file in dict_list]
        s3subdir = flist[1].replace(s3path, '').split('/')[0]
        # print('s3path: ', s3path)
        # print('s3subdir: ', s3subdir)

        selection = {}
        for b in bands:
            if b in ['B02', 'B03', 'B04', 'B08']:
                r = '10m'
            else:
                r = '20m'
            selection[b] = f"R{r}/{file_info['mgrs_tile']}_{file_info['full_tstamp']}_{b}_{r}.jp2"

        file_set = {}
        try:
            for k in selection.keys():
                s = selection.get(k)
                alt_s = s.replace('0m/', '0m/L2A_')

                # print(s3path, s3subdir)
                if len(object_storage.list_files('{}{}/IMG_DATA/{}'.format(s3path, s3subdir, s))) == 1:
                    # print("Image {} found in bucket".format(s), 1)
                    # print('{}{}/IMG_DATA/{}'.format(s3path,s3subdir,s))
                    file_set[k] = '{}{}/IMG_DATA/{}'.format(
                        s3path, s3subdir, s)
                elif len(object_storage.list_files('{}{}/IMG_DATA/{}'.format(s3path, s3subdir, alt_s))) == 1:
                    # print("Image {} found in bucket".format(alt_s), 2)
                    file_set[k] = '{}{}/IMG_DATA/{}'.format(
                        s3path, s3subdir, alt_s)
                else:
                    print("Neither Image {} nor {} found in bucket".format(s, alt_s))
                    sys.exit(1)

            # Get the chip in this image' footprint
            # bands = file_set.keys()
            chip_set = {}
            with ProcessPoolExecutor(len(bands)) as executor:
                jobs = {}
                for band in bands:
                    job = executor.submit(object_storage.get_subset,
                                          file_set.get(band), features)
                    jobs[job] = band
                for job in as_completed(jobs):
                    band = jobs[job]
                    chip_set[band] = job.result()

            for band in bands:
                os.makedirs(filespath, exist_ok=True)
                fname = f"{filespath}{reference.replace('.SAFE', '')}.{band}.tif"
                img = rasterio.open(fname, 'w', driver='GTiff',
                                    width=chipsize / 10, height=chipsize / 10,
                                    count=1,
                                    crs=target_EPSG,
                                    transform=chip_set.get(band)[1],
                                    dtype=np.uint16
                                    )

                img.write(chip_set.get(band)[0][0, :, :], 1)
                img.close()
            date = reference.split('_')[2].split('T')[0]
            print(f"Images for bands: '{bands}', for the date '{date}'",
                  "are downloaded.")

        # print('{}{}/IMG_DATA/{}'.format(s3path,s3subdir,s))

        except Exception as err:
            print(
                f"! Warning ! Uneble to downloaded image for: {ref_img}\n", err)

    for band in bands:
        dates = [d.split('_')[2] for d in reference_list]
        chips = [
            f"/direct/{chipsize}/{d.replace('.SAFE', '')}.{band}.tif" for d in reference_list]
        band_reflist = [dates, chips]

        df = DataFrame(band_reflist).transpose()
        df.columns = ['dates', 'chips']
        df_file = f'{filespath}images_list.{band}.csv'
        df.to_csv(df_file, index=True, header=True)

    print("\n------Total time------")
    print(f"Total time required for {len(bands)}",
          f"bands: {time.time() - start} seconds")


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
            affine = cbm.transform
            CRS = cbm.crs
            data = cbm.read(1)

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
