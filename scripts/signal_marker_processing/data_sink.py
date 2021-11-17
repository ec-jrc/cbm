#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Tue Sep  7 16:37:12 2021


class marker_sink :
    """
    Summary:
        Object responsible for saving to csv file marker information.
    """
    def __init__(self, sink_options : dict) :
        """
        Summary :
            Object constructur.
        
        Arguments:
            options - dictionary with the options to initialize the object
        
        Returns:
            Nothing.
        """
                    
        # Check if the output file has been specified
        if "output_file" in sink_options :
            filename = sink_options["output_file"]
        else :
            filename = "./marker_output.csv"
        
        # Open the output file
        self.out_file = open(filename, 'w')
        
        # Now check if the header should be printed
        include_header = False
        if "include_header" in sink_options :
            include_header = sink_options["include_header"]
        
        if include_header :
            self.out_file.write("FID,signal,type,start_data,main_date," \
                                "stop_date,duration,value 1,value 2, value 3\n")
    
        return
    
    def dump_marker_info(self, fid, markers) :
        """
        Summary :
            Dump marker information to file.
        
        Arguments:
            fid - FOI identifier
        
        Returns:
            Nothing.
        """
        if isinstance(markers, list) :
            for marker in markers :
                self.out_file.write(str(fid) + ',-,' + \
                                    marker.__str__() + '\n')
        else :
            # loop on the signals
            for signal in markers :
                for marker in markers[signal] :
                    self.out_file.write(str(fid) + ',' + str(signal) + ',' + \
                                        marker.__str__() + '\n')
        
        return
    
    def __del__(self) :
        """
        Summary :
            Object destructur.
        
        Arguments:
            None.
            
        Returns:
            Nothing.
        """        
        
        # Do not forget to close the output file
        self.out_file.close()
