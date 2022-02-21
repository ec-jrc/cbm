#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2022 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Mon Feb 21 09:25:29 2022

from ipywidgets import (Button, VBox, Dropdown, HBox,\
                        RadioButtons, Box, Label)
    
from ipyfilechooser import FileChooser

import config
import json


class scenario_evidence_widget(VBox) :
    """    
    Summary:
        Class defining the widget for the scenario evidence configuration.        
    """
    
    mkdet2mk = { "data-gaps" : "gap",
                 "peak-detector" : "peak",
                 "drop-detector" : "drop",
                 "state_change" : "state_change"
                
        }
    
    def __init__(self, action_list : list, marker_list : list ) :
        """    
        Summary:
            Object constructor.
    
        Arguments:
            action_list - list of actions defining the combination of markers
            marker_list - list of options for the marker detections
    
        Returns:
            Nothing.        
        """ 
        
        # get the list of available markers
        self.available_markers = scenario_evidence_widget.get_markers_names( \
                                    action_list, marker_list )
        
        self.wdd_primary_marker = Dropdown(
            description = "Primary Marker:",
            options = self.available_markers,
            disabled = False
        )
        
        self.wdd_gap = Dropdown(
            description = "Gap Marker:",
            options = self.available_markers,
            disabled = False
        )
        
        self.wfc_output_file = FileChooser(
            placeholder='Output file',
            description='Output file:',
            disabled=False
        )
                
        self.header = RadioButtons(
                options=[
                ("True", "True"),
                ("False", "False")],
            value='True',
            layout={'width': 'max-content'}
        )
        
        # Cosmetic element, it will be place close to the radio buttons 
        self.header_box = Box([
            Label(value="Include Header:"),
            self.header]
        )

        self.confbox = VBox([self.wdd_primary_marker, self.wdd_gap, self.wfc_output_file,\
                             self.header_box])
        ############################## Standard buttons ####################### 
        self.wb_save = Button(
             description='Save',
             disabled=False,
             icon='save'
             )
    
        @self.wb_save.on_click
        def wb_save_on_click(b):
        
            # Create the output element in the JSON file
            _dict = self.dump()
            
            config.set_value("scenario-evidence", _dict)
                            
        self.wb_load = Button(
             description='Load',
             disabled=False,
             icon='load'
             )
        
        wfc_options = FileChooser(
            placeholder='Option file',
            description='Option file:',
            disabled=False
        )
        
        self.whb_load = HBox([self.wb_load, wfc_options])
        
        @self.wb_load.on_click
        def wb_load_on_click(b):
        
            if wfc_options.selected is not None :
                optionFile = open(wfc_options.selected)
                options = json.load(optionFile)
                
                if "scenario-evidence" in options :
                    self.initialize(options["scenario-evidence"])
            
        super().__init__([self.confbox, self.wb_save, self.whb_load])
    
    @staticmethod
    def get_markers_names(action_list : list, marker_list : list) -> list :
        
        # first build the list of basic markers
        basic_markers = {}
        for marker in marker_list :
            if marker["type"] in scenario_evidence_widget.mkdet2mk :
                basic_markers[marker["signals"][0]] = scenario_evidence_widget.mkdet2mk[marker["type"]]
        
        # Now build the composite marker
        input_marker = ""
        composite_markers = [*basic_markers.values()]
        
        for action in action_list :
            
            if action["action"] == "merge" :
                # merge does not create any new marker
                if len(action["signals"]) == 2 :
                    input_marker = action["signals"][0]
                    
                # else input_marker stay as before
                    
            if action["action"] == "confirm" :
                # confirm does not create any new marker
                if len(action["signals"]) == 2 :
                    input_marker = action["signals"][0]
                # else input_marker stay as before
                
            if action["action"] == "aggregate" :
                # confirm does create a new marker
                if len(action["signals"]) == 2 :
                    input_marker = action["signals"][0]
                    
                    new_marker = basic_markers[action["signals"][0]] + '-' + \
                                 basic_markers[action["signals"][1]]
                else : 
                    # input_marker stay as before            
                    new_marker = basic_markers[input_marker] + '-' + \
                                 basic_markers[action["signals"][0]]
                
                composite_markers.append(new_marker)
        
        return composite_markers
    
    def dump(self) -> dict :
        outdict = {}
        
        outdict["primary-marker"] = self.wdd_primary_marker.value
        
        outdict["gap-marker"] = self.wdd_gap.value
        
        if self.wfc_output_file.selected is not None :
            outdict["output_file"] = self.wfc_output_file.selected
        else :
            outdict["output_file"] = "./scenario_evidence.csv"
            
        header_value = False
        if self.header.value == "True" :
            header_value = True
            
        outdict["include_header"] = header_value
            
        return outdict
    
    def initialize(self, options : dict) :

        if "primary-marker" in options :
            self.wdd_primary_marker.options = self.available_markers
            self.wdd_primary_marker.value = options["primary-marker"]
            
        if "gap-marker" in options :
            self.wdd_gap.options = self.available_markers
            self.wdd_gap.value = options["gap-marker"]
            
        if "output_file" in options :
            try :
                full_path = options["output_file"].replace("\\","/")
                
                base_path = full_path[:full_path.rfind("/")+1]
                filename = full_path[full_path.rfind("/")+1:]
                self.wfc_output_file.reset(path=base_path, filename = filename)
                
            except :
                print("Unable to set path")
                
        if ("include_header" in options) and options["include_header"] :
            self.header.value = "True"
        else :
            self.header.value == "False"