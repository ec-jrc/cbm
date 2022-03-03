#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Thu Jul  1 09:58:08 2021


import abc
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt

# this is a temporary solution - maybe
import marker_utils as mu
import copy

"""
Summary:
    Classes and functions for marker definition and processing including
    marker detection.
"""

class base_marker :
    """
    Summary:
        Base class implementing a marker.
    """
    def __init__(self, start_date : datetime.datetime, stop_date : datetime.datetime, \
                 main_date : datetime.datetime = datetime.datetime(2000,1,1), \
                 mtype : str = "base", plot_type = None, color = None) :
        """
        Summary:
            Object constructor.
        
        Arguments :
            start_date - starting date of the marker
            stop_date - stop date of the marker
            main_date - the date at which the main marker event likely occurred.
                        For example, if the marker is related to the detection of 
                        a peak, the date of the peak.
            mtype - type of marker
            plot_type - string allowing one to select different plot configurations
            color - string allowing one to select different colors (for the vertical line plots)
        
        Returns:
            Nothing.
        """
        
        # Set the dates
        self.start_date = start_date
        self.stop_date = stop_date
        
        if main_date == datetime.datetime(2000,1,1) :
            self.main_date = []
        else :
            self.main_date = main_date
            
        # Set the type
        self.type = mtype
        
        # Set initial properties, these should be values of the time series
        # generating the marker
        self.values = np.nan * np.ones(3)
        
        # additional properties
        self.properties = {}
        
        # information for plotting
        self.plot_type = plot_type 
        self.color = color
        
        
    def __str__(self):
        """
        Summary:
            Function used to provide a representation of the marker as string
            
        Arguments:
            None.
            
        Returns :
            A string with the class representation.
        """
        class_descr = self.type + ',' + \
                      self.start_date.strftime('%Y-%m-%d') + ',' + \
                      self.main_date.strftime('%Y-%m-%d') + ',' + \
                      self.stop_date.strftime('%Y-%m-%d') + ',' + \
                      str( self.get_duration_in_days() ) + ',' + \
                      str( self.values[0] ) + ',' + \
                      str( self.values[1] ) + ',' + \
                      str( self.values[2] )
                      
        if len(self.properties) > 0 :
            class_descr = class_descr + ',' + self.properties.__str__()

        return class_descr 
        
    def get_duration_in_days( self ) :
        """
        Summary:
            Get the duration in days of the marker.
            
        Arguments:
            None.
            
        Returns :
            The duration in days of the marker.
        """
        duration = ( self.stop_date - self.start_date).days
            
        return duration

    def plot(self, ax = None ) :
        """
        Summary:
            Plot the marker according to the specified options
            
        Arguments:
            ax - the current axes for the plot
            
        Returns :
            Nothing.
        """
        if ax is None :
            ax = plt.gca()
            
        # Check if some plotting options have been specified
        if self.plot_type is not None :
            if "t" in self.plot_type :
                self.plot_as_triangle(ax)
                
            if "l" in self.plot_type :
                self.plot_as_vertical_line(ax)
        
        else :
            self.plot_as_triangle(ax)


    def plot_as_triangle( self, ax = None ) :
        """
        Summary:
            Plot the marker as a transparent triangle
            
        Arguments:
            ax - the current axes for the plot
            
        Returns :
            Nothing.
        """
        if ax is None :
            ax = plt.gca()
            
        # build the time series to plot
        ind = np.array([self.start_date, self.main_date, self.stop_date])
            
        ts = pd.Series( self.values, index = ind)
        ax.fill( ts, alpha = 0.3 )    

    def plot_as_vertical_line( self, ax = None ) :
        """
        Summary:
            Plot the marker's main date as a vertical line
            
        Arguments:
            ax - the current axes for the plot
            
        Returns :
            Nothing.
        """
        if ax is None :
            ax = plt.gca()
            
        # print(self.type)
            
        ax.axvline(x=self.main_date, lw = 3, color = self.color)        
        ax.text(self.main_date, ax.get_ylim()[0] + 0.1 * (ax.get_ylim()[1] - ax.get_ylim()[0]), \
                self.type, rotation=90, verticalalignment='center', \
                fontsize=15, color = self.color)                

    
    def set_plot_type(self, plot_type) :
        """
        Summary:
            Set the plot type.
        """
        self.plot_type = plot_type
        
    def get_plot_type(self) :
        """
        Summary:
            Get the plot type.
        """
        return self.plot_type    
        
    def set_plot_color(self, color) :
        """
        Summary:
            Set the color of the line for the marker.
        """
        self.color = color

    def overlap_in_days(self, marker) :
        """
        Summary:
            Check the amount of overlapping (in terms of days)
            between two markers
            
        Arguments:
            marker - second marker to check overlapping
            
        Returns :
            The amount of overlapping in days
        """
        if ( self.start_date >= marker.stop_date ) or \
           ( self.stop_date <= marker.start_date) :
               
               # the two events do not overlap
               return 0
           
        # if here the two events overlap
        start_date = max([self.start_date, marker.start_date])
        stop_date = min([self.stop_date, marker.stop_date])
        
        return (stop_date - start_date).days
        
    
    def overlap(self, marker) :
        """
        Summary:
            Check the amount of overlapping (in terms of dates)
            between two markers
            
        Arguments:
            marker - second marker to check overlapping
            
        Returns :
            The amount of overlapping (between 0 and 1)
        """
        overlap = self.overlap_in_days(marker)
        
        over_perc = overlap / self.get_duration_in_days()
        
        return over_perc
    
    def symmetric_overlap(self, marker) :
        overlap = max([self.overlap(marker), marker.overlap(self)])
        
        return overlap
    
    def copy(self) :
        """
        Summary:
            Create a deep copy of the object. 
            
        Arguments:
            None.
            
        Returns :
            A deep copy of the object.
        """
        return copy.deepcopy(self)
        
    def __lt__(self, marker) :
        """
        Summary:
            A marker is "lower" than another if it stops before this
            second one starts
            
        Arguments:
            marker - second marker to check condition
            
        Returns :
            True/False
        """
        return ( self.stop_date < marker.start_date)
    
    def __gt__(self, marker) :
        """
        Summary:
            A marker is "greater" than another if it start after this
            second one stops
            
        Arguments:
            marker - second marker to check condition
            
        Returns :
            True/False
        """
        return ( self.start_date > marker.stop_date)
    
    def __contains__(self, marker) :
        """
        Summary:
            A marker contains another if it starts after this
            second one and stops before
            
        Arguments:
            marker - second marker to check condition
            
        Returns :
            True/False
        """
        a = self.start_date <= marker.start_date
        b = self.stop_date >= marker.stop_date
        
        return  (a and b)
    
    def merge_markers(self, marker) :
        """
        Summary:
            Create a new marker by merging the current marker (self) with a 
            second one
            
        Arguments:
            marker - second marker to check condition
            
        Returns :
            The merged marker.
        """        
        
        start_date = min([self.start_date, marker.start_date])
        stop_date = max([self.stop_date, marker.stop_date])
        
        main_date = self.main_date + (marker.main_date - self.main_date) / 2
        
        m_type = self.type + "-" + marker.type
        
        # Create the new marker
        m_merged = base_marker(start_date, stop_date, main_date, m_type)
        
        return m_merged
    
    def trim_right(self, stop_date):
        """
        Summary:
            Trim the stop date of the marker and adjust the corresponding values
            
        Arguments:
            stop_date - the new stop date
            
        Returns :
            The merged marker.
        """
                    
        if self.stop_date <= stop_date :
            return self
        elif self.start_date >= stop_date :
            raise Exception("marker_aggregator.trim_right() - Empty marker") 
        else :
            m_trim = self.copy()
            m_trim.stop_date = stop_date
            
            if m_trim.main_date > stop_date :
                m_trim.main_date = m_trim.start_date + (m_trim.stop_date - m_trim.start_date) / 2
                
                # Now interpolate the values
                slope = ( self.values[1] - self.values[0] ) / (self.main_date - self.start_date).days
                m_trim.values[1] = self.values[0] + slope * (m_trim.main_date - self.start_date).days
                m_trim.values[2] = self.values[0] + slope * (m_trim.stop_date - self.start_date).days
            else :
                # interpolate only the stop value
                slope = ( self.values[2] - self.values[1] ) / (self.stop_date - self.main_date).days
                m_trim.values[2] = self.values[1] + slope * (m_trim.stop_date - self.main_date).days
        
        return m_trim
                
    def trim_left(self, start_date):
        """
        Summary:
            Trim the start date of the marker and adjust the corresponding values
            
        Arguments:
            start_date - the new start date
            
        Returns :
            The merged marker.
        """
        if self.start_date >= start_date :
            return self
        elif self.stop_date <= start_date :
            raise Exception("marker_aggregator.trim_left() - Empty marker") 
        else :
            m_trim = self.copy()
            m_trim.start_date = start_date
            
            if m_trim.main_date < start_date :
                m_trim.main_date = m_trim.start_date + (m_trim.stop_date - m_trim.start_date) / 2
                
                # Now interpolate the values
                slope = ( self.values[2] - self.values[1] ) / (self.stop_date - self.main_date).days
                m_trim.values[1] = self.values[1] + slope * (m_trim.main_date - self.main_date).days
                m_trim.values[2] = self.values[1] + slope * (m_trim.stop_date - self.main_date).days
            else :
                # interpolate only the start value
                slope = ( self.values[1] - self.values[0] ) / (self.main_date - self.start_date).days
                m_trim.values[0] = self.values[0] + slope * (m_trim.start_date - self.start_date).days
        
        return m_trim
    
