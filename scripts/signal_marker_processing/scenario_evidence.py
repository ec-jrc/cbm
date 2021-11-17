#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


class scenario_evidence :
    """
    Summary:
        Object responsible for creating the scenario evidence from the 
        aggregated markers and the parcel properties.
    """
    
    def __init__(self, options : dict) :
        """
        Summary:
            Object constructor.
            
        Arguments:
            options - dictionary defining the properties of the scenario
                      evidence
        Returns:
            Nothing.
        """

        # Check if the output file has been specified
        if "output_file" in options :
            filename = options["output_file"]
        else :
            filename = "./scenario_evidence_output.csv"
        
        # Open the output file
        self.out_file = open(filename, 'w')
        
        # Now check if the header should be printed
        include_header = False
        if "include_header" in options :
            include_header = options["include_header"]
        
        if include_header :
            self.out_file.write("FID,Area,Perimeter,S2_pixels,Shape index," \
                                "Side ratio,Nb primary markers,Nb data gaps,"\
                                "Nb other markers\n")
        
        self.primary_marker = options["primary-marker"]
        
        if "gap-marker" in options :
            self.data_gap = options["gap-marker"]
        else :
            self.data_gap = None
        return

    def dump(self, fid, aggregated_markers, properties) :
        """
        Summary:
            Function dumping the scenario evidence to file.
            
        Arguments:
            fid - the parcel ID
            aggregated_markers - list of aggregated markers
            properties - parcel properties.
            
        Returns:
            Nothing.
        """
        marker_types = [x.type for x in aggregated_markers]
        
        # count the number of primary markers
        primary_nb = len([p for p in marker_types if p == self.primary_marker])
        
        # count the number of data gaps
        if self.data_gap is not None :
            gap_nb = len([p for p in marker_types if p == self.data_gap])
        else :
            gap_nb = 0
            
        # number of other markers
        other_nb = len(aggregated_markers) - primary_nb - gap_nb
        
        # Now print the results
        out_str = str(fid) + ", "
        
        for key in properties :
            out_str = out_str + str(properties[key]) + ','
            
        out_str = out_str + str(primary_nb) + ','
        out_str = out_str + str(gap_nb) + ','
        out_str = out_str + str(other_nb) + '\n'
        
        self.out_file.write(out_str)

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
        
        
    
