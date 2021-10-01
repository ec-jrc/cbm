#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Gilbert Voican
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
# from pathlib import Path
import time
from osgeo import gdal, gdalnumeric, ogr, osr
from PIL import Image, ImageDraw
import numpy as np
import fiona
# import shapely
from shapely import geometry
from shapely.geometry import shape, mapping, Polygon, Point
import rasterio
import rasterio.mask
from rasterstats import zonal_stats

import cv2
from matplotlib import pyplot as plt
from yaml import load, FullLoader

import csv
from itertools import zip_longest

from cbm.utils import config


def clip_raster(rast, feature, gt=None, nodata=-1):
    '''
    Clips a raster (given as either a gdal.Dataset or as a numpy.array
    instance) to a polygon layer provided by a Shapefile (or other vector
    layer). If a numpy.array is given, a "GeoTransform" must be provided
    (via dataset.GetGeoTransform() in GDAL). Returns an array. Clip features
    must be a dissolved, single-part geometry (not multi-part). Modified from:

    http://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html
    #clip-a-geotiff-with-shapefile

    Arguments:
        rast            A gdal.Dataset or a NumPy array
        features_path   The path to the clipping features
        gt              An optional GDAL GeoTransform to use instead
        nodata          The NoData value; defaults to -9999.
    '''
    def array_to_image(a):
        '''
        Converts a gdalnumeric array to a Python Imaging Library (PIL) Image.
        '''
        i = Image.fromstring('L', (a.shape[1], a.shape[0]),
                             (a.astype('b')).tostring())
        return i

    def image_to_array(i):
        '''
        Converts a Python Imaging Library (PIL) array to a gdalnumeric image.
        '''
        a = gdalnumeric.fromstring(i.tobytes(), 'b')
        a.shape = i.im.size[1], i.im.size[0]
        return a

    def world_to_pixel(geo_matrix, x, y):
        '''
        Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
        the pixel location of a geospatial coordinate; from:
        http://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html#clip-a-geotiff-with-shapefile
        '''
        ulX = geo_matrix[0]
        ulY = geo_matrix[3]
        xDist = geo_matrix[1]
        yDist = geo_matrix[5]
        rtnX = geo_matrix[2]
        rtnY = geo_matrix[4]
        pixel = int((x - ulX) / xDist)
        line = int((ulY - y) / xDist)
        return (pixel, line)

    # Can accept either a gdal.Dataset or numpy.array instance
    if not isinstance(rast, np.ndarray):
        gt = rast.GetGeoTransform()
        rast = rast.ReadAsArray()

    # Convert the layer extent to image pixel coordinates
    minX, minY, maxX, maxY = shape(feature['geometry']).bounds
    ulX, ulY = world_to_pixel(gt, minX, maxY)
    lrX, lrY = world_to_pixel(gt, maxX, minY)

    # Calculate the pixel size of the new image
    pxWidth = int(lrX - ulX)
    pxHeight = int(lrY - ulY)

    # If the clipping features extend out-of-bounds and ABOVE the raster...
    if gt[3] < maxY:
        # In such a case... ulY ends up being negative--can't have that!
        iY = ulY
        ulY = 0

    # Multi-band image?
    try:
        clip = rast[:, ulY:lrY, ulX:lrX]

    except IndexError:
        clip = rast[ulY:lrY, ulX:lrX]

    # Create a new geomatrix for the image
    gt2 = list(gt)
    gt2[0] = minX
    gt2[3] = maxY

    # Map points to pixels for drawing the boundary on a blank 8-bit,
    #   black and white, mask image.
    points = []
    pixels = []
    pts = feature["geometry"]["coordinates"][0]

    for p in pts:
        pixels.append(world_to_pixel(gt2, p[0], p[1]))

    raster_poly = Image.new('L', (pxWidth, pxHeight), 1)
    rasterize = ImageDraw.Draw(raster_poly)
    rasterize.polygon(pixels, 0)  # Fill with zeroes

    # If the clipping features extend out-of-bounds and ABOVE the raster...
    if gt[3] < maxY:
        # The clip features were "pushed down" to match the bounds of the
        #   raster; this step "pulls" them back up
        premask = image_to_array(raster_poly)
        # We slice out the piece of our clip features that are "off the map"
        mask = np.ndarray(
            (premask.shape[-2] - abs(iY), premask.shape[-1]), premask.dtype)
        mask[:] = premask[abs(iY):, :]
        mask.resize(premask.shape)  # Then fill in from the bottom

        # Most importantly, push the clipped piece down
        gt2[3] = maxY - (maxY - gt[3])

    else:
        mask = image_to_array(raster_poly)

    # Clip the image using the mask
    try:
        clip = gdalnumeric.choose(mask, (clip, nodata))

    # If the clipping features extend out-of-bounds and BELOW the raster...
    except ValueError:
        # We have to cut the clipping features to the raster!
        rshp = list(mask.shape)
        if mask.shape[-2] != clip.shape[-2]:
            rshp[0] = clip.shape[-2]

        if mask.shape[-1] != clip.shape[-1]:
            rshp[1] = clip.shape[-1]

        mask.resize(*rshp, refcheck=False)

        clip = gdalnumeric.choose(mask, (clip, nodata))

    return clip


