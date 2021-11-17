#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

from scipy import signal
import numpy as np
import pandas as pd
import markers_processing as mp


##############################################################################

def get_maxima( series, N, start_date = None, stop_date = None, _sorted = True ) :
    """
    Summary:
        Function that determines the first N maxima of a pandas time series
        
    Arguments:
        series - pandas series
        N - number of maxima
        start_date - start date as DateTime - used to limit the search for the maxima 
        stop_date - stop date as DateTime - used to limit the search for the maxima
        _sorted - tell to sort with respect to the highest values
        
    Returns:
        maxima - the maxima of the time series

    """
    
    if start_date == None :
        start_date = series.index[0]
        
    if stop_date == None :
        stop_date = series.index[-1]

    ind_in_date_range = np.argwhere( (series.index >= start_date) & (series.index <= stop_date) ).flatten()
        
    # First find the local maxima
    all_maxima = signal.argrelmax(series.values[ind_in_date_range])[0]
    # all_maxima = argrelmax(series.values[ind_in_date_range])
    
    if _sorted :
        # Then sort the minima
        ind = np.argsort( series.values[ind_in_date_range[all_maxima]] )
        nmaxima = min([N, len(ind)])
        ind = all_maxima[ind[-nmaxima:]]
        maxima = series.iloc[ ind_in_date_range[np.sort(ind)] ].copy()
    else :
        nmaxima = min([N, len(all_maxima)])
        maxima = series.iloc[ind_in_date_range[all_maxima[:nmaxima]]]
        
    return maxima

def get_minima( series, N, start_date = None, stop_date = None, _sorted = True ) :
    """
    Summary:
        Function that determines the first N minima of a pandas time series
        
    Arguments:
        series - pandas series
        N - number of minima
        start_date - start date as DateTime - used to limit the search for the maxima 
        stop_date - stop date as DateTime - used to limit the search for the maxima
        _sorted - tell to sort with respect to the highest values
        
    Returns:
        minima - the minima of the time series
    """
    
    if start_date == None :
        start_date = series.index[0]
        
    if stop_date == None :
        stop_date = series.index[-1]

    ind_in_date_range = np.argwhere( (series.index >= start_date) & (series.index <= stop_date) ).flatten()
    
    # First find the local minima
    all_minima = signal.argrelmin(series.values[ind_in_date_range])[0]


    if _sorted :
        # Then sort the minima
        ind = np.argsort( series.values[ind_in_date_range[all_minima]] )
        nminima = min([N, len(ind)])
        ind = all_minima[ind[:nminima]]
        minima = series.iloc[ ind_in_date_range[np.sort(ind)] ].copy()
    else :
        nminima = min([N, len(all_minima)])
        minima = series.iloc[ind_in_date_range[all_minima[:nminima]]]
    
    return minima

def argrelmax( timeseries ) :
    """
    Summary:
        Function that determines the relative maxima of a time series
        It performs the same job performed by scipy.signal.argrelmin
        Implemented here mainly to understand the mechanism.
        
    Arguments:
        timeseries - numpy array
        
    Returns:
        maxima - the maxima of the time series
    """
    
    # First compute the first derivative
    dseries = np.diff( timeseries )
    
    # Compute the second derivative
    ddseries = np.diff( dseries )
    
    # Look for a sign change in the first derivative
    dsignchange = np.sign(dseries[:-1] * dseries[1:])
    
    # Extrema occur in occurence of a sign change of the first derivative
    # Maxima have negative second derivative
    maxima = np.argwhere( (dsignchange <= 0) & ( ddseries < 0) ).flatten()
    
    return maxima + 1

