# -*- coding: utf-8 -*-
"""
Created on Tue May 18 14:52:21 2021

@author: Csaba
"""
import math

def get_parcel_area_ha_2decimals_str(parcel):
    # check the parcels projection. if it is not geographic then project it to WG84

    orig_crs = parcel.crs
    orig_crs_value = orig_crs['init'].split(":")[1]
    if not orig_crs_value == "4326":
        #reproject parcel to 4326
        parcel = parcel.to_crs("EPSG:4326") 
        
    # longitude is the "x" axis
    lon = parcel.centroid.x
    
    # determine the UTM zone
    utm_zone = int(math.floor((lon + 180) / 6) + 1)
    # add this new zone value to the following string format
    utm_crs = "EPSG:326" + str(utm_zone)
    # use geopandas to trigger a reprojection of the geodataframe
    pacel_utm = parcel.to_crs(utm_crs)
    parcel_area_ha = pacel_utm['geometry'].area / 10000
    parcel_area_ha_str = str(round(parcel_area_ha.values[0],2))
    return parcel_area_ha_str