class base_marker_detector(metaclass = abc.ABCMeta) :
    """
    Summary :
        Abstract class defining the basic interfaces for all the derived 
        classes. It defines a generic marker detector. It takes a time series
        an generates a sequence of markers
    """
    def __init__(self, start_date : datetime.datetime, stop_date : datetime.datetime, \
                 signal_type : list ) :
        """
        Summary :
            Object constructor.
            
        Arguments:
            start_date - start date for the processing of the time series.
            stop_date - last date to consider for the processing of the time series.
            signal_type - list of strings indicating the time series to process
            
        Returns:
            Nothing.
        """
        self.start_date = start_date
        self.stop_date = stop_date 
        
        self.signal_type = signal_type
        
    @abc.abstractmethod    
    def get_markers(self, ts : dict) -> dict :
        """
        Summary :
            Process the dictionary with the different time series and return
            a sequence of markers.
            
        Arguments:
            ts - dictionary of time series.
            
        Returns:
            Dictionary with sequences of markers. The keys of the dictionary
            are the different signals processed.
        """
        return
    
    def get_markers_from_dates(self, start_dates, stop_dates, main_dates,\
                               start_values, stop_values, main_values) :
        """
        Summary :
            Build the list of markers from the dates
            
        Arguments:
            start_dates - array of start dates.
            stop_dates - array of stop dates.
            main_dates - array of main dates.
            start_values - array of values corresponding to the start dates 
            stop_values - array of values corresponding to the stop dates
            main_values - array of values corresponding to the main dates
        
        Returns:
            List of markers.
        """
        out_markers = []
        
        
        for ii, start_date in enumerate(start_dates) :
            marker = base_marker(start_date, stop_dates[ii], \
                                 main_dates[ii], self.marker_type)
                
            marker.values[0] = start_values[ii]
            marker.values[1] = main_values[ii]
            marker.values[2] = stop_values[ii]
            out_markers.append(marker)
        
        return out_markers

    def get_markers_from_start_stop(self, start_dates, stop_dates, start_values, stop_values) :
        """
        Summary :
            Build the list of (gap) markers from the start and stop dates
            
        Arguments:
            start_dates - array of start dates.
            stop_dates - array of stop dates.
            start_values - array of values corresponding to the start dates 
            stop_values - array of values corresponding to the stop dates
            
        Returns:
            List of markers.
        """
        out_markers = []
        
        if (len(start_dates) == 0) or (len(stop_dates) == 0) :
            return out_markers
            
        for ii, start_date in enumerate(start_dates) :
            main_date  = start_date + (stop_dates[ii] - start_date) / 2
            marker = base_marker(start_date, stop_dates[ii], \
                                 main_date, self.marker_type)
                
            marker.values[0] = start_values[ii]
            marker.values[2] = stop_values[ii]
            out_markers.append(marker)
        
        return out_markers

