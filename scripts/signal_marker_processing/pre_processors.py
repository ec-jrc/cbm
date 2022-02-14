#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import abc
import pandas as pd
import numpy as np
from scipy import signal as sig

import warnings
import gc

# for the KNN classifier
from sklearn.neighbors import KNeighborsClassifier

"""
Summary:
    Classes implementing different pre-processing operations on the time series.
    Each class takes time series (pandas data frame) as input and returns new time series.
"""

class base_pre_processor(metaclass = abc.ABCMeta) :
    """
    Summary :
        Base class defining the main interfaces for time-series pre-processors
    """
    
    def __init__(self, signals, components = [], outnames = []) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            outnames - names to associate to the output data frames
        
        Returns:
            Nothing.
        """
        self.signals = signals
        self.components = components
        self.outnames = outnames
        
       
    @abc.abstractmethod
    def process(self, ts : dict ) -> dict :
        """
        Summary :
            Process the data provided as input.
        
        Arguments :
            ts - time series stored in a dictionary. The dictonary has as keys the
                 signals available and as values the related data frames
        
        Returns :
            processed time series as a dictionary
        """
        return

class all_pass(base_pre_processor) :
    """
    Summary :
        Pass the time series unchanged.
    """    
    def process(self, ts : dict ) -> dict :
        """
        Summary :
            Process the data provided as input.
        
        Arguments :
            ts - time series stored in a dictionary. The dictonary has as keys the
                 signals available and as values the related data frames
        
        Returns :
            processed time series as a dictionary
        """
        
        out_dict = {}
        
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())
        
        ii = 0
        for signal in self.signals :
            
            # Now generates the final data frame
            out_ts = ts[signal][self.components].copy()
            
            if 'Date' in ts[signal] :
                out_ts.set_index(ts[signal]['Date'], inplace=True)
            
            if len(self.outnames) > ii :
                out_dict[self.outnames[ii]] = out_ts
            else :
                out_dict[signal] = out_ts
            ii += 1
            
        return out_dict

class data_filter(base_pre_processor) :
    """
    Summary :
        Remove data points based on a threshold.
    """
    def __init__(self, signals, components, outnames, by, criterion, threshold) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            by - column to be used to filter the data (the condition will be 
                 applied on this column)
         	criteria - type of condition to apply (greater or lower)
			threshold -  threshold to apply	

        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)
        
        self.by = by
        
        self.criterion = criterion
        
        self.threshold = threshold
    
    def process(self, ts : dict ) -> dict :
        """
        Summary :
            Process the data provided as input. Filter the time series with respect
            to the attribute 'by'
        
        Arguments :
            ts - time series stored in a dictionary. The dictonary has as keys the
                 signals available and as values the related data frames
        
        Returns :
            processed time series as a dictionary
        """
        out_dict = {}
        
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())
        
        ii = 0
        for signal in self.signals :
            
            # find the indexes for which the condition is valid
            if self.criterion == 'greater' :
                ind = ts[signal][self.by].values <= self.threshold
            elif self.criterion == 'greater_equal' :
                ind = ts[signal][self.by].values < self.threshold
            elif self.criterion == 'lower' :
                ind = ts[signal][self.by].values >= self.threshold
            elif self.criterion == 'lower_equal' :
                ind = ts[signal][self.by].values >= self.threshold
            elif self.criterion == 'equal' :
                ind = ts[signal][self.by].values != self.threshold
            elif self.criterion == 'not_equal' :
                ind = ts[signal][self.by].values == self.threshold
            else :
                raise Exception("data_filter - process(): unsupported criterion")
                
                
            if len(self.components) == 0 :
                out_ts = ts[signal][ind].copy()
                
            else :
                out_ts = ts[signal][self.components][ind].copy()
                        
            if len(self.outnames) > ii :
                out_dict[self.outnames[ii]] = out_ts
            else :
                out_dict[signal] = out_ts
            ii += 1
            
        return out_dict

class index_adder(base_pre_processor) :
    """
    Summary :
        Add an additional component (column) to a dataframe. The component is
        a function of already existing components in the dataframe.
    """
    def __init__(self, signals, components, outnames, as_, function ) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            outnames - names of the output time series (dataframe)

            as_ - name of the new column

            function - string identifing the function to use to compute the
                       new index
        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)
        
        self.col_name = as_
        
        self.function = function
        
        return
    
    @staticmethod
    def diff_div_by_sum(x, y) :
        
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
        
            rval = (x - y) / (x + y)
            
        return rval 
    
    # ADD other functions here
    
    def process(self, ts : dict ) -> dict :
        """
        Summary :
            Process the data provided as input. Add a new component to the
            dataframe
        
        Arguments :
            ts - time series stored in a dictionary. The dictonary has as keys the
                 signals available and as values the related data frames
        
        Returns :
            processed time series as a dictionary
        """
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())
        
        # only one signal is assumed
        data = ts[self.signals[0]]
        
        if self.function == "diff_div_by_sum" :
            new_component = index_adder.diff_div_by_sum(data[self.components[0]].values, 
                                                        data[self.components[1]].values)            
        # add other options here
        # elif self.function == "":
        else :
            raise Exception("index_adder.process() - unknown function")
        
        data[self.col_name] = new_component
        
        if len(self.outnames) > 0 :
            out_dict = {self.outnames[0] : data}
        else :
            out_dict = {self.signals[0] : data}
                
        return out_dict
                        
class data_merger(base_pre_processor) :
    """
    Summary:
        Merge two data frames with respect to the date.
        The data frames need to have the same date. 
        Note: this processor needs additional work.
    """
    
    def __init__(self, signals, components, outnames) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            outname - output names.
            
        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)
        
    def process(self, ts : dict ) -> dict :
        """
        Summary :
            Process the data provided as input. Merge the time series with respect
            to the date used as index
        
        Arguments :
            ts - time series stored in a dictionary. The dictonary has as keys the
                 signals available and as values the related data frames
        
        Returns :
            processed time series as a dictionary
        """
        out_dict = {}
        
        
        
        # if not defined, all the signals in the time series should be processed
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())
        
        # Keep only common elements
        self.signals = list(set(self.signals) & set(list(ts.keys())))
        
        # at least two signals should be present
        if len(self.signals) < 2 :
            raise Exception("data_merger - process(): at least two signals should be specified")
            
        # first component
        data1 = ts[self.signals[0]]
        
        # second component
        data2 = ts[self.signals[1]]
            
        df = pd.merge(data1, data2, left_index=True, right_index=True)

        if len(self.outnames) > 0 :
            new_signal = self.outnames[0]
        
        else :
            new_signal = self.signals[0] + '_' + self.signals[1]

        out_dict[new_signal] = df
                
        return out_dict 

class data_function(base_pre_processor) :
    """
    Summary :
        Apply a function to the specified time series. It uses the python
        "eval()" function and the function to be passed have to be a consistent
        python command.
    """
    def __init__(self, signals, components, outnames, function : str) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            function - string specifying the function to apply to the time
                        series
        
        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)
        
        self.function = function
    
    def process(self, ts : dict ) -> dict :        
        """
        Summary :
            Process the data provided as input applying the specified function
            to the time series of interest.
        
        Arguments :
            ts - time series stored in a dictionary. 
        
        Returns :
            processed time series as a dictionary
        """

        # If not specified, process all signals        
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())

        # create the output dictionary
        out_dict = {}
        
        empty_components = False
        if len(self.components) == 0 :
            empty_components = True

        for ii, signal in enumerate(self.signals) :
            df = ts[signal].copy()
                        
            if empty_components :
                components = df.keys()
            else : 
                components = self.components
            
            for component in components :
                df[component] = eval(self.function, {'x' : df[component].values, 'np' : np})
                
            if len(self.outnames) > ii :
                out_dict[self.outnames[ii]] = df
            else :
                out_dict[signal] = df
                        
        return out_dict
    
        
    
class data_splitter(base_pre_processor) :
    """
    Summary :
        Split time series in a data frame with respect to a specified column.
    """
    def __init__(self, signals, components, outnames, by) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            by - column to be used to split the data
        
        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)
        
        self.by = by

    def process(self, ts : dict ) -> dict :
        """
        Summary :
            Process the data provided as input. Split the time series with respect
            to the attribute 'by'
        
        Arguments :
            ts - time series stored in a dictionary. The dictonary has as keys the
                 signals available and as values the related data frames
        
        Returns :
            processed time series as a dictionary
        """
        out_dict = {}
        
        # if not defined, all the signals in the time series should be processed
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())
            
        # loop on the different signals (set at creation)
        for signal in self.signals :
            
            # check if the signal is present in the dictionary
            if signal not in ts :
                # move to the next signal (if any)
                continue
            
            # if here work on the components
            data = ts[signal]
            
            # check if the attribute for splitting is available
            if self.by not in data :
                raise Exception("data_spitter.process() - missing attribute for splitting")
                
            # get unique values in the 'by' attribute
            unique_val, inv_ind = np.unique( data[self.by].values, return_inverse=True )
            
            for ii in range(len(unique_val)) :
                
                val = unique_val[ii]
                if len(self.outnames) > ii :
                    new_signal = self.outnames[ii]
                else :
                    new_signal = signal + '_' + str(val)
                
                df = data[inv_ind == ii].drop(columns = [self.by]).copy()
                                
                # if the components are specified, return only those in the list
                if len(self.components) > 0 :
                    df = df[self.components]
                
                out_dict[new_signal] = df
                
        return out_dict        
        
class interpolator(base_pre_processor) :
    """
    Summary :
        Use linear interpolation to interpolate time-series.
    """
    def __init__(self, signals, components, outnames, Ts, method = "linear") :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            Ts - the sampling interval after interpolation
        
        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)
        
        self.Ts = Ts
        self.method = method
        
    def process(self, ts : dict ) -> dict :        
        """
        Summary :
            Process the data provided as input. Creates linearly interpolated
            time series
        
        Arguments :
            ts - time series stored in a dictionary. 
        
        Returns :
            processed time series as a dictionary
        """
        
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())
            
        out_data = []
        start_date = None
        stop_date = None
        compo_names = []
        
        for signal in self.signals :
            
            if 'Date' in ts[signal] :
                dates = ts[signal]['Date'].normalize()
            else:
                dates = ts[signal].index.normalize()
            
            # If not specified, process all the components
            if len(self.components) == 0 :
                self.components = list(ts[signal].keys())
                
            for component in self.components :
                ots = pd.Series(index=dates, data = ts[signal][component].values)
                
                its = ots.resample('%dD' % self.Ts).mean().interpolate(
                    method=self.method, limit_area="inside").dropna()  # drop nans at beginning and end of time series
                
                out_data.append(its)
                compo_names.append( signal + '_' + component)
                
                if start_date is None :
                    start_date = its.index[0]
                else :
                    if start_date < its.index[0] :
                        start_date = its.index[0]
                    
                if stop_date is None :
                    stop_date = its.index[-1]
                else :
                    if stop_date > its.index[-1] :
                        stop_date = its.index[-1]
        
        # If only 1 signal is considered, keep the names
        if len(self.signals) == 1 :
            compo_names = self.components
        
        # Now generates the final data frame
        out_ts = pd.DataFrame({compo_names[-1] : its[(its.index >= start_date) & (its.index <= stop_date)]}, 
                               index = its.index[(its.index >= start_date) & (its.index <= stop_date)])
        
        for ii in range(len(compo_names) - 1) :
            out_ts[compo_names[ii]] = out_data[ii]
            
        if len(self.outnames) > 0 :
            out_key = self.outnames[0]
        else :
            out_key = "lininterp"
            
        return { out_key : out_ts}

class butterworth_smoother(base_pre_processor) :
    """
    Summary :
        Performs smoothing using a butterworth filter.
    """
    
    def __init__(self, signals, components, outnames, fcut) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            fcut - the cut-off frequency
        
        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)

        self.fcut = fcut
        
        # Filter the time series
        self.B, self.A = sig.butter(13, 2 * fcut)
        self.padlen = 3 * max((len(self.B), len(self.A)))
            
    def process(self, ts : dict ) -> dict :        
        """
        Summary :
            Process the data provided as input. Perform Butterworth smoothing.
        
        Arguments :
            ts - time series stored in a dictionary.
        
        Returns :
            processed time series as a dictionary
        """
        
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())

        # create the output dictionary
        out_dict = {}
        
        empty_components = False
        if len(self.components) == 0 :
            empty_components = True

        ii = 0
        for signal in self.signals :
            df = ts[signal].copy()
            
            if len(df) < self.padlen :
                continue
            
            if empty_components :
                components = df.keys()
            else : 
                components = self.components
            
            for component in components :
                df[component] = sig.filtfilt(self.B, self.A, df[component].values)
            
            if len(self.outnames) > ii :
                out_dict[self.outnames[ii]] = df
            else :
                out_dict[signal] = df
            
            ii += 1
            
        return out_dict
            
class norm_processor(base_pre_processor) :
    """
    Summary :
        Compute the norm of 'synchronous' time series.
    """ 
    def __init__(self, signals, components = [], outnames = [], normalize = False) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            outnames - names to associate to the output data frames
        
            normalize - tells if the norm should be normalized by the sqrt of the number
                        of components. This could be useful if each component is upper/lower
                        bounded
        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)
    
        self.normalize = normalize
    
    def process(self, ts : dict ) -> dict :        
        """
        Summary :
            Process the data provided as input. Compute the norm of the specified 
            components.
        
        Arguments :
            ts - time series stored in a dictionary.
        
        Returns :
            processed time series as a dictionary
        """
        
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())

        # create the output dictionary
        out_dict = {}
        
        empty_components = False
        if len(self.components) == 0 :
            empty_components = True
        
        ii = 0
        for signal in self.signals :
            
            df = ts[signal]
            
            norm = np.zeros(len(df))
            
            if empty_components :
                components = df.keys()
            else : 
                components = self.components
            
            for component in components :
                norm += df[component].values**2
                
            norm = norm**0.5
            
            if self.normalize == True :
                norm /= len(components)**0.5
                
            if 'Date' in df :
                odf = pd.DataFrame({'norm': norm}, index=df['Date'])
            else :
                # try with the index
                odf = pd.DataFrame({'norm': norm}, index=df.index)

            if len(self.outnames) > ii :
                out_dict[self.outnames[ii]] = odf
            else :
                out_dict[signal] = odf
            
            ii += 1
            
        return out_dict

class lut_strecthor(base_pre_processor) :
    """
    Summary:
        Apply lut-strecthing to a time series.
    """
    def __init__(self, signals, components, outnames, min_val, max_val) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            min_val - minimum value for the data strecthing
            max_val - maximum value for the data strecthing
        
        Returns:
            Nothing.
        """
        super().__init__(signals, components, outnames)

        self.min_val = min_val
        self.max_val = max_val
    
    def process(self, ts : dict ) -> dict :        
        """
        Summary :
            Process the data provided as input. Apply strecthing to specif time
            series.
        
        Arguments :
            ts - time series stored in a dictionary.
        
        Returns :
            processed time series as a dictionary
        """
        
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())

        # create the output dictionary
        out_dict = {}
        
        empty_components = False
        if len(self.components) == 0 :
            empty_components = True
        
        ii = 0
        for signal in self.signals :
            
            df = ts[signal]
            
            if empty_components :
                components = df.keys()
            else : 
                components = self.components
            
            # check if the length of the parameters is matching
            use_single_value = False
            
            if (len(self.min_val) == 1) and (len(self.max_val) == 1) :
                use_single_value = True
            else :
                if (len(self.min_val) != len(self.components)) and \
                   (len(self.max_val) != len(self.components)) : 
                       
                       raise Exception("lut_strecthor.process() - wrong parameter number")
            
            ots = {}
            for jj in range(len(components)) :
                component = components[jj]
                
                if use_single_value :
                    ots[component] = lut_strecthor.lut_strecthing(df[component].values ,\
                                                         self.min_val[0], self.max_val[0])
                else :
                    ots[component] = lut_strecthor.lut_strecthing(df[component].values ,\
                                                         self.min_val[jj], self.max_val[jj])
            if 'Date' in df :
                odf = pd.DataFrame(ots, index=df['Date'])
            else :
                # try with the index
                odf = pd.DataFrame(ots, index=df.index)

            if len(self.outnames) > ii :
                out_dict[self.outnames[ii]] = odf
            else :
                out_dict[signal] = odf
            
            ii += 1
            
        return out_dict
            
    @staticmethod
    def lut_strecthing(ts, min_val, max_val) :
        """
        Summary :
            Apply lut strecthing to the time series.
        
        Arguments :
            ts - time series.
            min_val - minimum value defining the stretching
            max_val - maximum value defining the stretching
        
        Returns :
            processed time series
        """
        m = 255.0 / (max_val - min_val)
        b = -m * min_val

        value = m * ts + b
        value[value > 255] = 255
        value[value < 0] = 0

        return value.astype(np.uint8)
        
