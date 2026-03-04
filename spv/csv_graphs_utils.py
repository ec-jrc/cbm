#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 24 09:41:12 2025

@author: daniele
"""

import os
import pandas as pd
import numpy as np


import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# plt.ioff()

plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14

scl_dict = { 0 : (0, 0, 0),     # No Data (Missing data)
             1 : (255, 0, 0),   # Saturated or defective pixel
             2 : (47, 47, 48),  # Dark features/Shadows
             3 : (100, 50, 0),  # Cloud shadows
             4 : (0, 160, 0),   # Vegetation
             5 : (255, 230, 85), # Not-vegetated
             6 : (0, 0, 255),   # Water
             7 : (128, 128, 128),   # Unclassified
             8 : (192, 192, 192),   # Cloud medium probability
             9 : (255, 255, 255),   # Cloud high probability
             10 : (100, 200,255),   # Thin cirrus
             11 : (255, 150, 255)
    }


def make_compo_scl_ndvi_graph(suffix, output_folder :  str = "./", to_file = True) :
    
    """
    Summary :
        Function that combines several sources of information including SCL and
        NDVI
        
    Arguments :
        suffix - string used to load the different CSV files
        
        output_folder - folder where to save the graphs
        
    Returns :
        A dictionary with the matplotlib axes pointing to the plots        
    """ 
    
    # Allocate the figure
    height_ratios = [1, 8, 2]
        
    fig, ax = plt.subplots(3, 1, gridspec_kw={'height_ratios': height_ratios}, \
                           sharex=True)
    
    # Plot the SCL components
    scl_file = suffix + "_SCL.csv"
    scl_df = pd.read_csv(scl_file)
    
    # re-index the dataframe with respect to the dates
    scl_df = scl_df.set_index(pd.to_datetime(scl_df["acq_date"]))
    
    # resample the SCL modes
    daily_scl = scl_df['band_mode1'].resample('D').interpolate(method='nearest')
    
    # Number of SCL points    
    nb_points = len(daily_scl)
    
    bottom_bar = np.ones((1, nb_points, 3), dtype=np.uint8)                        
                
    for ii, scl_value in enumerate(daily_scl.values) :
        bottom_bar[0,ii,:] = scl_dict[scl_value]

    if len(scl_df) > 0 :
        xextent = mdates.date2num([daily_scl.index[0], daily_scl.index[-1]])
        ax[0].imshow( bottom_bar, extent = [xextent[0], xextent[1],  0, 1], aspect = 'auto' )
    
    # Add the NDVI
    ndvi_file = suffix + "_NDVI.csv"
    ndvi_df = pd.read_csv(ndvi_file)
    
    # Synchronize the two dataframes
    values, ind1, ind2 = np.intersect1d(ndvi_df["acq_date"].values, scl_df["acq_date"].values, return_indices=True)
    
    ndvi_df = ndvi_df.iloc[ind1]
    scl_df = scl_df.iloc[ind2]
    
    # re-index the dataframe with respect to the dates
    ndvi_df = ndvi_df.set_index(pd.to_datetime(ndvi_df["acq_date"]))
    ax[1].plot(ndvi_df.index, ndvi_df["band_mean"])
    
    # filter the NDVI by SCL values
    ndvi_scl = ndvi_df["band_mean"]
    ndvi_scl = ndvi_scl[scl_df["band_mode1"].isin([2, 4, 5, 6, 7])]
    
    ax[1].plot(ndvi_scl.index, ndvi_scl, '.-')
    
    # Now compute the "Inter-band comparison"
    ibc = get_ibc_values(suffix)
    
    for ii, date in enumerate(ibc.index) :
        ax[2].text(date, 0, str(ibc.values[ii][0]), rotation="vertical", va= 'bottom', ha='center')
        
    # ndvi_ibc = ndvi_df["band_mean"] 
    # ndvi_ibc = ndvi_ibc[ibc["ibc_values"].isin([list from PL])]
    # ax[1].plot(ndvi_ibc.index, ndvi_ibc, '.-')
    
def get_ibc_values(suffix) :
    
    # List of bands for the comparison
    band_list = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"] 
    
    
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
        
    for ii, compo in enumerate(comp_table) :
        
        # Load the dataframes for the comparison
        df1 = pd.read_csv(suffix + f"_{band_list[compo[0]]}.csv")
        df2 = pd.read_csv(suffix + f"_{band_list[compo[1]]}.csv")
        
        if ii == 0 :
            time, ind1, ind2 = np.intersect1d(df1["acq_date"].values, \
                                              df2["acq_date"].values, return_indices=True)
                       
            icb_values = (df1["band_mean"].values[ind1] < df2["band_mean"].values[ind2]) * compo[2]
        else :
            
            ctime, ind1, ind2 = np.intersect1d(df1["acq_date"].values, \
                                               df2["acq_date"].values, return_indices=True)
                       
            delta_values = (df1["band_mean"].values[ind1] < df2["band_mean"].values[ind2]) * compo[2]
             
            time, ind1, ind2 = np.intersect1d(ctime, time, return_indices=True)
            
            icb_values = icb_values[ind2] + delta_values[ind1]
            
        icb_df = pd.DataFrame({"icb_values" : icb_values}, index=pd.to_datetime(time))
    
    return icb_df

def plot_csv_profiles(csv_filename, output_folder : str = "./", \
                    cols_to_plot : list = ["band_mean", "band_std"],
                    ax_dict = None, to_file = True):
    """
    Summary :
        Function used to plot a time index extracted from a CSV file.
        Several plots may be generated if several parcels are present in the
        CSV file
        
    Arguments :
        csv_filename - string indicating the CSV file to process
        
        output_folder - folder where to save the graphs
        
        cols_to_plots - columuns to be used for the plotting. The list can
                        contain either one value (only the time series will be
                        plotted) or two. In this latter case, the second value
                        will be used as element of dispersion.
    Returns :
        A dictionary with the matplotlib axes pointing to the plots        
    """ 
    
    # Infer the index from the CSV file
    index_name = csv_filename.split('.')[-2].split('_')[-1]
    
    # First read the CSV file as data frame
    df = pd.read_csv(csv_filename)
    
    # Convert the acquisition dates to datetime objects
    df['acq_date'] = pd.to_datetime(df['acq_date'])
    
    # Now determine the list of parcels to plot
    fids = np.unique(df["Field_ID"].values).astype(str)
    
    # Check if the output directory exists
    if not os.path.exists(output_folder) :
        os.makedirs(output_folder)
  
    # Output dictionary
    if ax_dict is not None :
        out_dict = ax_dict
    else :
        out_dict = {}
  
    # Now make a plot for each parcel
    for fid in fids :
        
        df_fid = df[df["Field_ID"] == fid].copy()
        df_fid.sort_values(by=['acq_date'], inplace = True)
                
        # Allocate the figure
        if ax_dict is not None :
            fig, ax = plt.subplots(figsize = (13, 7))
        else :
            # check if the axis for the specific fid exists
            if fid in out_dict :
                ax = ax_dict[fid]
                fig = ax.gcf()
            else :
                fig, ax = plt.subplots(figsize = (13, 7))
                    
        if len(cols_to_plot) == 1 :
            df_fid.plot(kind='line', marker='+', x='acq_date',y= cols_to_plot[0], \
                        color = 'blue', ax = ax)            
        
        else :
            df_fid.plot(kind='line', marker='+', x ='acq_date', y = cols_to_plot[0], \
                        yerr= cols_to_plot[1], color = 'blue', ax = ax, \
                        capsize=4, ecolor='grey', barsabove = 'True')
                
        # Format the graph
        ax.set_ylabel(index_name)
        ax.set_xlabel("Date")        
        ax.set_title("Parcel id: " + str(fid) + " " + index_name)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
         
        ax.xaxis.grid() # horizontal lines
        ax.yaxis.grid() # vertical lines

        # save the figure to a jpg file
        if to_file :
            fig.savefig(f"{output_folder}/{fid}_{index_name}.png") 
        
        # Eventually update the output dictionary
        if fid not in out_dict :
            out_dict[fid] = ax
        
        plt.close(fig)    
    
        
    
    return out_dict

def plot_csv_parcel(csv_filename, output_folder : str = "./", \
                    band_to_plot : str = "NDVI",
                    cols_to_plot : list = ["band_mean", "band_std"],
                    ax_dict = None, to_file = True):
    """
    Summary :
        Function used to plot a time index extracted from a CSV file.
        In this case, it assumed that all the bands are saved in a single file
        A single parcel is considered
        
    Arguments :
        csv_filename - string indicating the CSV file to process
        
        output_folder - folder where to save the graphs
        
        bands_to_plot - specifies which band should be plotted
        
        cols_to_plots - columuns to be used for the plotting. The list can
                        contain either one value (only the time series will be
                        plotted) or two. In this latter case, the second value
                        will be used as element of dispersion.
    Returns :
        A dictionary with the matplotlib axes pointing to the plots        
    """ 
    
    # Infer the index from the CSV file
    index_name = csv_filename.split('.')[-2].split('_')[-1]
    
    if index_name != "stats" :
        raise ValueError("Suffix stats expected in the csv filename")
    
    # First read the CSV file as data frame
    df = pd.read_csv(csv_filename)
    
    # Filter the df with respect to the specified band
    df = df[df["band"] == band_to_plot]
    
    # Convert the acquisition dates to datetime objects
    df['acq_date'] = pd.to_datetime(df['acq_date'])
    
    
    # Now determine the list of parcels to plot
    fid = np.unique(df["Field_ID"].values).astype(str)[0]
    
    # Check if the output directory exists
    if to_file and (not os.path.exists(output_folder)) :
        os.makedirs(output_folder)
  
    df.sort_values(by=['acq_date'], inplace = True)
            
    # Allocate the figure
    if ax_dict is None :
        fig, ax = plt.subplots(figsize = (13, 7))
    else :
        ax = ax_dict[fid]
        fig = ax.gcf()
                
    if len(cols_to_plot) == 1 :
        df.plot(kind='line', x='acq_date',y= cols_to_plot[0], \
                    marker="o", color="forestgreen", linewidth=2, ax = ax)            
    else :
        # Add mean profile with std bands
        ax.plot(df['acq_date'], df[cols_to_plot[0]],  marker="o", 
                color="forestgreen", linewidth=2)
        
        ax.fill_between(df['acq_date'],
                        df[cols_to_plot[0]] - df[cols_to_plot[1]], 
                        df[cols_to_plot[0]] + df[cols_to_plot[1]],
                         alpha=0.2, color = 'green')
                
    # Format the graph
    ax.set_ylabel(band_to_plot, fontsize = 14)
    ax.set_xlabel("Date", fontsize = 14)        
    ax.set_title("Parcel id: " + str(fid), fontsize = 14)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
     
    ax.xaxis.grid() # horizontal lines
    ax.yaxis.grid() # vertical lines

    ax.autoscale(tight='True')

    fig.autofmt_xdate() # Rotation
    
    fig.tight_layout()
    # save the figure to a jpg file
    if to_file :
        fig.savefig(f"{output_folder}/{fid}_{band_to_plot}.png") 
        plt.close(fig) 
            
    return fig, ax