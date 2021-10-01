#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Gilbert Voican, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import psycopg2
# from psycopg2 import Error
import subprocess
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from rasterstats import zonal_stats
from fiona import open as fopen
import fiona
from yaml import load, FullLoader
from os.path import dirname, abspath, join, normpath
from pathlib import Path

from cbm.utils import config
from cbm.datas import db

import geopandas as gpd

path_foi_func = normpath(join(dirname(abspath(__file__)), 'foi_db_func'))


def main(reference_data, raster_classif_file, yaml_file, pre_min_het,
         pre_max_het, area_threshold, db_str='main'):
    """FOI assessment is based on spatial analysis of a “thematic” raster
    produced in advance.

    The thematic raster can be the result of a any image/raster processing
    method yielding a class label for each pixel - crop classification, behavior
    analysis of land phenomenon, gridded data on soil, slope, humidity, etc.
    The starting point was the idea that inside of an homgeneous parcel we
    should have only one type of pixel.
    For example if the thematic raster is the result of a crop classification,
    inside a parcel we should have only one type of pixels that represent the
    respective crop
    If the thematic raster is the result of a behaviour analysis, all the pixels
    inside a parcel should behave in the same way during a period of time.
    The FOI assessment is based on the analysis made on the presence and
    distribution of different types of pixels inside the FOI.

    Args:
        reference_data (str): Spatial data to be tested -
            parcels that will be checked for heterogeneity and cardinality
            The parcels poligons in .shp file format or
            database table name without .shp ending.
        raster_classif_file (str): Thematic raster - classification raster, or
            raster from other source that will be used for testing
            heterogeneity and cardinality
        yaml_file: YAML file that holds the classes of thematic raster file.
            can be also a simple list of values in the notebook corespondence
            between pixel values and names for the classes
        pre_min_het: Minimum thresholds for heterogeneity checks.
        pre_max_het: Maximum thresholds for heterogeneity checks.
        area_threshold: Minimum area for clusters selection.

    Returns:
        bool: True if successful, False otherwise.

    """

    # database connection string
    if type(db_str) is str:
        db_connection = f"PG:{db.conn_str(db_str)}"
    elif type(db_str) is list:
        db_connection = "PG:host={} port={} dbname={} user={} password={}".format(
            *db_str)

    def db_conn():
        if type(db_str) is str:
            return db.conn(db_str)
        elif type(db_str) is list:
            return psycopg2.connect("host={} port={} dbname={} user={} password={}".format(*db_str))

    # ogr2ogr options
    geom_field_name = "GEOMETRY_NAME=wkb_geometry"
    overwrite_option = "-OVERWRITE"
    geom_type = "MULTIPOLYGON"
    output_format = "PostgreSQL"

    # Path for storing the processed data - final spatial data that will be
    #    exported after database processing
    processed_data = normpath(join('foi', 'processed_data'))
    os.makedirs(processed_data, exist_ok=True)

    # Path for storing the final output data
    output_data = normpath(join('foi', 'output_data'))
    os.makedirs(output_data, exist_ok=True)
    reference_data_name = os.path.splitext(os.path.basename(reference_data))[0]
    try:
        with open(f"{config.get_value(['paths','temp'])}tb_prefix", 'r') as f:
            reference_data_table = f.read()
    except Exception:
        reference_data_table = reference_data_name

    # Vector file resulted from the raster stats pixel count
    # pixelcount_output = f'{output_data}pixel_count_{reference_data_table}.shp'

    pixelcount_output = f'{processed_data}/{reference_data_name}_pixelcount.shp'
    # Vector file resulted from raster to vector process (polygonize)
    polygonize_output = f'{processed_data}/{reference_data_name}_polygonize.shp'

    # Name of the table to be created in the database - import of the pixel
    #   count into the database
    pixelcount_table = f"{reference_data_name}_pixelcount"
    # Name of the table to be created in the database - import of the
    #   polygonize result into the database
    polygonize_table = f"{reference_data_name}_polygonize"

    # Name and path of the files resulted from the analysis
    heterogeneity_output = f'{output_data}/{reference_data_name}_foih_v1.shp'
    cardinality_output = f'{output_data}/{reference_data_name}_foic_v1.shp'
    cardinality_output_clusters = f'{output_data}/{reference_data_name}_foic_clusters_v1.shp'

    sql = "SELECT * FROM " + reference_data_table + ";"
    try:
        ps_connection = db_conn()

        ps_connection.autocommit = True

        cursor = ps_connection.cursor()

        gpd_data = gpd.read_postgis(
            sql=sql, con=ps_connection, geom_col='wkb_geometry')

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        # closing database connection.
        if(ps_connection):
            cursor.close()
            ps_connection.close()
            # print("PostgreSQL connection is closed")

    temp_reference_data = f'foi/{reference_data_name}_temp.shp'

    gpd_data.to_file(temp_reference_data)

    shape = fiona.open(temp_reference_data)
    spatialRef = shape.crs["init"]
