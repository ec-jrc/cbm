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


def swap_xy(indata):
    """
    A general function to swap (x,y) for any spatial geometry type,
    it also preserves z coordinates (if present)

    Exaple code:
        from cbm.utils import spatial_utils
        geom = [[20, 40]]
        spatial_utils.swap_xy(geom)

        # POINT Z (1 2 3) -> POINT Z (2 1 3)
        spatial_utils.swap_xy(Point(1, 2, 3))

        # MULTILINESTRING ((1 2, 3 4)) -> MULTILINESTRING ((2 1, 4 3))
        spatial_utils.swap_xy(MultiLineString([[(1, 2), (3, 4)]]))

        # Map the function to a geopandas geometry column
        table.geometry = table.geometry.map(spatial_utils.swap_xy)
    """
    if type(indata) is str:
        indata = eval(indata)
    if 'geom' in indata:
        if type(indata['geom']) is list:
            geom = indata['geom'][0]
        else:
            geom = indata['geom']
        if geom is str:
            geom = eval(geom)
    else:
        geom = indata

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
            geom['coordinates'][0] = [swap_xy_coords(
                coords) for coords in coords_list]
        elif geom['type'].startswith('Multi') or geom['type'] == 'GeometryCollection':
            geom_list = []
            for sub_geom in geom['coordinates'][0]:
                geom_list.append([swap_xy_coords(coords)
                                  for coords in sub_geom])
                geom['coordinates'] = [geom_list]
        else:
            raise ValueError("Type {geom['type']} not recognized")
        if 'geom' in indata:
            indata['geom'] = geom
            return indata
        else:
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
        elif list_depth(geom) == 4:
            geom_all = []
            for sub_geom in geom[0]:
                geom_list = []
                for sub_geom in geom[0]:
                    geom_list.append([swap_xy_coords(coords)
                                      for coords in sub_geom])
                geom_all.append(geom_list)
            return geom_all
    else:
        print("Unrecognized geometry type")


def list_depth(lsit_):
    if isinstance(lsit_, list):
        return 1 + max(list_depth(item) for item in lsit_)
    else:
        return 0


def centroid(indata):
    """
    Args:
        geom: json data or list with coordinates.
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

    if type(indata) is str:
        indata = eval(indata)
    if 'geom' in indata:
        if type(indata['geom'][0]) is dict:
            geom = indata['geom'][0]['coordinates']
        else:
            indata['geom'][0] = eval(indata['geom'][0])
            geom = indata['geom'][0]['coordinates']
    elif 'coordinates' in indata:
        geom = indata['coordinates']
    elif type(indata) is list:
        geom = indata

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
    elif list_depth(geom) == 4:
        _x, _y = xy_center(geom[0][0])
    else:
        print("Not recognized coordinates format.")

    from osgeo import gdal
    if int(gdal.VersionInfo()) < 3000000:
        return(round(_y, 4), round(_x, 4))
    else:
        return(round(_x, 4), round(_y, 4))


def transform_geometry(indata, target_epsg=4326, source_epsg=None):
    """
    Args:
        indata: json or list with coordinates
        target_epsg default wgs84 (4326)
        source_epsg default None
    Returns:
        geom: json formated geometry in target_epsg.
    Raises:
    Example:
    """
    from osgeo import ogr, osr
    import json
    try:
        if 'geom' in indata:
            geom = indata['geom'][0]
        elif 'coordinates' in indata:
            geom = indata
        elif type(indata) is list:
            geom = {}
            geom['type'] = 'MultiPolygon'
            geom['coordinates'] = indata
            geom = str(geom)

        g = ogr.CreateGeometryFromJson(geom)
        source = osr.SpatialReference()

        if 'srid' in indata:
            source.ImportFromEPSG(indata['srid'][0])
        elif source_epsg is not None:
            source.ImportFromEPSG(source_epsg)
        else:
            print("Please provide source srid.")

        target = osr.SpatialReference()
        target.ImportFromEPSG(target_epsg)
        transform = osr.CoordinateTransformation(source, target)
        g.Transform(transform)
        geom_target = json.loads(g.ExportToJson())

        if 'geom' in indata:
            indata['geom'][0] = geom_target
            return indata
        else:
            return geom_target
    except Exception as err:
        print("Could not transform geometry: ", err)
        return indata