def get_first_maxima_before( series, N, stop_date ) :
    """
    Summary:
        Function that determines the first N maxima of a pandas time series
        before a specific date. In here the 'first N' are determined by the 
        closeness in date
        
    Arguments:
        series - pandas series
        N - number of maxima
        stop_date - end date as DateTime
        
    Returns:
        maxima - the maxima of the time series

    """    
    ind_in_date_range = np.argwhere( series.index < stop_date ).flatten()
        
    # First find the local maxima
    all_maxima = signal.argrelmax(series.values[ind_in_date_range])[0]
        
    # Then sort the maxima with respect to closeness to the end date
    ind = np.argsort( stop_date - series.index[ind_in_date_range[all_maxima]] )
    # Keep only the first N maxima
    nmaxima = N
    if nmaxima > len( ind ) :
        nmaxima = len( ind )
        
    ind = all_maxima[ind[:nmaxima]]
    
    if len( ind ) == 0 :
        # if no maximum was found, use the left extremum
        maxima = series.iloc[ ind_in_date_range[0:1] ].copy()
    else :
        maxima = series.iloc[ ind_in_date_range[ind] ].copy()
    
    return maxima
    
def get_first_maxima_after( series, N, start_date ) :
    """
    Summary:
        Function that determines the first N maxima of a pandas time series
        after a specific date. In here the 'first N' are determined by the 
        closeness in date
        
    Arguments:
        series - pandas series
        N - number of maxima
        start_date - start date as DateTime
        
    Returns:
        maxima - the maxima of the time series

    """    
    ind_in_date_range = np.argwhere( series.index > start_date ).flatten()
        
    # First find the local maxima
    all_maxima = signal.argrelmax(series.values[ind_in_date_range])[0]
        
    # Then sort the maxima with respect to closeness to the start date
    ind = np.argsort( series.index[ind_in_date_range[all_maxima]] - start_date )
    
    # Keep only the first N maxima
    nmaxima = N
    if nmaxima > len( ind ) :
        nmaxima = len( ind )
        
    ind = all_maxima[ind[:nmaxima]]
    if len( ind ) == 0 :
        # if no maximum was found, use the right extremum
        maxima = series.iloc[ ind_in_date_range[-1:] ].copy()
    else :
        maxima = series.iloc[ ind_in_date_range[ind] ].copy()
    
    return maxima

def get_first_minima_before( series, N, stop_date ) :
    """
    Summary:
        Function that determines the first N minima of a pandas time series
        before a specific date. In here the 'first N' are determined by the 
        closeness in date
        
    Arguments:
        series - pandas series
        N - number of minima
        stop_date - end date as DateTime
        
    Returns:
        minima - the minima of the time series

    """    
    ind_in_date_range = np.argwhere( series.index < stop_date ).flatten()
        
    # First find the local minima
    all_minima = signal.argrelmin(series.values[ind_in_date_range])[0]
        
    # Then sort the minima with respect to closeness to the end date
    ind = np.argsort( stop_date - series.index[ind_in_date_range[all_minima]] )
    
    # Keep only the first N minima
    nminima = N
    if nminima > len( ind ) :
        nminima = len( ind )
        
    ind = all_minima[ind[:nminima]]
    
    if len( ind ) == 0 :
        # if no minimum was found, use the left extremum
        minima = series.iloc[ ind_in_date_range[0:1] ].copy()
    else :
        minima = series.iloc[ ind_in_date_range[ind] ].copy()
    
    return minima

def get_first_minima_after( series, N, start_date ) :
    """
    Summary:
        Function that determines the first N minima of a pandas time series
        after a specific date. In here the 'first N' are determined by the 
        closeness in date
        
    Arguments:
        series - pandas series
        N - number of minima
        start_date - start date as DateTime
        
    Returns:
        minima - the minima of the time series

    """    
    ind_in_date_range = np.argwhere( series.index > start_date ).flatten()
        
    # First find the local minima
    all_minima = signal.argrelmin(series.values[ind_in_date_range])[0]
        
    # Then sort the minima with respect to closeness to the start date
    ind = np.argsort( series.index[ind_in_date_range[all_minima]] - start_date )
    
    # Keep only the first N minima
    nminima = N
    if nminima > len( ind ) :
        nminima = len( ind )
        
    ind = all_minima[ind[:nminima]]
    
    if len( ind ) == 0 :
        # if no minimum was found, use the right extremum
        minima = series.iloc[ ind_in_date_range[-1:] ].copy()
    else :
        minima = series.iloc[ ind_in_date_range[ind] ].copy()
    
    return minima