class drop_detector(base_marker_detector) :
    """
    Summary:
        Detect drops in a time series.
    """
    def __init__(self, start_date : datetime.datetime, stop_date : datetime.datetime, \
                 signal_type : list, max_number : int, min_duration = -1, \
                 min_drop = -1, agg_number : int = 0, filter_by_angle : bool = False, \
                 by_date = False ) :
        """
        Summary:
            Object constructor.
        
        Arguments:
            start_date - the start date to consider when analysing the time series
            stop_date - the stop date to consider when analysing the time series
            signal_type - list of strings indicating the time series to process
            max_number - maximum number of markers to find
            agg_number - if different from zero, perform aggregation 'agg_number' of
                         times
            filter_by_angle - remove markers based on angle conditions
            by_date - if true tells to take only the first marker occurring in chronological 
                     order
        
        Returns :
            Nothing.
        """
        
        # call the basic constructor
        super().__init__(start_date, stop_date, signal_type )
        
        # set the other parameters
        self.max_number = max_number
        
        self.agg_number = agg_number
        
        self.filter_by_angle = filter_by_angle
        
        self.marker_type = "drop"
        
        self.min_duration = min_duration
        
        self.min_drop = min_drop
        
        self.sort = not by_date
        
    def get_markers(self, ts : dict) -> dict :
        """
        Summary :
            Process the dictionary with the different time series and return
            a sequence of markers.
            
        Arguments:
            ts - dictionary of time series.
            
        Returns:
            Dictionary with sequences of markers. The keys of the dictionary
            are the different signals processed.
        """
        # output dictionary
        out_dict = {}
        
        # loop on the different signals to process
        for signal in self.signal_type : 
            
            if signal not in ts :
                continue
            
            # Extract the data frame
            df = ts[signal]
            
            # Process all components
            components = list(df.columns)
            
            for component in components :
                
                time_series = df[component]
                
                # search for features in the time series    
                features = mu.get_extrema_features(time_series, self.max_number, \
                                                   self.start_date, self.stop_date, \
                                                   self.sort)

                # ... and aggregate them
                for ii in range(self.agg_number) :
                    features = mu.aggregate_extrema_angle(features)
                
                # check if the criteria in duration are met
                if self.min_duration != -1 :
                    features = mu.filter_by_duration(features, self.min_duration)
                if features is None :
                    continue
                
                if self.min_drop != -1 :
                    features = mu.filter_by_drop(features, self.min_drop)    
                if features is None :
                    continue
                
                if self.filter_by_angle :
                    features = mu.filter_events_based_on_angle(features)
                if features is None :
                    continue
                
                # convert "features" to markers
                markers = mu.features_to_markers(features, self.marker_type)
                
                if len(components) > 1 :
                    marker_name = signal + '_' + components
                else :
                    marker_name = signal
                
                out_dict[marker_name] = markers
        
        return out_dict
        