class red_nir_swir_processor(base_pre_processor) :
    """
    Summmary :    
        Remove data points based on the corresponding values of the
        red, nir, swir components
    """
    
    # Static member
    # Classifier used for performing the data selection
    color_classifier = KNeighborsClassifier(n_neighbors=5, p=2, metric='minkowski')
    classifier_initialized = False

    # classes considered in this specific implementation    
    class_labels = ['cloudy', 'hazy', 'shady', 'maintained', 'vegetated (O)',
                        'vegetated (Y)', 'vegetated (D)', 'other']
    
    @staticmethod
    def class_labels_to_indeces(class_lab) :
        """
        Summary :
            Returns the indexes associated to a list of class
        """
        indexes = []
        for label in class_lab :
            if label in red_nir_swir_processor.class_labels :
                indexes.append(red_nir_swir_processor.class_labels.index(label) + 1)
            else :
                indexes.append(-1)
        
        return indexes
    

    def __init__(self, signals, components, outnames, \
                 excluded_cat : list = ["cloudy", "hazy", "shady"], \
                 training_file : str = "" , \
                 min_val : list = [1200, 800, 150], \
				 max_val : list = [5700, 4100, 2800]) :
        """
        Summary :
            Object constructor.
        
        Arguments:
            signals - list of signals identifying the data frame to be used as
                      input
            components - names of the attributes in the data frame to be used for
                         the processing
            outnames - name of the output time series
            training_file - name of the file with the training data
        
        Returns:
            Nothing.
        """
        
        # initialized the parent class
        super().__init__(signals, components, outnames)

        # eventually initialize the classifier
        if training_file == "" :
            training_file = "./nl2020_b08_b11_b04_classified_1000.csv"
        
        if not red_nir_swir_processor.classifier_initialized :
            # Load the labeled data 
            df_colors = pd.read_csv(training_file)

            X_train = df_colors[['red','green', 'blue']].values
            y_train = df_colors['class']
            
            # Train the classifier
            red_nir_swir_processor.color_classifier.fit(X_train, y_train)
            red_nir_swir_processor.classifier_initialized = True
            
        # Set the categories for exclusion
        self.exclude_ind = red_nir_swir_processor.class_labels_to_indeces(excluded_cat)

        self.min_val = min_val
        self.max_val = max_val

    def process(self, ts : dict ) -> dict :        
        """
        Summary :
            Process the data provided as input. Apply NDVI filtering based on
            specific classes for the (red, nir, swir) classifier
        
        Arguments :
            ts - time series stored in a dictionary.
        
        Returns :
            processed time series as a dictionary
        """
        if len(self.signals) == 0 :
            self.signals = list(ts.keys())
            
        # first get the input data
        # it is assumed that a single signal is provided
        df = ts[self.signals[0]]

        # check if the length of the parameters is matching
        use_single_value = False
            
        if (len(self.min_val) == 1) and (len(self.max_val) == 1) :
            use_single_value = True
        else :
                if (len(self.min_val) != len(self.components) - 1) and \
                   (len(self.max_val) != len(self.components) - 1) : 
                       
                       raise Exception("red_nir_swir_processor.process() - wrong parameter number")

        # the first 3 componets are NIR, SWIR and RED
        # perform strecting
        ots = {}
        for jj, component in enumerate(self.components) : 
                # Process only the first three components
                if jj > 2 :
                    break
                
                if use_single_value :
                    ots[component] = lut_strecthor.lut_strecthing(df[component].values ,\
                                                         self.min_val[0], self.max_val[0])
                else :
                    ots[component] = lut_strecthor.lut_strecthing(df[component].values ,\
                                                         self.min_val[jj], self.max_val[jj])
        
        # Perform actual filtering
        X = np.array([ots[self.components[0]], \
                      ots[self.components[1]], \
                      ots[self.components[2]]], dtype = np.uint8).transpose()
            
        # check the classified type
        y = red_nir_swir_processor.color_classifier.predict(X)
            
        ind = ~np.in1d(y,self.exclude_ind)
                
        # Now build the output dictionary
        out_dict = {}
        
        if 'Date' in ts[self.signals[0]] :
            out_dict[self.outnames[0]] = ts[self.signals[0]][['Date', *self.components[3:]]][ind].copy()
            out_dict[self.outnames[0]].set_index('Date',inplace=True)
        else :
            out_dict[self.outnames[0]] = ts[self.signals[0]][self.components[3:]][ind].copy()
                
        if len(self.outnames) > 1 :
            # Convert band components it into a dataframe
            if 'Date' in df :
                odf = pd.DataFrame(ots, index=df['Date'])
            else :
                # try with the index
                odf = pd.DataFrame(ots, index=df.index)
            
            out_dict[self.outnames[1]] = odf.iloc[ind]
        
        # In this way, also the classification results are required
        if len(self.outnames) > 2 :
            # create a new data frame
            if 'Date' in df :
                out_classes = pd.DataFrame({"classes" : y}, index=df['Date'])
            else :
                # try with the index
                out_classes = pd.DataFrame({"classes" : y}, index=df.index)

            out_dict[self.outnames[2]] = out_classes.iloc[ind]
            
        return out_dict
        