def get_extrema_features( series, N, start_date = None, stop_date = None, _sorted = True  ) :

    """
    Summary:
        Function that determines the first N minima as candidates for mowing
        detection. For each minima, the left/right maxima are found and used
        to evaluate the 'recovery' time associated to the minimum and the 
        depth of the minima. These pieces of information form the feature
        vector associated to the time series
        
    Arguments:
        series - pandas series
        N - number of maxima
        start_date - start date as DateTime - used to limit the search for the maxima 
        stop_date - stop date as DateTime - used to limit the search for the maxima
        _sorted - tell to sort with respect to the highest values
    
    Returns:
        extrema - feature vector provided as pandas series. 
                  The vector should have 3N elements and be of the form:
                      
                maxima 1l - minima 1 - maxima 1r -
                maxima 2l - minima 2 - maxima 2r -
                ...
                maxima Nl - minima N - maxima Nr
                
                If less than N minima are found, the vector will habe 3n elements
                where n is the number of minima found
    """
    
    if start_date == None :
        start_date = series.index[0]
        
    if stop_date == None :
        stop_date = series.index[-1]
        
    # First get the first N minima
    minima = get_minima( series, N, start_date, stop_date, _sorted )
    
    extrema = []
    
    # For each minima find the left and right maxima
    for ii in range( len( minima ) ):
        
        lmaxima = get_first_maxima_before( series, 1, minima.index[ii] )
        rmaxima = get_first_maxima_after( series, 1, minima.index[ii] )
        
        if ii == 0 :
            extrema = pd.concat([lmaxima, minima.iloc[ii:(ii+1)], rmaxima])
        else :                
            extrema = pd.concat([extrema, lmaxima, minima.iloc[ii:(ii+1)], rmaxima])

    return extrema            

def find_closest_date( ts, date, search_min = True) :
    """
    Summary:
        Function that search for the closest date in a time series using
        a specific criteria (min/max)
        
    Arguments:
        ts - the time series where to search for the event
        date - the event date
        search_min - if true it searches for minumum value, if false for the
                    maximum
        
    Returns:
        close_date - the date in the time series satisfying the criteria
    """
    
    # find the previous and following date
    previous_date_ind = len((date - ts.index).days[(date - ts.index).days >= 0]) - 1
    
    if ts.index[previous_date_ind] == date :
        return date
    
    next_date_ind = previous_date_ind + 1
    
    if search_min :
        if ts[previous_date_ind] > ts[next_date_ind] :
            return ts.index[next_date_ind]
        else:
            return ts.index[previous_date_ind]
    else :
        if ts[previous_date_ind] < ts[next_date_ind] :
            return ts.index[next_date_ind]
        else:
            return ts.index[previous_date_ind]
        



def aggregate_extrema(features, Th, percentage = True) :
    """
    Summary:
        Function that tries to remove false minima aggregating closeby extrema
        
    Arguments:
        features - pandas series containing the extrema to be aggregated. 
                The series is of the form: Max, Min, Max, Max, Min, ...
        Th - threshold used to remove 'false' minima
        percentage - tells if the thrshold is expressed as percentage of the distance
                     between adjacent maxima and minima
        
    Returns:
        aggregatedFeat - pandas vector with aggregated features

    """   
    # Keep the first maximum and minimum
    ind = [0]

    # Factor used to scale the threshold depending on 'percentage'    
    d = 1
    skipNext = False
    
    # For each minima check if it can be merged with the right node
    for ii in range(1, len(features), 3) :
        if skipNext :
            skipNext = False
            continue
        
        # check if are at the end of the feature vector
        if ii + 2 >= len( features ) :
            # Record the point which is the last in the list
            ind.append(ii)      # Current minima
            ind.append(ii + 1)  # Following maxima
            break
        
        aggregate = False

        # check if the next two maxima coincide
        if features[ii+1] == features[ii+2] :
            
            # find what is lowest minimum 
            if features[ ii ] > features[ii + 3] :
                # try to aggregate on the left
                if percentage :
                    d = features[ii - 1] - features[ii + 3]  
                
                if  (features[ii-1] > features[ii+1]) and (features[ii+1] - features[ii] < Th * d):
                    aggregate = True
                # in this case, the point and the next 2 coincident maxima
                # should not be included in the output list
            else :
                # try to aggregate on the right
                if percentage :
                    d = features[ii + 4] - features[ii]  
                
                if (features[ii+4] > features[ii+2]) and (features[ii+2] - features[ii+3] < Th * d):
                    aggregate = True
                    # in this case, the point should be included but the next should not
                    ind.append(ii)      # Current minima
                    ind.append(ii+4)
                    if ii + 5 < len(features) :
                        ind.append(ii+5)
                    skipNext = True     # skip the next minima that has already been processed
                    
        if not aggregate:
            # Record the point
            ind.append(ii)      # Current minima
            ind.append(ii + 1)  # Following maxima
            ind.append(ii + 2)  # Maxima of the next minima
    
    # check if the last max was copied twice
    if features[ind[-1]] == features[ind[-2]]:
        ind.pop()
    
    return features[ind].copy()