class peak_detector(base_marker_detector) : 
    """
    Summary:
        Detect peak in a time series. It essentially the same as a drop detector
        operating on the negative time series.
    """
    def __init__(self, start_date : datetime.datetime, stop_date : datetime.datetime, \
                 signal_type : list, max_number : int, min_duration = -1, \
                 min_drop = -1, agg_number : int = 0, filter_by_angle : bool = False, \
                 by_date = False ) :
        """
        Summary:
            Object constructor.
        
        Arguments:
            start_date - the start date to consider when analysing the time series
            stop_date - the stop date to consider when analysing the time series
            signal_type - list of strings indicating the time series to process
            max_number - maximum number of markers to find
            agg_number - if different from zero, perform aggregation 'agg_number' of
                         times
            filter_by_angle - remove markers based on angle conditions
            by_date - if true tells to take only the first marker occurring in chronological 
                     order
        Returns :
            Nothing.
        """
        
        # call the basic constructor
        super().__init__(start_date, stop_date, signal_type )
        
        # set the other parameters
        self.max_number = max_number
        
        self.agg_number = agg_number
        
        self.filter_by_angle = filter_by_angle
        
        self.marker_type = "peak"
        
        self.min_duration = min_duration
        
        self.min_drop = min_drop

        self.sort = not by_date        

    def get_markers(self, ts : dict) -> dict :
        """
        Summary :
            Process the dictionary with the different time series and return
            a sequence of markers.
            
        Arguments:
            ts - dictionary of time series.
            
        Returns:
            Dictionary with sequences of markers. The keys of the dictionary
            are the different signals processed.
        """
        # output dictionary
        out_dict = {}
        
        # loop on the different signals to process
        for signal in self.signal_type : 
            
            if signal not in ts :
                continue
            
            # Extract the data frame
            df = ts[signal]
            
            # Process all components
            components = list(df.columns)
            
            for component in components :
                
                time_series = -df[component]
                
                # search for features in the time series    
                features = mu.get_extrema_features(time_series, self.max_number, \
                                                   self.start_date, self.stop_date, \
                                                   self.sort )
    
                # ... and aggregate them
                for ii in range(self.agg_number) :
                    features = mu.aggregate_extrema_angle(features)
                
                # check if the criteria in duration are met
                if self.min_duration != -1 :
                    features = mu.filter_by_duration(features, self.min_duration)
                if features is None :
                    continue
                
                if self.min_drop != -1 :
                    features = mu.filter_by_drop(features, self.min_drop)    
                if features is None :
                    continue
                
                if self.filter_by_angle :
                    features = mu.filter_events_based_on_angle(features)
                if features is None :
                    continue
                
                # convert "features" to markers
                markers = mu.features_to_markers(-features, self.marker_type)
                
                if len(components) > 1 :
                    marker_name = signal + '_' + components
                else :
                    marker_name = signal
                
                out_dict[marker_name] = markers
        
        return out_dict  