class composite_processor(base_pre_processor) :
    """
    Summmary :    
        Time-series processor that operates several other preprocessors in 
        series.
    """
    def __init__(self, outnames, pre_processor_list ) :
        """
        Summary :
            Object constructor.
        
        Arguments :
            signals - list of signals identifying the data frame to be used as
                      input 
            components - names of the attributes in the data frame to be used for
                         the processing
            pre_processors_list - list of pre-processors to be operated in series
        
        Returns:
            Nothing.
        """
        super().__init__(pre_processor_list[0].signals, pre_processor_list[0].components, outnames)
        
        self.pre_processors = pre_processor_list
        self.pre_processors[-1].outnames = outnames
               
    def process(self, ts : dict ) -> dict :        
        """
        Summary :
            Process the data provided as input. Compute the norm of the specified 
            components.
        
        Arguments :
            ts - time series stored in a dictionary.
        
        Returns :
            processed time series as a dictionary
        """
        # first check if the signal to process is present
        data_available = True
        for signal in self.signals :
            data_available &= signal in ts            
        
        if not data_available :
            return {}
        
        current_ts = ts
        
        for processor in self.pre_processors :
            current_ts = processor.process(current_ts)
            
            # Force garbage collection
            gc.collect()
            
        return current_ts

class processor_factory :
    """
    Summary :
        Object responsible for the creation of time series pre-processors
    """
    
    def get_pre_processors(self, options) :
        """
        Summary:
           Create a lits of pre-processors for the time series processing.
           Each pre-processor works in parallel.
           
        Arguments:
            options - dictionary with the options for the creation of the different
                      pre-processors
        Returns:
            A list of pre-processors.
        """
        
        # first check if the related options are available
        if "pre-processors" not in options :
            raise Exception("processor_factory.get_pre_processors() - missing options")
            
        pre_pro_list = []
        
        for pp_opt in options["pre-processors"] :
                            
            # get the output names
            outnames = []
            if "outnames" in pp_opt :
                outnames = pp_opt['outnames']
            
            # get the processors
            processors = pp_opt['processors']
            
            if len(processors) == 1 :
                pp = self.get_processor(processors[0], outnames)
            else :
                loc_list = []
                for pro_opt in processors :
                    loc_list.append(self.get_processor(pro_opt))
                
                # create a composite processor
                pp = composite_processor(outnames, loc_list)
                
            pre_pro_list.append(pp)
        
        return pre_pro_list
            
    def get_processor(self, pro_opt, out_names = []) :
        """
        Create a single pre-processor
           
        Arguments:
            options - dictionary with the options for the creation of the specific
                      pre-processor  
        Returns:
            A list of pre-processors.
        """
        
        # creation depending on the type
        pp_type = pro_opt["type"]
        
        signals = []
        if "signals" in pro_opt :
            signals = pro_opt["signals"]
        
        components = []
        if "components" in pro_opt :
            components = pro_opt["components"]
            
        outnames = []
        if len(out_names) > 0 :
            outnames = out_names
            
        if "outnames" in pro_opt :
            outnames = pro_opt["outnames"]
                
        if pp_type == "split" :
            sort_by = pro_opt["by"]
            processor = data_splitter(signals, components, outnames, sort_by)            
        
        elif pp_type == "merge" :
            processor = data_merger(signals, components, outnames)
            
        elif pp_type == "interp" :
            Ts = 1
            if "Ts" in pro_opt :
                Ts = pro_opt["Ts"]
            
            method = "linear"
            if "method" in pro_opt :
                method = pro_opt["method"]
                      
            processor = interpolator(signals, components,  outnames, Ts, method)
                
        elif pp_type == "butter_smoother" :
            fc = 0.05
            if "fc" in pro_opt :
                fc = pro_opt["fc"]
            
            processor = butterworth_smoother(signals, components, outnames, fc)
        
        elif pp_type == "norm" :
            normalize = False
            if "normalize" in pro_opt :
                normalize = pro_opt["normalize"]
            processor = norm_processor(signals, components, outnames, normalize)
        
        elif pp_type == "all_pass" :
            processor = all_pass(signals, components, outnames)
           
        elif pp_type == "lut_strect" :
            min_val = pro_opt["min_val"]
            max_val = pro_opt["max_val"]

            processor = lut_strecthor(signals, components, outnames, min_val, max_val)            
        
        elif pp_type == "filter" :
            sort_by = pro_opt["by"]
            criterion = pro_opt["criterion"]
            threshold = pro_opt["threshold"]
            
            processor = data_filter(signals, components, outnames, sort_by, \
                                    criterion, threshold)
        elif pp_type == "band_filter" :
            if "min_val" in pro_opt :
                min_val = pro_opt["min_val"]
            else :
                min_val = [1200, 800, 150]				
                
            if "max_val" in pro_opt :
                max_val = pro_opt["max_val"]
            else :
                max_val = [5700, 4100, 2800]	
                
            if "excluded_categories" in pro_opt : 
                ex_cat = pro_opt["excluded_categories"]
            else :
                ex_cat = ["cloudy", "hazy", "shady"]
		
            if "training_file" in pro_opt :
                training_file = pro_opt["training_file"]
            else :
                training_file = ""
                
            processor = red_nir_swir_processor(signals, components, outnames, \
                                               ex_cat, training_file, min_val, \
                                               max_val)
        elif pp_type == "index_adder" :
            if "function" in pro_opt : 
                function = pro_opt["function"]
            else :
                function = "diff_div_by_sum"
                
            if "as" in pro_opt :
                name = pro_opt["as"]
            else :
                name = "ndvi"
                
            processor = index_adder(signals, components, outnames, \
                                    name, function)
        
        elif pp_type == "math_function" :
            if "function" not in pro_opt :
                raise Exception("processor_factory.get_processors() - a function of single variable x must be specified")
                
            processor = data_function(signals, components, outnames, pro_opt["function"])

        else :
            raise Exception("processor_factory.get_processor() - Unsupported processor")
            
        return processor