def aggregate_extrema_angle(features, angle = 135) :
    """
    Summary:
        Function that tries to remove false minima aggregating closeby extrema.
        The aggregation is based on the angel between the upper sides of
        adjacent triangles
        
    Arguments:
        features - pandas series containing the extrema to be aggregated. 
                The series is of the form: Max, Min, Max, Max, Min, ...
        
        angle - minimum angle to have distinct events
        
    Returns:
        aggregatedFeat - pandas vector with aggregated features

    """
    
    # To perfom aggregation there should be at least two events, i.e. 6 points
    if len(features) < 6 :
        return features.copy()
    
    # indexes of the aggregated features
    indexes = []
    
    # variable accounting for the last aggregated feature 
    last_aggregated = 3
    min_ind = 2
    
    # Now start from the second event and compare it with the previous
    for ii in range(3, len(features), 3) :
        
        # Aggregate only if the two events have a common point
        if features.index[ ii ] > features.index[ ii - 1] :
            indexes.append( ii - last_aggregated )
            indexes.append( ii - min_ind )
            indexes.append( ii - 1 )
            
            # since there is not aggregation, reset the index variables
            last_aggregated = 3
            min_ind = 2
        elif features.index[ ii ] < features.index[ ii - 1] :
            # this should be a very rare event and occurs only if the
            # signal.argrelmin/max had some problems
            last_aggregated += 3
                
            if features[ ii - min_ind ] < features[ ii + 1] :
                    min_ind +=3
        else :            
            # if here, aggregation can be attempted
            # left angle
            if features[ii - 3] < features[ii - 1] :
                a1 = 90 + np.rad2deg( np.arcsin( (features[ii - 1] - features[ii - 3]) /
                                                 (features[ii - 1] - features[ii - 2]) ) )
            else :
                a1 = np.rad2deg( np.arccos( (features[ii - 3] - features[ii - 1]) /
                                            (features[ii - 3] - features[ii - 2]) ) )
                
            # right angle
            if features[ii] < features[ii + 2] :
                a2 = np.rad2deg( np.arccos( (features[ii + 2] - features[ii]) /
                                           (features[ii + 2] - features[ii + 1]) ) )
            else :
                a2 = 90 + np.rad2deg( np.arcsin( (features[ii] - features[ii + 2]) /
                                                 (features[ii] - features[ii + 1]) ) )                
            angle_v = a1 + a2
            
            if angle_v < 0 : 
                angle_v += 360
                
            if angle_v < angle :
                # aggregate
                last_aggregated += 3
                
                if features[ ii - min_ind ] < features[ ii + 1] :
                    min_ind +=3
                
            else :
                # move to the next event
                indexes.append( ii - last_aggregated )
                indexes.append( ii - min_ind )
                indexes.append( ii - 1 )
                
                # since there is not aggregation, reset the index variables
                last_aggregated = 3
                min_ind = 2
    
    # Now insert the last event
    indexes.append( len(features) - last_aggregated )
    indexes.append( len(features) - min_ind )
    indexes.append( len(features) - 1 )
                           
    return features[indexes].copy()


    