class state_change_detector(base_marker_detector) :
    """
    Summary:
        Detect a transition to a state in a time series.
    """
    def __init__(self, start_date : datetime.datetime, stop_date : datetime.datetime, \
                 signal_type : list, max_number : int, target_state : int, 
                 min_duration = -1 ) :
        """
        Summary:
            Object constructor.
        
        Arguments:
            start_date - the start date to consider when analysing the time series
            stop_date - the stop date to consider when analysing the time series
            signal_type - list of strings indicating the time series to process
            max_number - maximum number of markers to find
            target_state - the state that should be reached during the change
            min_duration - minimum duration of the event
                    
        Returns :
            Nothing.
        """
        # call the basic constructor
        super().__init__(start_date, stop_date, signal_type )
        
        self.target_state = target_state
        self.max_number = max_number
        self.marker_type = "state_change"
        self.min_duration = min_duration
        
        return
    
    def get_markers(self, ts : dict) -> dict :
        """
        Summary :
            Process the dictionary with the different time series and return
            a sequence of markers.
            
        Arguments:
            ts - dictionary of time series.
            
        Returns:
            Dictionary with sequences of markers. The keys of the dictionary
            are the different signals processed.
        """
        # output dictionary
        out_dict = {}
        
        # loop on the different signals to process
        for signal in self.signal_type : 
            
            if signal not in ts :
                continue
            
            # Extract the data frame
            df = ts[signal]
            
            # Process all components
            components = list(df.columns)
            
            for component in components :
                
                # consider data only in the specified time range
                time_series = df[(df.index >= self.start_date) & (df.index <= self.stop_date)]
                
                # Check if there are data, otherwise continue
                if len(time_series) == 0 :
                    continue
                
                # find indeces with values equal to state of interest and coming 
                # from a different state
                start_ind = np.argwhere((time_series.values.flatten()[:-1] != self.target_state) & \
                                        (time_series.values.flatten()[1:] == self.target_state)).flatten()
                    
                stop_ind = np.argwhere((time_series.values.flatten()[:-1] == self.target_state) & \
                                       (time_series.values.flatten()[1:] != self.target_state)).flatten()
                stop_ind +=1
                
                # check boundary conditions
                if time_series.values.flatten()[0] == self.target_state :
                    start_ind = np.insert(start_ind, 0, 0)
                    
                if time_series.values.flatten()[-1] == self.target_state :
                    stop_ind = np.append(stop_ind, len(time_series.values.flatten()))
                
                # Now find the events
                start_dates = []
                stop_dates = []
                main_dates = []
                
                start_values = []
                stop_values = []
                main_values = []
                
                for jj, start_ii in enumerate(start_ind) :
                    
                    stop_ii = stop_ind[jj]
                    
                    if start_ii == 0 :
                        start_date = time_series.index[start_ii]
                    else :
                        start_date = time_series.index[start_ii] + \
                            (time_series.index[start_ii+1] - time_series.index[start_ii]) / 2
                    
                    
                    if stop_ii == len(time_series.values.flatten()) :
                        stop_date = time_series.index[stop_ii-1]
                        stop_value = time_series.values.flatten()[stop_ii-1]
                    else :
                        stop_date = time_series.index[stop_ii] - \
                            (time_series.index[stop_ii] - time_series.index[stop_ii-1]) / 2
                        stop_value = time_series.values.flatten()[stop_ii]

                    if (stop_date - start_date).days >= self.min_duration :                    
                        start_dates.append(start_date)
                        start_values.append(time_series.values.flatten()[start_ii])
                        stop_dates.append(stop_date)
                        stop_values.append(stop_value)                    
                        
                        main_date = start_date + (stop_date - start_date) / 2
                        main_dates.append(main_date)
                        main_values.append(self.target_state)
                
                # get the gap markers
                markers = super().get_markers_from_dates(start_dates, stop_dates, \
                                                     main_dates, start_values, \
                                                     stop_values, main_values)
            
                out_dict[signal] = markers
        
        return out_dict
    
