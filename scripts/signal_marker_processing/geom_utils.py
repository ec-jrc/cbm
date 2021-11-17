#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Authors    : Daniele Borio, Csaba WIRNHARDT
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import geopandas as gpd
import numpy as np
from shapely import geometry

import matplotlib.pyplot as plt
import math

import warnings


def min_area_rect( polygon, changeCrs = True ) :
    """
    Summary:
        Function that determines oriented rectangle with minimum area and 
        covering the polygon provided as input
        
    Arguments:
        polygon - polygon provided as GeoSeries with a single element        
        changeCrs - tell if a change to a rectangular crs is needed
        
    Returns:
        rect - polygon provided as GeoSeries with a single element

    """
    
    # First convert the polygon to a 'rectangular' CRS
    # Here, it is assumed that polygons corresponds to parcels from Europe
    if changeCrs :
        rec_polygon = polygon.geometry.to_crs("EPSG:3035")
    else :
        rec_polygon = polygon.geometry
    
    # Use the shapely function minimum_rotated_rectangle
    poly = rec_polygon.geometry.iloc[0].minimum_rotated_rectangle
    rect = gpd.GeoSeries(poly, crs=rec_polygon.crs )
    
    return rect

def extreme_side_ratio( polygon, changeCrs = True ) :
    """
    Summary:
        Compute the ratio between the largest and smallest sides of a polygon
        
    Arguments:
        polygon - polygon provided as GeoSeries with a single element        
        changeCrs - tell if a change to a rectangular crs is needed
        
    Returns:
        ratio - ratio between the largest and smallest sides of a polygon
    """
    
    if changeCrs :
        rec_polygon = polygon.geometry.to_crs("EPSG:3035")
    else :
        rec_polygon = polygon.geometry
    
    # Get the coordinates of  the complex hull
    edges = np.asarray( rec_polygon.geometry.iloc[0].convex_hull.exterior.coords.xy ).T
    
    # Compute the side lengths
    sides = edges[1:] - edges[:-1]
    sidelen = np.sqrt( np.dot(sides**2, np.ones((2,1))) ).flatten()
    
    # return the ratio of the longest and shortes sides
    ratio = min(sidelen) / max(sidelen)
    
    return ratio

def get_area( polygon, changeCrs = True ) :
    """
    Summary:
        Return the area of a polygon
        
    Arguments:
        polygon - polygon provided as GeoSeries with a single element        
        changeCrs - tell if a change to a rectangular crs is needed
        
    Returns:
        area - area of the polygon
    """
    
    if changeCrs :
        rec_polygon = polygon.geometry.to_crs("EPSG:3035")
    else :
        rec_polygon = polygon.geometry
    
    return rec_polygon.area.iloc[0]

def get_perimeter( polygon, changeCrs = True ) :
    """rec_polygon.length.iloc[0]
    Summary:
        Return the perimeter of a polygon
        
    Arguments:
        polygon - polygon provided as GeoSeries with a single element        
        changeCrs - tell if a change to a rectangular crs is needed
        
    Returns:
        perimeter - perimeter of the polygon
    """
    
    if changeCrs :
        rec_polygon = polygon.geometry.to_crs("EPSG:3035")
    else :
        rec_polygon = polygon.geometry
    
    return rec_polygon.length.iloc[0]

def get_shape_index( polygon, changeCrs = True ) :
    """
    Summary:
        Return the perimeter of a polygon
        
    Arguments:
        polygon - polygon provided as GeoSeries with a single element        
        changeCrs - tell if a change to a rectangular crs is needed
        
    Returns:
        si - the shape index of the polygon
        
    Notes:
        The definition of the shape indexes can be found in 
        Demetris Demetriou, Linda See and John Stillwell
        "A Parcel Shape Index for Use in Land Consolidation Planning"
    """
    if changeCrs :
        rec_polygon = polygon.geometry.to_crs("EPSG:3035")
    else :
        rec_polygon = polygon.geometry
    
    si = rec_polygon.length.iloc[0] / np.sqrt(np.pi * rec_polygon.area.iloc[0])
    
    return si

