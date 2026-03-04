#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 23 07:04:07 2025

@author: daniele
"""

import pandas as pd
import xarray as xr
import os

def filter_data_set(ds, mask) :
    """
    Function that filter a dataset based on a specific mask.
        
    Arguments :
        ds: the dataset to be filtered
        
        mask : mask used for the filtering
    """
    ds_masked = ds.where( mask, drop = True)

    # For some reason, the CRS is not copied
    ds_masked = ds_masked.rio.write_crs(ds.rio.crs)

    return ds_masked

def get_mask_from_values(ds, attribute, valid_list : list) :
    
    return ds[attribute].isin(valid_list)
    
    
def get_SCL_mask(ds, scl_list : list = [0, 1, 3, 8, 9, 10, 11] ) :
    
    # All scl classes
    scl = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    
    # scl_list contains the classes that are excluded: need to keep the one
    # that are included
    included_scl = list(set(scl) - set(scl_list))
    
    if len(scl_list) < 1 :
        raise Exception("The SCL list cannot be empty")
    
    if not "SCL" in ds :
        raise Exception("SCL variable not present")
        
    return ds["SCL"].isin(included_scl)

def get_band_statistics(ds, parcel, parcel_ID, band_list : list = [], \
                      scl_list : list = [0, 1, 3, 8, 9, 10, 11]) :
    """
    Function that computes band statistics for an xarray dataset
        
    Arguments:
        
    Returns:
    """
    
    # First check if SCL masking needs to be applied
    if len(scl_list) > 0 :
        ds_masked = ds.where( get_SCL_mask(ds, scl_list), drop = True)
    else :
        ds_masked = ds
        
    # For some reason, the CRS is not copied
    ds_masked = ds_masked.rio.write_crs(ds.rio.crs)
        
    # Check the band list (and create one if empty)
    if len(band_list) == 0 :
        band_list = list(ds.keys())
        
        # There is no interest for the SCL
        if "SCL" in band_list :
            band_list.remove("SCL")
            
    # Clip the dataset to the parcel geometry
    clipped = ds_masked.rio.clip(parcel["geometry"].values, parcel.crs, drop=True)
    
    # Keep only 'images' with at least one valid pixel
    clipped = clipped.isel( t = (clipped[band_list[0]].count(dim=["x", "y"]).values > 0) ) 

    return_dict = {}
    
    # Now compute the statistics
    for band_name in band_list :
        
        # Do something only if the band is present
        if band_name not in ds :
            continue
        
        if ('x' not in clipped[band_name].dims) or ('y' not in clipped[band_name].dims) :
            continue
        
        mean_val = clipped[band_name].mean(dim=["x", "y"], skipna=True)
        
        stat_dict = {}
        
        stat_dict["Field_ID"] =  [parcel_ID] * len(mean_val.t)
        stat_dict["acq_date"] = mean_val.t.values
        stat_dict["band_mean"] = mean_val.values
        stat_dict["band_count"] = clipped[band_name].count(dim=["x", "y"]).values
        stat_dict["band_std"] = clipped[band_name].std(dim=["x", "y"], skipna=True).values
        stat_dict["band_median"] = clipped[band_name].median(dim=["x", "y"], skipna=True).values
        stat_dict["band_25p"] = clipped[band_name].quantile(0.25, dim=["x", "y"], skipna=True).values
        stat_dict["band_75p"] = clipped[band_name].quantile(0.75, dim=["x", "y"], skipna=True).values
        stat_dict["band_max"] = clipped[band_name].max(dim=["x", "y"], skipna=True).values
        stat_dict["band_min"] = clipped[band_name].min(dim=["x", "y"], skipna=True).values
            
        return_dict[band_name] = stat_dict
        
    return return_dict
        
def ds_statistics_to_csvs(ds, parcel, parcel_ID, out_dir = './band_stats', \
                        band_list : list = [], \
                        scl_list : list = [0, 1, 3, 8, 9, 10, 11]):
    
    """
    Function that extract the statistics from a netcdf file and same them
    as csv.
    
    N.B.: a csv file is produced for each parcel
    
    Arguments :
        ds - the data set with the netcdf data 
        parcel - geopandas dataframe with the parcel geometry 
        parcel_ID - unique identifier for the parcel 
        out_dir - output directory
        band_list - list of bands (dataset variables to process)
        scl_list - list of SCL values to filter ouyt e.g. [0, 1, 3, 8, 9, 10, 11]
    """
    
    if not os.path.exists(out_dir) :
        os.makedirs(out_dir)
        
    # Get the statistics as a dictionary
    return_dict = get_band_statistics(ds, parcel, parcel_ID, band_list, scl_list)

    # Now save the csv files
    for key in return_dict :
        
        csv_filename = f"{out_dir}/{parcel_ID}_{key}.csv"
        
        # Convert the dictionary with the band information into a panda dataframe
        df = pd.DataFrame(return_dict[key])
        
        # save it as csv file
        df.to_csv(csv_filename, index = False )
       
def ds_statistics_to_parcel_csv(ds, parcel, parcel_ID, out_dir = './band_stats', \
                                band_list : list = [], \
                                scl_list : list = [0, 1, 3, 8, 9, 10, 11]):
    
    """
    Function that extract the statistics from a netcdf file and save all the
    information to a single csv. All the bands are considered
    
    Arguments :
        ds - the data set with the netcdf data 
        parcel - geopandas dataframe with the parcel geometry 
        parcel_ID - unique identifier for the parcel 
        out_dir - output directory
        band_list - list of bands (dataset variables to process)
        scl_list - list of SCL values to filter ouyt e.g. [0, 1, 3, 8, 9, 10, 11]
    """
    
    if not os.path.exists(out_dir) :
        os.makedirs(out_dir)
        
    # Get the statistics as a dictionary
    return_dict = get_band_statistics(ds, parcel, parcel_ID, band_list, scl_list)

    # Now restruct the return dictionary
    full_dict = {}
    first_key = list(return_dict.keys())[0]
    for key in return_dict[first_key] :
        full_dict[key] = []
    full_dict['band'] = []
    
    for key in return_dict :
        for fkey in return_dict[key] :
            full_dict[fkey] = [*full_dict[fkey], *(return_dict[key][fkey])]

        full_dict['band'] = [*full_dict['band'], *([key]*len(return_dict[key]['Field_ID']))]
        
    csv_filename = f"{out_dir}/{parcel_ID}_stats.csv"
        
    # Convert the dictionary with the band information into a panda dataframe
    df = pd.DataFrame(full_dict)
        
    # save it as csv file
    df.to_csv(csv_filename, index = False )
    
    return csv_filename
    
def ds_statistics_to_single_csv(parcels, col_names, ds_prefix, out_name, band_list : list = [], \
                             scl_list : list = [0, 1, 3, 8, 9, 10, 11]) :
    """
    Function that extract the statistics from a set of netcdf files and same them into a set of 
    csv files.
    
    N.B.: a single csv file is produced for each band
    
    Arguments :
        parcels - geopandas dataframe with all the parcel geometries 
        col_names - list of columns to use for building the parcel ID 
        ds_prefix - prefix to be used to build the name of the different datasets to load
        out_name - string used to specify the name of output csv files
        band_list - list of bands (dataset variables to process)
        scl_list - list of SCL values to filter ouyt e.g. [0, 1, 3, 8, 9, 10, 11]
    """
    
    # Loop on the parcels
    for ii in range(len(parcels)) :
        
        parcel = parcels.iloc[ii:ii+1]
        
        # Build the parcel ID
        for kk, value in enumerate(col_names) : 
            if kk == 0 :
                parcelID = str(parcel[value].values[0])
            else :
                parcelID = parcelID + '_' + str(parcel[value].values[0])
                
        # Now load the dataset
        filename = ds_prefix + parcelID + '.nc'
         
        if not os.path.exists(filename) :
            continue
        
        ds = xr.open_dataset(filename) 
    
        # assign the crs
        crs_wkt = ds["crs"].attrs.get("crs_wkt")
        ds = ds.rio.write_crs(crs_wkt)
    
        # Now get the band statistics
        stats = get_band_statistics(ds, parcel, parcelID, band_list, scl_list)
        
        # check if the output folder exists
        outfolder = out_name[:out_name.rfind("/")]
        
        if not os.path.exists(outfolder) :
            os.makedirs(outfolder)
        
        # Now save the csv files
        for key in stats :
            
            csv_filename = f"{out_name}_{key}.csv"
            
            # Convert the dictionary with the band information into a panda dataframe
            df = pd.DataFrame(stats[key])
            
            # save it as csv file
            if ii == 0 :
                # This is the first parcel
                df.to_csv(csv_filename, index = False )
            else :
                # Append
                df.to_csv(csv_filename, index = False, mode ="a", header = False)
                
def add_index(ds, index_fun, index_name, band_list = ["B08", "B04"]) :
    
    # New data set with the new variable
    dn = ds.assign(newvar = index_fun(ds, band_list))
    dn = dn.rename({"newvar" : index_name})
    
    return dn


def normalized_difference(ds, band_list = ["B08", "B04"]) :
    """
    Function that computes the normalized difference between two bands    
    """
    
    return (ds[band_list[0]] - ds[band_list[1]]) / (ds[band_list[0]] + ds[band_list[1]])

def ratio(ds, band_list = ["B08", "B04"]) :
    """
    Function that computes the ratio between two bands    
    """
    
    return ds[band_list[0]] / ds[band_list[1]]


def binary_score(ds, band_list = []) :
    """
    Function that computes a score resulting from the comparison of different bands.    
    """
    
    # Since we need all the bands, band_list is overwritten
    band_list = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B11", "B12"] 
    
    
    # Table with the indexes and scores for the comparison
    comp_table = [[0, 1, 1],
                  [1, 2, 2],
                  [2, 3, 4],
                  [3, 4, 8],
                  [4, 5, 16],
                  [5, 6, 32],
                  [6, 7, 64],
                  [7, 8, 128],
                  [8, 9, 256],
                  [6, 8, 512],
                  [6, 9, 1024],
                  [9, 4, 2048],
                  [8, 4, 4096]]
    
    for ii, comp in enumerate(comp_table) :
        if ii == 0 :
            dn  = (ds[band_list[comp[0]]] < ds[band_list[comp[1]]]) * comp[2]
        else :
            dn  = dn + (ds[band_list[comp[0]]] < ds[band_list[comp[1]]]) * comp[2]
            
    return dn