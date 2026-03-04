# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 16:08:11 2025

@author: borioda

Porting of plotting functions to be used with NetCDF files
"""

import numpy as np
import os
import pickle

import matplotlib.pyplot as plt
plt.ioff()


import plot_utils

MAXVAL = 10000


def get_parcel_name_and_id(name_cols, parcel) :
    
    # Build path name
    if name_cols is None :
        parcel_name = str(parcel.index[0])
        parcel_id = parcel.index[0]
    else :
        parcel_name = ""
        for jj, cols in enumerate(name_cols) :
            if jj == 0 :
                parcel_name = str(parcel.iloc[0][cols])
            else :
                parcel_name = parcel_name + "_" + str(parcel.iloc[0][cols])
            
        parcel_id = parcel.iloc[0][name_cols[0]]
    
    return parcel_name, parcel_id

def check_boundary_img_conditions( red : np.array, green : np.array, blue : np.array ) :
    """
    Summary :
        Function that checks if a least one of the bands has a first/last row/column 
        all equal to zero. If this is the case, alse the other bands are adjusted.

    Parameters
    ----------
    red : np.array
        2D numpy array with the red band
        
    green : np.array
        2D numpy array with green band
        
    blue : np.array
        2D numpy array with blue band

    Returns
    -------
    None.

    """
    
    # All four boundary conditions need to be tested
    if all(red[:,0] == 0) or all(green[:,0] == 0) or all(blue[:,0] == 0):
        red[:,0] = MAXVAL * np.ones(red[:,0].shape)
        green[:,0] = MAXVAL * np.ones(green[:,0].shape)
        blue[:,0] = MAXVAL * np.ones(blue[:,0].shape)
        
    if all(red[:,-1] == 0) or all(green[:,-1] == 0) or all(blue[:,-1] == 0):
        red[:,-1] = MAXVAL * np.ones(red[:,-1].shape)
        green[:,-1] = MAXVAL * np.ones(green[:,-1].shape)
        blue[:,-1] = MAXVAL * np.ones(blue[:,-1].shape)

    if all(red[0,:] == 0) or all(green[0,:] == 0) or all(blue[0,:] == 0):
        red[0,:] = MAXVAL * np.ones(red[0,:].shape)
        green[0,:] = MAXVAL * np.ones(green[0,:].shape)
        blue[0,:] = MAXVAL * np.ones(blue[0,:].shape)
        
    if all(red[-1,:] == 0) or all(green[-1,:] == 0) or all(blue[-1,:] == 0):
        red[-1,:] = MAXVAL * np.ones(red[-1,:].shape)
        green[-1,:] = MAXVAL * np.ones(green[-1,:].shape)
        blue[-1,:] = MAXVAL * np.ones(blue[-1,:].shape)
    
    # Replace nans
    np.nan_to_num(red, copy=False, nan=MAXVAL) 
    np.nan_to_num(green, copy=False, nan=MAXVAL) 
    np.nan_to_num(blue, copy=False, nan=MAXVAL) 
    
            
def calendar_view_half_weekly(ds, parcel = None, name_cols = None, band_list = None, \
                              out_tif_folder_base = "./", 
                              stretch_table = None, buffer_size_meter = 50, \
                              vector_color = "black", image_resolution = 100 ) :   
    
    """
    Summary :
        Function that generates a calendar view visualization with half weekly display
        for a set of three bands. The function expects either a dataset as loaded from
        a NetCDF file.
        
        Code based on the calendar view function of Csaba Wirnhardt.
        
    Arguments :
        ds - dataset with the different bands extracted from the NetCDF file
        
        parcel - geometry of the parcel
        
        name_cols = list of colums for termining the parcel name/ID
        
        band_list - list of Sentinel-2 bands present in the merged geotiff.
                    This is needed to select the correct bands
        
        stretch_table - dictionary containig 3 keys corresponding to the three bands
                        to plot
                        
            Example:
                stretch_table = {'B08' : [1200, 5700],
                                 'B11' : [800, 4100],
                                 'B04' : [150, 2800]}
    """
    if name_cols is None :
        parcel_name = "1"
        parcel_id = 1
    else :
        parcel_name, parcel_id = get_parcel_name_and_id(name_cols, parcel)

    if band_list is None :
        band_list = ["B08", "B11", "B04"]
        
    if len(band_list) not in [1, 3] :
        raise Exception("Unsupported number of bands")
        
    # output folder
    output_jpg_folder = out_tif_folder_base
    
    if not os.path.exists(output_jpg_folder):
        os.makedirs(output_jpg_folder)

    # Acquistion dates are supposed to be stored in the t variable 
    # use uniqe to avoid duplications
    dates = np.unique(ds.t)
    
    # Imagettes will be displayed in a matrix, use these function to determine 
    # the matrix size
    year_months_dict = plot_utils.get_year_months_dict(dates)
    year_months_dict_half_weekly = plot_utils.get_year_months_dict_for_half_weekly(dates)
    
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = plot_utils.get_number_of_rows(dates)
    
    # Determine the number of rows, the number of columns is fixed
    num_rows = number_of_year_months + 1
    num_cols = 9
    
    textstrs = plot_utils.get_current_list_of_months(str(first_year_month), number_of_year_months)
    
    # figure size
    if parcel is not None :
        parcel_extent_ratio = plot_utils.get_parcel_extent_ratio(parcel, buffer_size_meter)
    else :
        parcel_extent_ratio = len(ds.y) / len(ds.x)
        
    fig_size_x = 16
    fig_size_y = fig_size_x * (number_of_year_months / (num_cols-1)) * parcel_extent_ratio
    
    fig, a = plt.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    info_text = str(parcel_id) + "\n"
    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=10,
                    verticalalignment='center', horizontalalignment='center')

    # Check if the lut for band stretching has been defined
    # If not allocate it
    undefined = False
    if (stretch_table is None) and (len(band_list) == 3) :
        
        stretch_table = {'B08' : [1200, 5700],
                         'B11' : [800, 4100],
                         'B04' : [150, 2800]}

        undefined = True
        
    # Loop on the acquisition dates
    for acq_date in dates:
        act_col = plot_utils.get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = plot_utils.get_current_row(acq_date, dates)
        
        if undefined and acq_date > np.datetime64("2022-01-25") :
            # If the lut was undefined, apply 'date' correction
            lut =  {'B08' : [2200, 6700],
                    'B11' : [1800, 5100],
                    'B04' : [1150, 3800]}
        else :
            lut = stretch_table
        
        if act_col > 0:
            
            # Identify the data related to a specific date
            data = ds.isel(t = np.argwhere(ds.t.values == acq_date).flatten()[0])
            
            if parcel is not None :
                parcel = parcel.to_crs(data.rio.crs)
            
            a[act_row][act_col].set_title(np.datetime_as_string(acq_date, unit='D'), verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})
        
            # Build the extent
            extent = (min(ds.x.values) - np.mean(abs(np.diff(ds.x.values))) / 2, # left value
                      max(ds.x.values) + np.mean(abs(np.diff(ds.x.values))) / 2, # right value
                      min(ds.y.values) - np.mean(abs(np.diff(ds.y.values))) / 2, # bottom value
                      max(ds.y.values) + np.mean(abs(np.diff(ds.y.values))) / 2)  # top value
            
            if len(band_list) == 3 :
            
                # Now read the three bands
                band_red = data[band_list[0]].values    
                band_green = data[band_list[1]].values
                band_blue = data[band_list[2]].values    
                
                # Check for boundary conditions
                check_boundary_img_conditions( band_red, band_green, band_blue )
                
                # Stack and stretch the three bands
                rgb_compo = plot_utils.stretch_and_stack(band_red, band_green, band_blue, lut)
                                    
                a[act_row][act_col].imshow(rgb_compo, extent = extent)
            else :
                band = data[band_list[0]].values
                
                #N.B.: vmin and vmax needs to be carefully checked since not all the indexes are between such ranges
                a[act_row][act_col].imshow(band, extent = extent, cmap = 'RdYlGn', vmin = 0, vmax=1)

            if parcel is not None :
                parcel.plot(ax=a[act_row][act_col], facecolor='none', edgecolor=vector_color)

    output_file = output_jpg_folder + "/" + str(parcel_name) + "_" + "".join(band_list)
    fig.savefig(output_file  + ".png", dpi = image_resolution, bbox_inches='tight')  

    # Also Pickle the figure object
    with open(output_file  + ".pickle", 'wb') as f:
        pickle.dump(fig, f)
    
    return fig, a

def calendar_view_half_weekly_scatter(ds, parcel = None, name_cols = None, \
                              out_tif_folder_base = "./", 
                              sc_dict = None, image_resolution = 100 ) :   
    
    """
    Summary :
        Function that generates a calendar view visualization with half weekly display
        providing the time evolution of the scatter plot between two bands. 
        The function expects a dataset as loaded from a NetCDF file.
        
        
    Arguments :
        ds - dataset with the different bands extracted from the NetCDF file
        
        parcel - geometry of the parcel
        
        name_cols = list of colums for termining the parcel name/ID
        
        sc_dict - dictionary with the information to create the scatter plot
        
        Example :
            sc_dict = {'x' : "B04",
                       'y' : "B08",
                       'xmax' : 6000,
                       'ymax' : 6000,
                       'cumulative' : True,
                       'color' : 'red',
                       'cumulative_color' : 'blue'}
    """

    if name_cols is None :
        parcel_name = "1"
        parcel_id = 1
    else :
        parcel_name, parcel_id = get_parcel_name_and_id(name_cols, parcel)

        
    # output folder
    output_jpg_folder = out_tif_folder_base + "/scatter_half_weekly"
    
    if not os.path.exists(output_jpg_folder):
        os.makedirs(output_jpg_folder)

    # Acquistion dates are supposed to be stored in the t variable 
    # use uniqe to avoid duplications
    dates = np.unique(ds.t)
    
    # Imagettes will be displayed in a matrix, use these function to determine 
    # the matrix size
    year_months_dict = plot_utils.get_year_months_dict(dates)
    year_months_dict_half_weekly = plot_utils.get_year_months_dict_for_half_weekly(dates)
    
    first_year_month = min(year_months_dict.keys())
    number_of_year_months = plot_utils.get_number_of_rows(dates)
    
    # Determine the number of rows, the number of columns is fixed
    num_rows = number_of_year_months + 1
    num_cols = 9
    
    textstrs = plot_utils.get_current_list_of_months(str(first_year_month), number_of_year_months)
            
    fig_size_x = 16
    fig_size_y = fig_size_x * (number_of_year_months / (num_cols-1))
    
    fig, a = plt.subplots(num_rows, num_cols, figsize=(fig_size_x, fig_size_y))

    # we remove the axes showing the coordinates which is anyway meaningless
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            a[i][j].set_axis_off()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    # plot Year and month names in first columnt
    output_row = 1
    for textstr in textstrs:
        a[output_row][0].text(0.5, 0.5, textstr, transform=a[output_row][0].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_row += 1

    # plot header row
    output_col = 1
    header_row_textstrs = ["Week\n1A", "Week\n1B", "Week\n2A", "Week\n2B", "Week\n3A", "Week\n3B", "Week\n4A", "Week\n4B",]
    for textstr in header_row_textstrs:
        a[0][output_col].text(0.5, 0.5, textstr, transform=a[0][output_col].transAxes, fontsize=14,
                verticalalignment='center', bbox=props, horizontalalignment='center')
        output_col += 1
        
    info_text = str(parcel_id) + "\n"
    a[0][0].text(0.5, 0.5, info_text, transform=a[0][0].transAxes, fontsize=10,
                    verticalalignment='center', horizontalalignment='center')

    # Check if the dictionary with the plotting information has been allocated
    if sc_dict is None :
        sc_dict = {'x' : "B04",
                   'y' : "B08",
                   'xmax' : 6000,
                   'ymax' : 6000,
                   'cumulative' : True,
                   'color' : 'red',
                   'cumulative_color' : 'blue'}
    
    # Dictionary with cumulative information
    cum_info = {'x' : [],
                'y' : []}
        
    # Loop on the acquisition dates
    for acq_date in dates:
        act_col = plot_utils.get_half_weekly_column(acq_date, year_months_dict_half_weekly)
        act_row = plot_utils.get_current_row(acq_date, dates)
                
        if act_col > 0:
            
            # Identify the data related to a specific date
            data = ds.isel(t = np.argwhere(ds.t.values == acq_date).flatten()[0])
            
            if parcel is not None :
                parcel = parcel.to_crs(data.rio.crs)
            
            a[act_row][act_col].set_title(np.datetime_as_string(acq_date, unit='D'), verticalalignment='center', fontdict={'fontsize': 8, 'fontweight': 'medium'})

            plot_scatter(data, parcel, cum_info, sc_dict, a[act_row][act_col])

            # Set y axis on only if this is the first column
            a[act_row][act_col].set_axis_on()
            
            if act_col != 1 :
                a[act_row][act_col].get_yaxis().set_visible(False)
                
            if act_row != num_rows - 1 :
                a[act_row][act_col].get_xaxis().set_visible(False)

            print(acq_date)

    output_jpg_file = output_jpg_folder + "/" + str(parcel_name) + "_" + sc_dict["x"] + "_" + sc_dict["y"] + "_scatter.png"
    fig.savefig(output_jpg_file, dpi = image_resolution, bbox_inches='tight')  
    plt.close(fig)
    
    return fig, a

def plot_scatter(data, parcel, cum_info, sc_dict, ax) :
    """
    Summary :
        Fuction that plots a single scatter plot given different parameters
        
    Parameters
    ----------
    data : xarray dataset with a single date
    
    parcel : geodataframe with the geometry of the parcel to consider
    
    cum_info : dictionary with previous points cumulated over the different epochs
    
    sc_dict : dictionary with the information for producing the scatter plot

    ax : matplotib axis to make the plot

    Returns
    -------
    None.

    """
    # Clip the dataset with respect to the polygon geometry
    if parcel is not None :
        clipped = data.rio.clip(parcel.geometry.values, parcel.crs, drop=True)
    else :
        clipped = data
        
    # Get the band values
    xval = clipped[sc_dict['x']].values
    yval = clipped[sc_dict['y']].values
    
    # Plot the past scatter plots and update cum_info
    if isinstance(sc_dict['cumulative'], bool) :
        # sc_dict['cumulative'] is either True or False
        if sc_dict['cumulative'] :

            # check if the color is defined
            if ('cumulative_color' in sc_dict) and \
               (sc_dict['cumulative_color'] is not None) :
                ccolor = sc_dict['cumulative_color']
            else :
                ccolor = 'blue'
            
            for ii, x in enumerate(cum_info['x']) :
                y = cum_info['y'][ii]
                ax.scatter(x, y, marker = "x", s = 1, color = ccolor)
                
            # Append the new info
            cum_info['x'].append(xval)
            cum_info['y'].append(yval)
        # else --> if False do not plot anything
    else :
        # sc_dict['cumulative'] is a number (i.e. keeps on the last N epochs)
        # remove extra points
        while len(cum_info['x']) > sc_dict['cumulative'] :
            cum_info['x'].pop(0)
            
        while len(cum_info['y']) > sc_dict['cumulative'] :
            cum_info['y'].pop(0)
            
        # check if the color is defined
        if ('cumulative_color' in sc_dict) and \
           (sc_dict['cumulative_color'] is not None) :
               ccolor = sc_dict['cumulative_color']
        else :
            ccolor = 'blue'
        
        for ii, x in enumerate(cum_info['x']) :
            y = cum_info['y'][ii]
            ax.scatter(x, y, marker = "x", s = 1, color = ccolor)
            
        # Append the new info
        cum_info['x'].pop(0)
        cum_info['y'].pop(0)
        cum_info['x'].append(xval)
        cum_info['y'].append(yval)
    
    # Now plot the new info
    
    # check if the color is defined
    if ('color' in sc_dict) and (sc_dict['color'] is not None) :
        color = sc_dict['color']
    else :
        ccolor = 'red'
    
    ax.scatter(xval, yval, marker = "x", s=1, color=color)
        
    # Set the plot limit
    if 'xmax' in sc_dict : 
        xmax = sc_dict['xmax']
    else :
        xmax = 6000
    
    if 'ymax' in sc_dict : 
        ymax = sc_dict['ymax']
    else :
        ymax = 6000
        
    ax.set(xlim=(0, xmax), ylim=(0, ymax))