class threshold_detector(base_marker_detector) :
    """
    Summary:
        Detector used to identify time intervals when a signal is above (below)
        a pre-defined threshold.
    """
    def __init__(self, start_date : datetime.datetime, stop_date : datetime.datetime, \
                 signal_type : list, threshold : float, above : False ) :
        
        """
        Summary:
            Object constructor.
            
        Arguments:
            start_date - start date for the processing of the time series.
            stop_date - last date to consider for the processing of the time series.
            signal_type - list of strings indicating the time series to process
            threshold - threshold used for the signal comparison
            above - tells if the signal should be above or below the threshold.
            
        Returns:
            Nothing.
        """
        super().__init__(start_date, stop_date, signal_type)
        
        self.threshold = threshold
                
        self.above = above
        
        self.marker_type = "threshold"
        
    def get_markers(self, ts : dict) -> dict :
        """
        Summary :
            Process the dictionary with the different time series and return
            a sequence of markers.
            
        Arguments:
            ts - dictionary of time series.
            
        Returns:
            Dictionary with sequences of markers. The keys of the dictionary
            are the different signals processed.
        """
        # output dictionary
        out_dict = {}
        
        # loop on the different signals to process
        for signal in self.signal_type : 
            
            if signal not in ts :
                continue
            
            # Extract the data frame
            full_df = ts[signal]
            
            # filter it with respect to the start and stop date
            if 'Date' in full_df :
                df = full_df[(full_df['Date'].values >= self.start_date) & \
                             (full_df['Date'].values <= self.stop_date)]
                dates = df['Date']
                
            else :
                df = full_df[(full_df.index >= self.start_date) & \
                             (full_df.index <= self.stop_date)]
                dates = df.index    
    
            # Process all components
            components = list(df.columns)
            
            for component in components :
                # find dates when threshold crossing occurs
                values = df[components].values
                
                if self.above :
                    th_values = (values > self.threshold)
                else :
                    th_values = (values < self.threshold)
                
                start_dates = []
                stop_dates = []
                start_values = []
                stop_values = []
                
                start_date = self.start_date
                stop_date = None
                start_val = 0
                stop_val =0
                
                previous_valid = False
                
                for ii, val in enumerate(th_values) :
                    if val == True :
                        if previous_valid == False :
                            previous_valid = True
                    else :
                        if previous_valid == False :
                            # advance the start date
                            start_date = dates[ii]
                            start_val = values[ii]
                        else :
                            stop_date = dates[max([ii - 1, 0])]
                            stop_val = values[max([ii - 1, 0])]
                            previous_valid = False
                            
                            # Add values for the creation of the marker
                            start_dates.append(start_date)
                            stop_dates.append(stop_date)
                            start_values.append(start_val)
                            stop_values.append(stop_val)
                            
                # create the markers
                markers = self.get_markers_from_start_stop(start_dates, stop_dates, start_values, stop_values)
                
                if len(components) > 1 :
                    marker_name = signal + '_' + components
                else :
                    marker_name = signal
                
                out_dict[marker_name] = markers
            # end loop on components
        # end loop on signal
        return out_dict
                