#     print("Vector EPSG: ", spatialRef)

    # Import reference data shapefile to database.
    # Overwrite option is needed, otherwise the import will append new
    # values to the ones existing in the table
    subprocess.call(["ogr2ogr", overwrite_option, "-nlt", geom_type, "-lco",
                     geom_field_name, "-a_srs", spatialRef, "-nln",
                     reference_data_table, "-f", "PostgreSQL", db_connection,
                     reference_data])

    # Reading the values from yaml file
    conf = load(open(yaml_file, 'r').read(), Loader=FullLoader)
    category_map = conf['category_map']
    rst_fields = list(category_map.values())

    # Counting the number of pixels for each parcel. The fields with names of
    #   the classes from yaml file will be added,
    # and updated with the number of pixels from each category
    with fopen(temp_reference_data, 'r') as input:
        spatialRef = input.crs["init"]
        schema = input.schema

        for i in rst_fields:
            schema['properties'][i] = 'int:5'

        rst_attribs = dict.fromkeys(rst_fields, 0)

        with fopen(pixelcount_output, 'w', 'ESRI Shapefile', schema) as output:
            for i, vct_feat in enumerate(input):
                vct_val_dict = dict(vct_feat['properties'])
                rst_val_dict = zonal_stats(
                    vct_feat, raster_classif_file,
                    categorical=True, copy_properties=True,
                    category_map=category_map, nodata=-999)[0]
                vct_val_dict.update(rst_attribs)

                for lu in rst_val_dict:
                    vct_val_dict[lu] = rst_val_dict.get(lu)

                for atrib in vct_val_dict:
                    vct_feat['properties'][atrib] = vct_val_dict.get(atrib)

                output.write(vct_feat)
    print("Finished pixel calculation!")

    # Import resulted shapefile, with the number of pixels for each class to
    #   database. Overwrite option is needed, otherwise the
    # import will append new values to the ones existing in the table
    subprocess.call(["ogr2ogr", overwrite_option, "-nlt", geom_type, "-a_srs",
                     spatialRef, "-nln",  pixelcount_table, "-f", "PostgreSQL",
                     db_connection,  pixelcount_output])

    # Number of classes from the thematic raster
    num_classes = len(category_map)
    # Minimum and maximum thresholds for heterogeneity checks. In this example,
    #   any parcel
    # with percentage of pixels for one class between 30 and 70 from the total,
    #   will be considered heterogenous.
    # min_heterogeneity_threshold = 30
    # max_heterogeneity_threshold = 70
    min_heterogeneity_threshold = pre_min_het
    max_heterogeneity_threshold = pre_max_het

    # Calling the PostgreSQL function wich checks the heterogeneity.
    # The function calculates the percentages and sets an attribute
    # "foi_h" to 1 when the percentage of pixels is between thresholds
    try:
        ps_connection = db_conn()

        ps_connection.autocommit = True

        cursor = ps_connection.cursor()

        # call stored procedure
        cursor.callproc('public.check_heterogeneity', (
            pixelcount_table, num_classes, min_heterogeneity_threshold,
            max_heterogeneity_threshold))

        print("Running function to check heterogeneity")

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        # closing database connection.
        if(ps_connection):
            cursor.close()
            ps_connection.close()
            print("PostgreSQL connection is closed")
    print("Heterogeneity assessment function finished")

    # Export processed data - heterogeneity, to shapefile
    subprocess.call(["ogr2ogr", "-f", "ESRI Shapefile",
                     heterogeneity_output, db_connection, pixelcount_table])
    print("Heterogeneity analysis output downloaded")

    # Polygonize the thematic raster. The process takes into account only
    #   one band (in this case - first band). Can be used with 8 connected
    #   pixels or with 4 connected pixels.
    connectedness = '-8'
    sourceRaster = gdal.Open(raster_classif_file)
    band = sourceRaster.GetRasterBand(1)
    srs = osr.SpatialReference(wkt=sourceRaster.GetProjection())
    dst_layername = polygonize_output
    drv = ogr.GetDriverByName("ESRI Shapefile")
    dst_ds = drv.CreateDataSource(dst_layername)
    dst_layer = dst_ds.CreateLayer(dst_layername, srs=srs)
    fd = ogr.FieldDefn("DN", ogr.OFTInteger)
    dst_layer.CreateField(fd)
    dst_field = dst_layer.GetLayerDefn().GetFieldIndex("DN")
    gdal.Polygonize(band, None, dst_layer, dst_field,
                    [connectedness], callback=None)
    dst_ds.Destroy()

    # Import polygonize result to database
    subprocess.call(["ogr2ogr", overwrite_option, "-nlt", geom_type, "-lco",
                     geom_field_name, "-nln",  polygonize_table, "-f",
                     output_format, db_connection,  polygonize_output])

    # Names of the tables to be created in the database during the processing
    processed_clusters = polygonize_table + "_clusters"
    processed_cardinality = polygonize_table + "_cardin"
    # Spatial data to be tested - parcels that will be checked for cardinality
    #   (I think we should use the same data as for heterogeneity)
    # reference_table = 'reference_data'
    # Minimum area for clusters selection - only clusters bigger that the
    #   threshold will be counted
    # area_threshold = 2000

    # Calling the PostgreSQL function wich checks the cardinality. The function
    #   fixes the geometry for the spatial data resulted from polygnize, clips
    #   the polygonize result with the parcels that needs to be checked,
    #   calculates the area of the clusters inside each parcel, selects the
    #   clusters that are more than one type, each of them bigger that the
    #   threshold, in each parcel.
    # The function creates two new tables: one with the clusters that matches
    #   the conditions, the other with data to be tested and a new column
    #   "foi_c" wich is 1 if the parcel has more that two types of clusters
    #   with the area bigger than the thershold

    # TO DO: put the unique identifier as function param

    try:
        ps_connection = db_conn()

        ps_connection.autocommit = True

        cursor = ps_connection.cursor()

        # call stored procedure
        # cursor.callproc('public.check_cardinality', (
        #     polygonize_table, reference_data_table, area_threshold))
        cursor.execute(
            "CALL public.check_cardinality_procedure( %s, %s, %s, %s); ",
            (polygonize_table, reference_data_table, area_threshold, 10000))

        print("Running function to check cardinality")

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        # closing database connection.
        if(ps_connection):
            cursor.close()
            ps_connection.close()
            print("PostgreSQL connection is closed")

    # Export processed data - clusters, to shapefile
    subprocess.call(["ogr2ogr", "-f", "ESRI Shapefile",
                     cardinality_output_clusters, db_connection,
                     processed_clusters])
    print("Cardinality assessment function finished")

    # Export processed data - data to be tested with "foi_c" flag, to shapefile
    subprocess.call(["ogr2ogr", "-f", "ESRI Shapefile",
                     cardinality_output, db_connection, processed_cardinality])
    print("Cardinality analysis output downloaded")

    filelist_temp = [f for f in os.listdir(
        'foi') if f.startswith(Path(temp_reference_data).stem)]
    for f in filelist_temp:
        os.remove(os.path.join('foi', f))


if __name__ == "__main__":
    import sys
    main(sys.argv)