def filter_events_based_on_angle(events, min_angle = 30) :
    """
    Summary:
        Function that filters events based on their geometric properties.
        In this case, the angle in correspondence of a side point is considered.
        An event of the type max-min-max is assumed.
        
    Arguments:
        events - pandas time series identifying the events to be filtered
                 
        min_angle - minimal angle to achieve in order to exclude the event
        
    Returns:
        List of filtered events
    """
    
    # list of indexes of the elements to keep
    ind = []
    
    for ii in range(0, len(events), 3) :
        # Compute the two side angles
        hside = (events.index[ii + 2] - events.index[ii]).days
        vside = max([events[ii], events[ii + 2]]) - events[ii + 1]
        
        # left angle
        v1 = np.array( [ (events.index[ii + 1] - events.index[ii]).days / hside, 
                         (events[ii + 1] - events[ii]) / vside ] )
        v2 = np.array( [ 1, (events[ii + 2] - events[ii]) / vside ] )
        
        langle = np.arccos( np.dot( v1, v2 ) / np.sqrt( np.dot(v1, v1) * np.dot(v2, v2) ) )
        langle = np.rad2deg(langle)
        
        # right angle 
        v1 = np.array( [ -1, (events[ii] - events[ii+2]) / vside ] )
        v2 = np.array( [ (events.index[ii + 1] - events.index[ii + 2]).days / hside, 
                         (events[ii + 1] - events[ii + 2]) / vside ] )
        
        rangle = np.arccos( np.dot( v1, v2 ) / np.sqrt( np.dot(v1, v1) * np.dot(v2, v2) ) )
        rangle = np.rad2deg(rangle)
                
        # If both angles are greater than min_angle, keep the event
        if min([langle, rangle]) >= min_angle :
            ind.append(ii)
            ind.append(ii+1)
            ind.append(ii+2)
        
    if len(ind) > 0 : 
        return events[ind].copy()
    else :
        return None

def filter_by_duration(events, min_duration) :
    """
    Summary:
        Function that filters events based on their duration in days.
        
    Arguments:
        events - pandas time series identifying the events to be filtered
                 
        min_duration - minimum duration of the events
        
    Returns:
        List of filtered events
    """
    
    # list of indexes of the elements to keep
    ind = []
    
    for ii in range(0, len(events), 3) :
        # duration of the event
        duration = (events.index[ii + 2] - events.index[ii]).days
        
        if duration >= min_duration :
            ind.append(ii)
            ind.append(ii+1)
            ind.append(ii+2)
    
    if len(ind) > 0 : 
        return events[ind].copy()
    else :
        return None
    
def filter_by_drop(events, min_drop) :
    """
    Summary:
        Function that filters events based on their drop.
        
    Arguments:
        events - pandas time series identifying the events to be filtered
                 
        min_duration - minimum duration of the events
        
    Returns:
        List of filtered events
    """
    
    # list of indexes of the elements to keep
    ind = []
    
    for ii in range(0, len(events), 3) :
        # drop of the event
        drop = max([events.values[ii], events.values[ii+2]]) - events.values[ii+1]
        
        if drop >= min_drop :
            ind.append(ii)
            ind.append(ii+1)
            ind.append(ii+2)
    
    if len(ind) > 0 : 
        return events[ind].copy()
    else :
        return None
    
def features_to_markers(features, marker_type) :
    """
    Summary :
        Converts a sequence of features to a list of markers
        
    Arguments:
        features - feature vector provided as pandas series. 
                 The vector should have 3N elements and be of the form:
                  
                maxima 1l - minima 1 - maxima 1r -
                maxima 2l - minima 2 - maxima 2r -
                ...
                maxima Nl - minima N - maxima Nr
    Returns:
        list of markers
        
    """
    if features is None :
        return None
    
    out_list = []
    
    for ii in range(0, len(features), 3) :
        
        marker = mp.base_marker(features.index[ii], features.index[ii+2], \
                                features.index[ii+1], marker_type)
            
        marker.values = features.values[ii:ii+3]
        
        out_list.append(marker)
    
    return out_list