class gap_detector(base_marker_detector) :
    """
    Summary:
        Identifies data gaps in a time series. The data gap should be 
        larger than a minimum duration.
    """
    def __init__(self, start_date : datetime.datetime, stop_date : datetime.datetime, \
                 signal_type : list, min_gap_duration : int ) :
        """
        Summary :
            Object constructor.
            
        Arguments:
            start_date - start date for the processing of the time series.
            stop_date - last date to consider for the processing of the time series.
            signal_type - list of strings indicating the time series to process
            min_gap_duration - minimum duration in days of the data gap 
            
        Returns:
            Nothing.
        """
        super().__init__(start_date, stop_date, signal_type)
        
        self.min_gap_duration = min_gap_duration
        
        self.marker_type = "gap"
        
    def get_markers(self, ts : dict) -> dict :
        """
        Summary :
            Process the dictionary with the different time series and return
            a sequence of markers.
            
        Arguments:
            ts - dictionary of time series.
            
        Returns:
            Dictionary with sequences of markers. The keys of the dictionary
            are the different signals processed.
        """
        # output dictionary
        out_dict = {}
        
        # loop on the different signals to process
        for signal in self.signal_type : 
            
            if signal not in ts :
                continue
            
            # Extract the data frame
            full_df = ts[signal]
            
            # filter it with respect to the start and stop date
            if 'Date' in full_df :
                df = full_df[(full_df['Date'].values >= self.start_date) & \
                             (full_df['Date'].values <= self.stop_date)]
                dates = df['Date']
                
            else :
                df = full_df[(full_df.index >= self.start_date) & \
                             (full_df.index <= self.stop_date)]
                dates = df.index    
                
            # look for data gaps
            delta_days = (dates[1:] - dates[:-1]).days
            
            ind = delta_days > self.min_gap_duration
            
            start_dates = dates[:-1][ind]
            stop_dates = dates[1:][ind]
            
            start_values = df.values[:-1][ind]
            stop_values = df.values[1:][ind]
            
            # get the gap markers
            markers = self.get_markers_from_start_stop(start_dates, stop_dates, start_values, stop_values)
            
            out_dict[signal] = markers
            
        return out_dict
    