def number_of_full_s2_pixels( parcel, Is20mRes = False, checkPlot = False ) :
    """
    Summary:
        Evaluate the number of full Sentinel-2 pixels contained inside the
        parcel
        
    Arguments:
        parcel - polygon provided as GeoSeries with a single element        
        Is20mRes - tell the resolution of a single S2 pixel. 10x10 m is 
                   assumed by default
        
    Returns:
        nS2P - number of Sentinel 2 pixels
    """
    
    if Is20mRes :
        pixel_size = 20
    else : 
        pixel_size = 10
    
    # The pixels of S2 images are aligned with the local UTM crs
    # Thus, there is no need to download a S2 image
    # It is sufficient to work on bounds on the parcel
    
    # check the parcels projection. if it is not geographic then project it to WG84
    orig_crs = parcel.crs
    if int(gpd.__version__.split(".")[1]) > 6:
        # this is a new geopandas version above version 6
        if not orig_crs.is_geographic:
            #reproject parcel to 4326
            parcel = parcel.to_crs("EPSG:4326") 
    else:
        # this is an old geopandas below version 7
        orig_crs_value = orig_crs['init'].split(":")[1]
        if not orig_crs_value == "4326":
            #reproject parcel to 4326
            parcel = parcel.to_crs("EPSG:4326") 
    
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')

        # longitude is the "x" axis
        lon = parcel.centroid.x
    
    # determine the UTM zone
    utm_zone = int(math.floor((lon + 180) / 6) + 1)
    
    # add this new zone value to the following string format
    utm_crs = "EPSG:326" + str(utm_zone)
    
    # use geopandas to trigger a reprojection of the geodataframe
    parcel_s2 = parcel.to_crs(utm_crs)
    
    # Get the bounds of the parcels
    bounds = [ np.ceil( parcel_s2.bounds.minx.iloc[0] / pixel_size ) * pixel_size,
               np.ceil( parcel_s2.bounds.miny.iloc[0] / pixel_size ) * pixel_size,
               np.floor( parcel_s2.bounds.maxx.iloc[0] / pixel_size ) * pixel_size,
               np.floor( parcel_s2.bounds.maxy.iloc[0] / pixel_size ) * pixel_size ]
    
    # Get the pixels as polygons
    pixel_list = pixels_to_polygons( bounds, pixel_size )
    
    # Check which pixel is inside the parcel
    inside = [parcel_s2.contains( pixel_list[ii] ).iloc[0] 
              for ii in range(len(pixel_list))]
    
    if checkPlot :
        plt.figure()
        ax = plt.gca()
        parcel_s2.plot(ax = ax, facecolor='none', edgecolor='red', linewidth=2)
        geoPixels = gpd.GeoSeries(pixel_list, crs=parcel_s2.crs)
        geoPixels[inside].plot(ax = ax, facecolor='none', edgecolor='green', linewidth=2)
    
    # Count the number the pixels inside the polygon
    return sum(inside)

def pixels_to_polygons( bounds, pixel_size = 10 ) :
    """
    Summary:
        Convert a parcel bound into a list of pixels represented as a set of
        squares
        
    Arguments:
        bounds - list of four values representing the square bounds of the 
                 parcel
        pixel_size - the pixel size
        
    Returns:
        pixel_list - list of pixels
    """
    
    pixel_list = []
    
    # Get the bounding box of the image
    for ii in np.arange( bounds[0], bounds[2], pixel_size ) :
        for jj in np.arange( bounds[1], bounds[3], pixel_size ) :
            
            pixel = geometry.Polygon([[ii, jj],[ii+pixel_size, jj], 
                                      [ii+pixel_size, jj+pixel_size],
                                      [ii, jj+pixel_size], [ii, jj]])
            
            pixel_list.append(pixel)
            
    return pixel_list

def get_geometric_properties( polygon ) -> dict :
    """
    Summary :
        Evaluate the geometric properties of a parcel and return them as
        a dictionary.

    Arguments :
        polygon - the polygon defying the geometry of the parcel.
        
    Returns:
        A dictionary with the geometric properties of the parcel.
    """
    
    # Perform a preliminary check on the polygon
    if polygon is None :
        
        out_dict = {'Area' : np.nan,
                    'Perimeter' : np.nan,
                    'Shape index' : np.nan,
                    'Side ratio': np.nan,
                    'S2 pixels' : np.nan }
        
        return out_dict
    
    area = get_area( polygon )
    perimeter = get_perimeter( polygon )
    si = get_shape_index( polygon )
    
    # determine the minimum area oriented rectangle and determine the side ratio
    mar_poly = min_area_rect( polygon )
    side_ratio = extreme_side_ratio(mar_poly, False)
    
    # and finally the number of sull Sentinel-2 pixels
    # NEED TO BE UPDATED - Check with Csaba 
    npixels = number_of_full_s2_pixels( polygon, False )
    
    out_dict = {'Area' : area,
                'Perimeter' : perimeter,
                'Shape index' : si,
                'Side ratio': side_ratio,
                'S2 pixels' : npixels }
    
    return out_dict