def main(vector_file, raster_file, yaml_file, negative_buffer,
         min_heterogeneity_threshold, max_heterogeneity_threshold,
         connectivity_option, cluster_threshold):

    # Spatial data to be tested - parcels that will be checked for heterogeneity
    #   and cardinality
    reference_data = vector_file

    # Thematic raster - classification raster, or raster from other
    # source that will be used for testing heterogeneity and cardinality
    raster_classif_file = raster_file

    # Path for storing the processed data - final spatial data that will be
    #   exported after database processing
    processed_data = f'foi/processed_data/'
    os.makedirs(processed_data, exist_ok=True)

    output_data = f'foi/output_data/'
    os.makedirs(output_data, exist_ok=True)

    raster_name = os.path.splitext(os.path.basename(raster_file))[0]
    reference_data_name = os.path.splitext(os.path.basename(reference_data))[0]

    if negative_buffer != 0:
        output_foic_name = f'{output_data}' + reference_data_name + \
            '_negative_buffer_' + str(abs(negative_buffer)) + '_foic_v2.shp'
        output_foih_name = f'{output_data}' + reference_data_name + \
            '_negative_buffer_' + str(abs(negative_buffer)) + '_foih_v2.shp'
        csv_foic_name = f'{output_data}' + reference_data_name + \
            '_negative_buffer_' + \
            str(abs(negative_buffer)) + '_skipped_foic.csv'
        csv_foih_name = f'{output_data}' + reference_data_name + \
            '_negative_buffer_' + \
            str(abs(negative_buffer)) + '_skipped_foih.csv'
    else:
        output_foic_name = f'{output_data}' + \
            reference_data_name + '_foic_v2.shp'
        output_foih_name = f'{output_data}' + \
            reference_data_name + '_foih_v2.shp'
        csv_foic_name = f'{output_data}' + \
            reference_data_name + '_skipped_foic.csv'
        csv_foih_name = f'{output_data}' + \
            reference_data_name + '_skipped_foih.csv'

    # raster_classif_file = raster_folder + "/" + raster_file
    # reference_data_file = vector_data_folder / vector_file
    # yaml_file = vector_data_folder / yaml_file_name
    # output_foic_file = output_data_folder / output_foic_name
    # output_foih_file = output_data_folder / output_foih_name
    # csv_foic_file = output_data_folder / csv_foic_name
    # csv_foih_file = output_data_folder / csv_foih_name

    # Reading the values from yaml file
    conf = load(open(yaml_file, 'r').read(), Loader=FullLoader)
    category_map = conf['category_map']
    raster_fields = list(category_map.values())
    raster_classes = list(conf['category_map'].keys())

    raster_classif = gdal.Open(raster_classif_file)
    # Get raster extent
    ulx, xres, xskew, uly, yskew, yres = raster_classif.GetGeoTransform()
    lrx = ulx + (raster_classif.RasterXSize * xres)
    lry = uly + (raster_classif.RasterYSize * yres)

    p1 = geometry.Point(ulx, lry)
    p2 = geometry.Point(lrx, lry)
    p3 = geometry.Point(lrx, uly)
    p4 = geometry.Point(ulx, uly)

    pointList = [p1, p2, p3, p4, p1]

    rasterExtent = geometry.Polygon([[p.x, p.y] for p in pointList])

    start = time.time()
    if(raster_classif.RasterCount == 1):
        skipped_parcels = []
        non_overlapping_parcels = []
        non_overlapping_buffered_parcels = []
        zero_pixels_parcels = []
        buffer_error_parcels = []
        with fiona.open(reference_data) as input:
            spatialRef = input.crs["init"]
            schema = input.schema
            nonCardinalParcels = []
            schema['properties']['foi_c'] = 'str:5'
            schema['properties']['clusters'] = 'str:250'
            with fiona.open(output_foic_name, 'w', driver="ESRI Shapefile",
                            schema=schema, crs=spatialRef) as output_foic:
                for feat in input:
                    geom_initial = shape(feat['geometry'])
                    geom = geom_initial.buffer(negative_buffer)
                    if geom.is_empty:
                        buffer_error_parcels.append(
                            int(list(feat['properties'].values())[0]))
                        print("Feature with id", int(list(feat['properties'].values())[
                              0]), "cannot be buffered due to its size/shape and it will be skipped")
                        continue
                    if not rasterExtent.intersects(geom) and negative_buffer == 0:
                        non_overlapping_parcels.append(
                            int(list(feat['properties'].values())[0]))
                        print("Feature with id", list(feat['properties'].values())[
                              0], "does not overlap with supplied raster")
                        continue
                    if not rasterExtent.intersects(geom) and negative_buffer != 0:
                        non_overlapping_buffered_parcels.append(
                            int(list(feat['properties'].values())[0]))
                        print("Buffered feature with id", int(list(feat['properties'].values())[
                              0]), "does not overlap with supplied raster")
                        continue
                    try:
                        tempImage = np.uint8(clip_raster(
                            raster_classif, feat, None, -1))
                    except:
                        zero_pixels_parcels.append(
                            int(list(feat['properties'].values())[0]))
                        print("Feature with id", list(feat['properties'].values())[
                              0], "produced a zero pixels image due to its size/shape and it will be skipped")
                        continue
                    feat['geometry'] = mapping(geom)
                    clusterNumber = 0
                    cardinalityFlag = 0
                    clustersRecord = []
                    for cls in raster_classes:
                        cloneTempImage = tempImage.copy()
                        cloneTempImage[cloneTempImage != cls] = 0
                        nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(
                            cloneTempImage, connectivity_option)
                        for i in range(nb_components - 1):
                            if nb_components - 1 > 0 and stats[1:][i][4] > cluster_threshold:
                                clustersRecord.append((cls, stats[1:][i][4]))
                                clusterNumber += 1
                        if clusterNumber > 1:
                            nonCardinalParcels.append(
                                feat['properties']['OBJECTID'])
                            cardinalityFlag = 1
                        feat['geometry'] = mapping(geom_initial)
                        feat['properties']['foi_c'] = cardinalityFlag
                        feat['properties']['clusters'] = str(
                            clustersRecord).strip('[]')
                    output_foic.write(feat)

        d = [buffer_error_parcels, zero_pixels_parcels,
             non_overlapping_parcels, non_overlapping_buffered_parcels]
        export_data = zip_longest(*d, fillvalue='')
        with open(csv_foic_name, "w") as f:
            writer = csv.writer(f)
            writer.writerow(("Buffer_error", "Zero pixels",
                             "Non overlapping", "Buffered non overlapping"))
            writer.writerows(export_data)
        f.close()
    else:
        print("Selected raster cannot be used in analisys")

    # Counting the number of pixels for each parcel. The fields with names of
    #   the classes from yaml file will be added,
    # and updated with the number of pixels from each category
    if(raster_classif.RasterCount == 1):
        non_overlapping_parcels = []
        non_overlapping_buffered_parcels = []
        buffer_error_parcels = []
        zero_pixels_parcels = []
        with fiona.open(reference_data, 'r') as input:
            spatialRef = input.crs["init"]
            schema = input.schema
            schema['properties']['foi_h'] = 'int:5'
            raster_fields_percentage = []
            for i in raster_fields:
                percentage = 'P_' + i
                schema['properties'][i] = 'int:5'
                schema['properties'][percentage] = 'float'
                raster_fields_percentage.append(percentage)

            rst_attribs = dict.fromkeys(raster_fields, 0)
            rst_attribs_percentage = dict.fromkeys(raster_fields_percentage, 0)

            with fiona.open(output_foih_name, 'w',  driver="ESRI Shapefile",
                            schema=schema, crs=spatialRef) as output_foih:
                for i, vct_feat in enumerate(input):
                    vct_val_dict = dict(vct_feat['properties'])

                    geom_initial = shape(vct_feat['geometry'])
                    geom = geom_initial.buffer(negative_buffer)
                    # check if feature can be buffered
                    if geom.is_empty:
                        buffer_error_parcels.append(
                            int(list(vct_feat['properties'].values())[0]))
                        print("Feature with id", int(list(vct_feat['properties'].values())[
                              0]), "cannot be buffered due to its size/shape and it will be skipped")
                        continue
                    # check if feature or buffered feature overlaps the thematic raster
                    if not rasterExtent.intersects(geom) and negative_buffer == 0:
                        non_overlapping_parcels.append(
                            int(list(vct_feat['properties'].values())[0]))
                        print("Feature with id", int(list(vct_feat['properties'].values())[
                              0]), "does not overlap with supplied raster")
                        continue
                    elif not rasterExtent.intersects(geom) and negative_buffer != 0:
                        non_overlapping_buffered_parcels.append(
                            int(list(vct_feat['properties'].values())[0]))
                        print("Buffered feature with id", int(list(vct_feat['properties'].values())[
                              0]), "does not overlap with supplied raster")
                        continue

                    vct_feat['geometry'] = mapping(geom)

                    rst_val_dict = zonal_stats(vct_feat, raster_classif_file,
                                               categorical=True, copy_properties=True,
                                               category_map=category_map, nodata=0)[0]
                    # check if the feature or the bufferd feature overlaps pixels from other class than nodata
                    if len(rst_val_dict) == 0 and negative_buffer == 0:
                        zero_pixels_parcels.append(
                            int(list(vct_feat['properties'].values())[0]))
                        print("Feature with id", int(list(vct_feat['properties'].values())[
                              0]), "does not include non-nodata pixels and it will be skipped")
                        continue
                    if len(rst_val_dict) == 0 and negative_buffer != 0:
                        zero_pixels_parcels.append(
                            int(list(vct_feat['properties'].values())[0]))
                        print("Buffered feature with id", int(list(vct_feat['properties'].values())[
                              0]), "does not include non-nodata pixels and it will be skipped")
                        continue

                    vct_feat['geometry'] = mapping(geom_initial)
                    vct_val_dict.update(rst_attribs)
                    vct_val_dict.update(rst_attribs_percentage)
                    vct_val_dict['foi_h'] = 0

                    for lu in rst_val_dict:
                        if (rst_val_dict.get(lu) / sum(rst_val_dict.values()) * 100 >= min_heterogeneity_threshold
                                and rst_val_dict.get(lu) / sum(rst_val_dict.values()) * 100 <= max_heterogeneity_threshold):
                            vct_val_dict['foi_h'] = 1

                        vct_val_dict[lu] = rst_val_dict.get(lu)
                        vct_val_dict['P_' + lu] = (
                            "%.2f" % (rst_val_dict.get(lu) / sum(rst_val_dict.values()) * 100))

                    for atrib in vct_val_dict:
                        vct_feat['properties'][atrib] = vct_val_dict.get(atrib)

                    output_foih.write(vct_feat)

        d = [buffer_error_parcels, zero_pixels_parcels,
             non_overlapping_parcels, non_overlapping_buffered_parcels]
        export_data = zip_longest(*d, fillvalue='')
        with open(csv_foih_name, "w") as f:
            writer = csv.writer(f)
            writer.writerow(("Buffer_error", "Zero pixels",
                             "Non overlapping", "Bufferd non overlapping"))
            writer.writerows(export_data)
        f.close()

    else:
        print("Selected raster cannot be used in analisys")

    print("Analysis finished!")


if __name__ == "__main__":
    main()
