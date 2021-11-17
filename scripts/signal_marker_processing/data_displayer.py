#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import gc

from get_time_series import convert_string_to_filename
import pandas as pd
import numpy as np
import os


class data_displayer :
    """
    Summary:
        Object responsible for making summary graphs.
    """
    
    def __init__(self, options : dict) :
        """
        Summary:
            Object constructor.
        
        Arguments:
            option - dictionary with the options to initialize the object
            
        Returns:
            Nothing.
        """
        
        plt.ioff()
                
        # get the list of signals to plot
        self.signals = []
        if "signals" in options :
            self.signals = options["signals"]
            
        # check if a component should be plotted in the bottom bar
        if "bottom_bar" in options :
            self.has_bottom_bar = True
            self.bottom_signal = options["bottom_bar"]
            self.bottom_components = options["bottom_bar_components"]
        else :
            self.has_bottom_bar = False
        
        if "start_date" in options :
            self.start_date = pd.to_datetime(options["start_date"])
        else :
            self.start_date = None
            
        if "stop_date" in options :
            self.stop_date = pd.to_datetime(options["stop_date"])
        else :
            self.stop_date = None
            
        if "output_folder" in options :
            self.outfolder = options["output_folder"]
        else :
            self.outfolder = "./results"
        
        # In the optic of having several displayer, a prefix can be added
        # to the output file names in order to have different outputs
        if "file_name_prefix" in options :
            self.file_name_prefix = options["file_name_prefix"]
        else :
            self.file_name_prefix = None
        
        # This is a lazy solution
        self.other_options = options
        
        # create the output directory if it does not exist
        if not os.path.exists(self.outfolder) :
            os.makedirs(self.outfolder)
            
    def plot(self, ts : dict, markers : dict) :
        """
        Summary :
            Make the summary plot.
            
        Arguments:
            ts - dictionary of time series to plot.
            markers - dictionary of markers
        
        Returns:
            Nothing.
        """
        if 'bar_height_ratio' in self.other_options :
            height_ratios = self.other_options['bar_height_ratio']
        else :
            height_ratios = [8, 1]
        
        if self.has_bottom_bar :
            fig, ax = plt.subplots(2, 1, gridspec_kw={'height_ratios': height_ratios})
        else :
            fig, ax = plt.subplots()
            ax = [ax]

        if len(self.signals) == 0:
            self.signals = list(ts.keys())

        # plot the time series
        for key in self.signals :
            if key in ts :
                ts[key].plot(ax=ax[0])
                
        if "ylim" in self.other_options :
            ax[0].set_ylim(self.other_options["ylim"])
                
        
        # look for the bottom bar
        if self.has_bottom_bar :
            if self.bottom_signal in ts :
                df = ts[self.bottom_signal]
                nb_points = len(df)                
                bottom_bar = np.ones((1, nb_points, 3), dtype=np.uint8)                        
                
                ii = 0
                for component in self.bottom_components :
                    bottom_bar[0,:,ii] = df[component].values.astype(np.uint8)
                    ii += 1

                xextent = mdates.date2num([df.index[0], df.index[-1]])
                ax[1].imshow( bottom_bar, extent = [xextent[0], xextent[1],  0, 1], aspect = 'auto' )
                ax[1].xaxis_date()
                ax[1].tick_params(labelsize=12)
                ax[1].set_xlim([self.start_date, self.stop_date])
                ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax[1].yaxis.set_visible(False)
                fig.autofmt_xdate() # Rotation
        
        # Plot the markers
        if "marker_signals" in self.other_options :
            signals = self.other_options["marker_signals"]
        else:
            signals = self.signals
        
        for key in markers :
            if key in signals :
                for marker in markers[key] :
                    # Check if specific options have been provided for plotting the marker
                    previous_plot_type = None
                    
                    if "marker_plot_type" in self.other_options :
                        previous_plot_type = marker.get_plot_type()
                        marker.set_plot_type(self.other_options["marker_plot_type"])
                    
                    if "marker_colors" in self.other_options :
                        color_dict = self.other_options["marker_colors"]
                        if marker.type in color_dict :
                            marker.set_plot_color(color_dict[marker.type])
                    
                    marker.plot(ax[0])
                    
                    if "marker_plot_type" in self.other_options :
                        marker.set_plot_type(previous_plot_type)
         
        if ("add_months" in self.other_options) and (self.other_options["add_months"]) :
            data_displayer.add_months(ax[0], self.start_date, self.stop_date)    
        
        if "legend" in self.other_options :
            ax[0].legend(self.other_options["legend"], fontsize = 14)
        else :
            ax[0].legend(fontsize = 14)
        
        if "ylabel" in self.other_options :
            ax[0].set_ylabel(self.other_options["ylabel"], fontsize = 14)    
        
        ax[0].set_xlim([self.start_date, self.stop_date])
        ax[0].grid( color='k', linestyle='--', linewidth=0.5)     # add the grid     
        ax[0].tick_params(labelsize=12)
        ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax[0].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        
        fig.autofmt_xdate() # Rotation
        
        # Force garbage collection
        gc.collect()
            
        return fig, ax
    
    def dump_to_file(self, ts : dict, markers : dict, fid ) :
        """
        Summary :
            Make the summary plot and dump it to file.
            
        Arguments:
            ts - dictionary of time series to plot.
            markers - dictionary of markers.
            filename - string with the name of the image that will be generated
                       by the data displayer.
        
        Returns:
            Nothing.
        """
        # Dump the information extracted and make summary graphs
        fig, ax = self.plot(ts, markers)
            
        # These is the standard power point size
        fig.set_size_inches(13.33, 7.5)  
        plt.tight_layout()
        
        # build the file name
        if self.file_name_prefix is not None :
            filename = self.file_name_prefix + '_' + convert_string_to_filename(fid) + '.png'
        else :
            filename = convert_string_to_filename(fid) + '.png'
        
        if "image_resolution" in self.other_options :
            img_res = self.other_options["image_resolution"]
        else :
            img_res = 100
                    
        fig.savefig(self.outfolder + '/' + filename, dpi = img_res)
        
        plt.cla()
        plt.clf()
        plt.close("all")
        
        gc.collect()
    
        return

    @staticmethod
    def get_current_list_of_months(first_year_month, number_of_year_months):
        """
        Summary :
            Provides a list of strings with the year and month starting from
            an initial year/month pair and the given a number of elements,
            
        Author :
            Csaba Wirnhardt. 
            Modified by Daniele Borio.
        """
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL","AUG", "SEP", "OCT",\
                  "NOV", "DEC"]

        year = int(int(first_year_month) / 100)
        month_index = ( int(first_year_month) % 100 ) - 1
    
        current_textstrs = []
        for i in range(number_of_year_months):
            current_textstrs.append(str(year) + "\n" + months[month_index])
            month_index += 1
            month_index %= 12
            if month_index == 0 :
                year += 1
    
        return current_textstrs 
    
    @staticmethod
    def add_months(ax, start_date, stop_date) :
        """
        Summary :
            Add month headers on the top of the plot.
            
        Author :
            Csaba Wirnhardt
        """
        min_month = start_date.month
        min_year = start_date.year

        min_year_month = str(min_year) + ('0' + str(min_month))[-2:]        
        number_of_months = (stop_date.year - start_date.year) * 12 + stop_date.month - start_date.month  + 1

        step_x = 1/number_of_months

        start_x = step_x/2  # positions are in graph coordinate system between 0 and 1
                            # so first year_month label is at half the size of the widht of
                            # one month
        loc_y = 0.915
        
        current_year_month_text = data_displayer.get_current_list_of_months(min_year_month, \
                                                                            number_of_months)
        
        for current_year_month_index in range (number_of_months):
            t = current_year_month_text[current_year_month_index]
            loc_x = start_x + (current_year_month_index) * step_x
            ax.text(loc_x, loc_y, t, verticalalignment='bottom', \
                    horizontalalignment='center', transform=ax.transAxes, \
                    color='blue', fontsize=13)  
    
