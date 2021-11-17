#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Sun Sep 26 15:34:44 2021


import numpy as np

"""
    Summary: 
        Class for aggregating dictionaries of markers in a single 
        list of consecutive composite markers
"""

class marker_aggregator :
    """
    Summary: 
        Class responsible for aggregating markers
    """
    def __init__(self, options : dict ) :
        """
        Summary: 
            Object constructor.
        
        Arguments:
            options - dictionary with the options specifying the operations
                      to be performed. 
        
        Returns:
            Nothing.
        """
        if "marker-aggregator" not in options :
            raise Exception("marker-aggregator.__init__() - missing options")
        else :
            self.action_list = options["marker-aggregator"]
            
        return
    
    def aggregate_markers(self, markers : dict) -> list :
        """
        Summary: 
            Function responsible for aggregating markers.
        
        Arguments:
            markers - dictionary of the markers to be aggregated 
        
        Returns:
            mark_list - list of aggregated markers
        """
        marker_dict = markers
        marker_list = []
        
        # There is nothing to aggregate
        if len(markers) == 0 :
            return []
            
        # check if there are actions to perform
        if not any(["action" in item for item in self.action_list]) :
            # there is nothing do 
            # just use the fist list in the marker dictionary
            marker_list = list(markers.values())[0]
            return marker_list
        
        for action in self.action_list :
            if action["action"] == "confirm":                
                marker_dict, marker_list = self.confirm(marker_dict, marker_list, action)
        
            elif action["action"] == "aggregate":                
                marker_dict, marker_list = self.aggregate(marker_dict, marker_list, action)
            
            elif action["action"] == "merge":
                marker_dict, marker_list = self.merge(marker_dict, marker_list, action)
                
            else :
                raise Exception("marker-aggregator.aggregate_markers() - unknown action")
                
        return marker_list
    
    def aggregate(self, marker_dict : dict, marker_list : list, action : dict) :
        """
        Summary: 
            Markers from two time series are aggregated eventually forming aggregated
            markers.
        
        Arguments:
            marker_dict - dictionary of the markers to be aggregated 
            marker_list - list of previously processed markers
            
        Returns:
            marker_dict - dictionary of the markers to be aggregated 
            marker_list - list of previously processed markers 
            action - dictionary specifing the action to be performed
        """
        if len(action["signals"]) == 1 :
            marker_list1 = marker_list
            
            if action["signals"][0] in marker_dict :
                marker_list2 = marker_dict[action["signals"][0]]
            else :
                marker_list2 = []
                
        elif len(action["signals"]) == 2 :
            marker_list1 = marker_dict[action["signals"][0]]
            
            if action["signals"][0] in marker_dict :
                marker_list1 = marker_dict[action["signals"][0]]
            else :
                marker_list1 = []
            
            if action["signals"][1] in marker_dict :
                marker_list2 = marker_dict[action["signals"][1]]
            else :
                marker_list2 = []
        else :
            raise Exception("marker-aggregator.aggregate() - signals not specified")
        
        if len(marker_list2) == 0:
            if "outname" in action :
                marker_dict[action["outname"]] = marker_list1
                return marker_dict, marker_list
            else :
                return marker_dict, marker_list1
        
        if len(marker_list1) == 0:
            if "outname" in action :
                marker_dict[action["outname"]] = marker_list2
                return marker_dict, marker_list
            else :
                return marker_dict, marker_list2 
        
        # overlapping
        if "overlap" in action :
            overlap_th = action["overlap"]
        else :
            overlap_th = 0

        m1_ov_markers = []
        m2_ov_markers = []
        m1_markers = []
        m2_markers = []
        ov = []

        for m1 in marker_list1 :
            overlapping = [m1.overlap_in_days(x) for x in marker_list2]
            max_overlap = max(overlapping)
                        
            if max_overlap > overlap_th :
                m2 = marker_list2[np.argmax(overlapping)]
                m1_ov_markers.append(m1)
                m2_ov_markers.append(m2)
                ov.append(max_overlap)
       
        jj = 1 
        while jj  < len(m2_ov_markers) :
            m2 = m2_ov_markers[jj]
            m2_old = m2_ov_markers[jj - 1]
                
            if m2 == m2_old :
                if ov[jj] > ov[jj - 1] :
                    m2_ov_markers.pop(jj - 1)
                    m1_ov_markers.pop(jj - 1)
                    ov.pop(jj - 1)
                else :
                    m2_ov_markers.pop(jj)
                    m1_ov_markers.pop(jj)
                    ov.pop(jj)
            else :
                jj += 1
        
        # Now aggregate the markers
        overlapping_markers = []
        for ii, m1 in enumerate(m1_ov_markers) :
            overlapping_markers.append(m1.merge_markers(m2_ov_markers[ii]))                        
                
        for m1 in marker_list1 :
            if m1 not in m1_ov_markers :
                m1_markers.append(m1)
                
        for m2 in marker_list2 :
            if m2 not in m2_ov_markers :
                m2_markers.append(m2)

        output_list = marker_aggregator.merge_event_list(overlapping_markers, m1_markers)
        output_list = marker_aggregator.merge_event_list(output_list, m2_markers)

        # Now generate the output
        if "outname" in action :
            marker_dict[action["outname"]] = output_list
            return marker_dict, marker_list
        else :
            return marker_dict, output_list        

        
    def confirm(self, marker_dict : dict, marker_list, action  : dict) :
        """
        Summary: 
            Markers in a time series are confirmed by the markers in 
            another time series
        
        Arguments:
            marker_dict - dictionary of the markers to be aggregated 
            marker_list - list of previously processed markers
            
        Returns:
            marker_dict - dictionary of the markers to be aggregated 
            marker_list - list of previously processed markers
            action - dictiory with the parameters for merging the markers
        """
        if len(action["signals"]) == 1 :
            marker_list1 = marker_list
            
            if action["signals"][0] in marker_dict :
                marker_list2 = marker_dict[action["signals"][0]]
            else :
                marker_list2 = []
            
        elif len(action["signals"]) == 2 :
            if action["signals"][0] in marker_dict :
                marker_list1 = marker_dict[action["signals"][0]]
            else :
                marker_list1 = []
            
            if action["signals"][1] in marker_dict :
                marker_list2 = marker_dict[action["signals"][1]]
            else :
                marker_list2 = []
        else :
            raise Exception("marker-aggregator.confirm() - signals not specified")
 
        if len(marker_list2) == 0 :
            # No possibility to confirm
            if "outname" in action :
                marker_dict[action["outname"]] = []
                return marker_dict, marker_list
            else :
                return marker_dict, []
 
        # convert into a numpy array for convenience    
        marker_array = np.array(marker_list2)
        
        # overlapping
        if "overlap" in action :
            overlap_th = action["overlap"]
        else :
            overlap_th = 0
               
        confirmed_list = []
        
        # now confirm the first marker series with the second
        for marker in marker_list1 :
            
            # find the overlapping between the markers of the two list            
            f = lambda x: marker.overlap_in_days(x)
            vf = np.vectorize(f)
            
            overlap = max(vf(marker_array))
            
            if overlap > overlap_th :
                confirmed_list.append(marker)
        
        if "outname" in action :
            marker_dict[action["outname"]] = confirmed_list
            return marker_dict, marker_list
        else :
            return marker_dict, confirmed_list
        
    def merge(self, marker_dict : dict, marker_list, action  : dict) :
        """
        Summary: 
            Markers from two time series are merged: no co-existence is
            foreseen.
        
        Arguments:
            marker_dict - dictionary of the markers to be aggregated 
            marker_list - list of previously processed markers
            
        Returns:
            marker_dict - dictionary of the markers to be aggregated 
            marker_list - list of previously processed markers 
            action - dictionary specifing the action to be performed
        """
        if len(action["signals"]) == 1 :
            marker_list1 = marker_list
            
            if action["signals"][0] in marker_dict :
                marker_list2 = marker_dict[action["signals"][0]]
            else :
                marker_list2 = []
        elif len(action["signals"]) == 2 :
            if action["signals"][0] in marker_dict :
                marker_list1 = marker_dict[action["signals"][0]]
            else :
                marker_list1 = []
                
            if action["signals"][1] in marker_dict :
                marker_list2 = marker_dict[action["signals"][1]]
            else :
                marker_list2 = []
        else :
            raise Exception("marker-aggregator.merge() - signals not specified")
    
        if len(marker_list2) == 0:
            if "outname" in action :
                marker_dict[action["outname"]] = marker_list1
                return marker_dict, marker_list
            else :
                return marker_dict, marker_list1
        
        if len(marker_list1) == 0:
            if "outname" in action :
                marker_dict[action["outname"]] = marker_list2
                return marker_dict, marker_list
            else :
                return marker_dict, marker_list2 
        
        # The second time series has precedence on the first
        output_list = []
        
        ii = 0
        jj = 0
        
        m1 = marker_list1[ii]
        m2 = marker_list2[jj]
            
        while ii < len(marker_list1) and jj < len(marker_list2) :
            
            if m1 < m2 :
                output_list.append(m1)
                ii += 1
                if ii < len(marker_list1) :
                    m1 = marker_list1[ii]

            elif m2 < m1 :
                output_list.append(m2)
                jj += 1
                if jj < len(marker_list2) :
                    m2 = marker_list2[jj]

            else :
                # the two markers overlap
                if m1.start_date < m2.start_date :
                   m_new = m1.trim_right(m2.start_date)
                   output_list.append(m_new)
                    
                   output_list.append(m2)
                   jj += 1
                
                   if m2.stop_date < m1.stop_date :
                       # m2 is totally contained in m1 - split in 3 events   
                       m1 = m1.trim_left(m2.stop_date)
                   else :
                       ii += 1
                       if ii < len(marker_list1) :
                           m1 = marker_list1[ii]
                           
                   if jj < len(marker_list2) :
                       m2 = marker_list2[jj]        
                else :
                   if m2.stop_date < m1.stop_date :
                       m1 = m1.trim_left(m2.stop_date)
                       output_list.append(m2)
                       jj += 1
                       if jj < len(marker_list2) :
                           m2 = marker_list2[jj]                    
                   else :
                       # m1 is completely in m2 - This should not happen
                       ii += 1
                       if ii < len(marker_list1) :
                           m1 = marker_list1[ii]    
                        
        # Now check if there are remaining markers in the two lists
        while ii < len(marker_list1) :
            output_list.append(m1)
            ii += 1
            if ii < len(marker_list1) :
                m1 = marker_list1[ii]
        
        while jj < len(marker_list2) :
            output_list.append(marker_list2[jj])
            jj += 1
        
        # Now generate the output
        if "outname" in action :
            marker_dict[action["outname"]] = output_list
            return marker_dict, marker_list
        else :
            return marker_dict, output_list
        
    @staticmethod
    def merge_event_list(list1, list2) :
        
        output_list = []
        ii = 0
        jj = 0

        while (ii < len(list1)) and (jj < len(list2)) :
            m1 = list1[ii]
            m2 = list2[jj]
            
            if m1.start_date < m2.start_date :
                output_list.append(m1)
                ii += 1
            else:
                output_list.append(m2)
                jj += 1
        
        while ii < len(list1) :
            output_list.append(list1[ii])
            ii += 1
            
        while jj < len(list2) :
            output_list.append(list2[jj])
            jj += 1
        
        return output_list
