#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


"""
Project: Copernicus DIAS for CAP 'checks by monitoring'.

Functions for spatial management and processing.

Options:
    swap_xy
    centroid
    trasform_geometry
  -h, --help    Show this screen.
  --version     Show version.
"""


def swap_xy(geom):
    """
    A general function to swap (x,y) for any spatial geometry type,
    it also preserves z coordinates (if present)

    Exaple code:
        from spatial.geometry import Point, Polygon, MultiPoint, MultiLineString

        # POINT Z (1 2 3) -> POINT Z (2 1 3)
        spatial.swap_xy(Point(1, 2, 3))

        # MULTILINESTRING ((1 2, 3 4)) -> MULTILINESTRING ((2 1, 4 3))
        spatial.swap_xy(MultiLineString([[(1, 2), (3, 4)]]))

        # Map the function to a geopandas geometry column
        table.geometry = table.geometry.map(spatial.swap_xy)
    """
#     print(type(geom))

    def swap_xy_coords(coords):
        if len(coords) == 2:
            x, y = coords
            return [y, x]
        elif len(coords) == 3:
            x, y, z = coords
            return [y, x, z]

    if type(geom) is dict:
        # Process coordinates from each supported geometry type
        if geom['type'] in ('Point', 'LineString', 'LinearRing', 'Polygon'):
            coords_list = geom['coordinates'][0]
            return [swap_xy_coords(coords) for coords in coords_list]
        elif geom['type'].startswith('Multi') or geom['type'] == 'GeometryCollection':
            geom_list = []
            for sub_geom in geom['coordinates'][0]:
                geom_list.append([swap_xy_coords(coords)
                                  for coords in sub_geom])
            return geom_list[0]
        else:
            raise ValueError("Type {geom['type']} not recognized")
            return geom
    elif type(geom) is list:
        if list_depth(geom) == 2:
            coords_list = geom
            return [swap_xy_coords(coords) for coords in coords_list]
        elif list_depth(geom) == 3:
            geom_list = []
            for sub_geom in geom:
                geom_list.append([swap_xy_coords(coords)
                                  for coords in sub_geom])
            return geom_list
    else:
        print("Unrecognized geometry type")


def list_depth(lsit_):
    if isinstance(lsit_, list):
        return 1 + max(list_depth(item) for item in lsit_)
    else:
        return 0


def centroid(geom):
    """
    Args:
        geom: A list of coordinates.
    Returns:
        _x, _y: Coordinates of the center point.
    Raises:
    Example:
    """
    def xy_center(coords_list):
        _x_list = [coords[0] for coords in coords_list]
        _y_list = [coords[1] for coords in coords_list]
        _len = len(coords_list)
        _x = sum(_x_list) / _len
        _y = sum(_y_list) / _len
        return [_x, _y]

#     print(list_depth(geom))
    if list_depth(geom) == 1:
        try:
            geom_ = [list(c) for c in geom]
            _x, _y = xy_center(geom_)
        except Exception:
            pass
    elif list_depth(geom) == 2:
        _x, _y = xy_center(geom)
    elif list_depth(geom) == 3:
        _x, _y = xy_center(geom[0])
    else:
        print("Not recognized coordinates format.")

    return(round(_x, 4), round(_y, 4))


def trasform_geometry(jsondata, target_epsg=4326):
    """
    Args:
        jsondata: Parsel information in json format with geometry.
            Must include srid and geom
    Returns:
        geom_wgs84: json formated geometry in wgs84.
    Raises:
    Example:
    """
    from osgeo import ogr, osr
    import json
    try:
        geom = jsondata['geom'][0]
        g = ogr.CreateGeometryFromJson(geom)
        source = osr.SpatialReference()
        source.ImportFromEPSG(jsondata['srid'][0])
        target = osr.SpatialReference()
        target.ImportFromEPSG(target_epsg)
        transform = osr.CoordinateTransformation(source, target)
        g.Transform(transform)
        geom_wgs84 = json.loads(g.ExportToJson())

        return geom_wgs84
    except Exception as err:
        print("could not transform geometry", err)


def bounds(geotiff):
    import rasterio
    import rasterio.features
    import rasterio.warp
    import numpy as np
    """
    Args:
        geotiff: A tiff type image with georeferencing information.
    Returns:
        img_bounds: The bounds of the geotiff.
    Example:
        (13, -130), (32, -100) # SW and NE corners of the image
    """
    with rasterio.open(geotiff) as dataset:
        # Read the dataset's valid data mask as a ndarray.
        mask = dataset.dataset_mask().astype(np.uint16)

        # Extract feature shapes and values from the array.
        for geom, val in rasterio.features.shapes(
                mask, transform=dataset.transform):

            # Transform shapes from the dataset's own coordinate
            # reference system to CRS84 (EPSG:4326).
            geom = rasterio.warp.transform_geom(
                dataset.crs, 'EPSG:4326', geom, precision=6)

            # Print GeoJSON shapes to stdout.
            img_bounds = ((geom['coordinates'][0][1][1],
                           geom['coordinates'][0][1][0]),
                          (geom['coordinates'][0][3][1],
                           geom['coordinates'][0][3][0]))

    return img_bounds