class data_displayer_factory :
    """
    Summary:
        Object responsible for creating the data displayers.
    """
    
    def get_data_displayers(self, options) :
        """
        Summary:
           Create a lits of data displayers for the generation of the graphical output.
           
        Arguments:
            options - dictionary with the options for the creation of the different
                      data displayers.
        Returns:
            A list of data displayers.
        """
        
        data_displayer_list = []
        # Several data displayers are foreseen and a list of options is expected
        if "data-displayers" in options :
            for doptions in options["data-displayers"] :
                data_displayer_list.append(self.get_displayer(doptions))
                
        # A single data displayer is expected and with a single option dictionary
        # This option is left for back-compatibility
        elif "data-displayer" in options :
            data_displayer_list.append(self.get_displayer(options["data-displayer"]))

        else :
            raise Exception("marker_detector_factory.get_marker_detectors() - missing options")
                    
        return data_displayer_list
    
    def get_displayer(self, options) :
        """
        Summary:
           Returns a single data displayer.
           
        Arguments:
            options - dictionary with the options for the creation of the data displayer.
            
        Returns:
            A data displayer.
        """
        
        # The type of data displayer has been specified (for future development)
        # At the moment only 1 type exists
        if "type" in options :
            if options["type"] == "standard" :
                data_disp = data_displayer( options )
            
            # elif options["type"] == "" :
            # add here other types
            else :
                raise Exception("data_displayer_factory - get_displayer() - unsupported type")
        else:
            data_disp = data_displayer( options )
            
        return data_disp