class marker_detector_factory :
    """
    Summary :
        Class responsible for the creation of the marker detectors
    """
    
    def get_marker_detectors(self, options) :
        """
        Summary:
           Create a lits of marker detectors for the time series processing.
           Each marker detector works in parallel.
           
        Arguments:
            options - dictionary with the options for the creation of the different
                      marker detectors.
        Returns:
            A list of marker detectors.
        """
        
        # first check if the related options are available
        if "marker-detectors" not in options :
            raise Exception("marker_detector_factory.get_marker_detectors() - missing options")
        
        mk_detect_list = []
        
        for md_opt in options["marker-detectors"] :
            
            mk_detect_list.append(self.get_detector(md_opt))
            
        return mk_detect_list
    
    def get_detector(self, option) :
        """
        Summary:
           Create a single marker detector.
           
        Arguments:
            options - dictionary with the options for the creation of the marker 
                    detector.
        Returns:
            A marker detector.
        """
        
        # get the start date
        if "start_date" not in option :
            raise Exception("marker_detector_factory.get_detector() - start date missing")
        
        start_date = pd.to_datetime(option["start_date"])
        
        # get the stop date
        if "stop_date" not in option :
            raise Exception("marker_detector_factory.get_detector() - stop date missing")
        
        stop_date = pd.to_datetime(option["stop_date"])
        
        # get the detector type
        if "type" not in option :
            raise Exception("marker_detector_factory.get_detector() - type missing")
        
        mdtype = option["type"]

        # get the signal list
        if "signals" not in option :
            raise Exception("marker_detector_factory.get_detector() - signal not specified")
        
        signals = option["signals"]

        # now build the detector depending on the types
        if mdtype == "drop-detector" :
            
            max_number = 10
            if "max_number" in option :
                max_number = option["max_number"]
            
            agg_number = 0
            if "aggregate" in option :
                agg_number = option["aggregate"]
                
            filter_by_angle = False
            if "filter_by_angle" in option :
                filter_by_angle = option["filter_by_angle"]
            
            min_duration = -1
            if "min_duration" in option :
                min_duration = option["min_duration"]
                
            min_drop = -1
            if "min_drop" in option :
                min_drop = option["min_drop"]
            
            detector = drop_detector(start_date, stop_date, signals, max_number, \
                                     min_duration, min_drop, agg_number, filter_by_angle ) 

        elif mdtype == "peak-detector" :
            
            max_number = 10
            if "max_number" in option :
                max_number = option["max_number"]
            
            agg_number = 0
            if "aggregate" in option :
                agg_number = option["aggregate"]
                
            filter_by_angle = False
            if "filter_by_angle" in option :
                filter_by_angle = option["filter_by_angle"]
            
            min_duration = -1
            if "min_duration" in option :
                min_duration = option["min_duration"]
                
            min_increase = -1
            if "min_increase" in option :
                min_increase = option["min_increase"]
            
            detector = peak_detector(start_date, stop_date, signals, max_number, \
                                     min_duration, min_increase, agg_number, filter_by_angle )
        
        elif mdtype == "data-gaps" :
            
            min_gap_len = 20
            if "min_gap_len" in option :
                min_gap_len = option["min_gap_len"]
                
            detector = gap_detector(start_date, stop_date, signals, min_gap_len)
        
        elif mdtype == "state_change" :
            
            to_state = -1
            if "to_state" in option :
                to_state = option["to_state"]
            else :
                raise("get_detector() : missing state")
               
            max_number = 10
            if "max_number" in option :
                max_number = option["max_number"]
            
            min_duration = -1
            if "min_duration" in option :
                min_duration = option["min_duration"] 
            
            detector = state_change_detector(start_date, stop_date, signals, \
                                             max_number, to_state, min_duration )            
        elif mdtype == "threshold" :
            above = False
            if "above" in option :
                above = option["above"]
                
            threshold = 0
            if "threshold" in option :
                threshold = option["threshold"]
                
            detector = threshold_detector(start_date, stop_date, signals, threshold, above)
        else :
            raise Exception("marker_detector_factory.get_detector() - type not supported")
        
        return detector
