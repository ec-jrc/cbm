#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio, Csaba WIRNHARDT
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

from ipywidgets import Button, VBox, HTML
import json

import sys
sys.path.append('../')
import time_series_sources as tss



# All the objects that should be initialized
from pds_widgets import parcel_data_source_widget
from dr_widgets import DataReaderTab
from pp_widgets import processing_tab
from md_widgets import marker_detector_tab
from dd_widgets import data_displayer_tab

from ma_widgets import action_line
from se_widgets import scenario_evidence_widget

import config

class w_initializer(VBox) :
    """
    Summary:
        Class allowing the initialization of all the elements in notebook
        for the creation of an option file.
    """
    def __init__(self, ps : parcel_data_source_widget, drt : DataReaderTab, \
                 pt : processing_tab, mdt : marker_detector_tab, \
                 ddt : data_displayer_tab, al : action_line, \
                 sew : scenario_evidence_widget, option_file_path : str) :
        
        self.wb_initialize = Button(
            description='Initialize All',
            disabled=False,
            icon='Initialize'
        )
        
        @self.wb_initialize.on_click
        def owb_initialize_all_on_click(b) :
            # Open the option file
            optionFile = open(option_file_path)
            options = json.load(optionFile)
            
            # initialize the parcel data source widget
            ps.initialize(options)
            _dict = ps.dump()
            key = list(_dict.keys())[0]
            value = _dict[key]
            config.set_value(key, value)            

        
            # Do the same with the data reader tab
            drt.initialize(options)
            _dict = drt.dump()
            key = list(_dict.keys())[0]
            value = _dict[key]
            config.set_value(key, value)            
            
            
            # Get the signals available
            # Create the actual time series sources
            ts_options = drt.dump()
            ts_source_factory = tss.time_serie_source_factory()
            ts_sources = ts_source_factory.get_time_series_sources(ts_options)
    
            # Build the signal/components dictionary
            signal_components = {}
            for ts_source in ts_sources :
                signal_components[ts_source.get_signal_type()] = ts_source.get_components()
            
            # Initialize the preprocessing tab
            pt.signal_components = signal_components
            pt.initialize(options)
            _dict = pt.dump()
            key = list(_dict.keys())[0]
            value = _dict[key]
            config.set_value(key, value)            
            
            
            # Merge the signal/component dictionaries
            sc_dict = {**signal_components, **(pt.get_signal_components())}
            
            # Re-initialize the marker detector tab
            mdt.signal_components = sc_dict
            mdt.initialize(options)
            _dict = mdt.dump()
            key = list(_dict.keys())[0]
            value = _dict[key]
            config.set_value(key, value)            
            
            # Initialize the marker aggregation tab
            al.signals = list(sc_dict.keys())
            al.initialize(options)
            _dict = al.dump()
            key = list(_dict.keys())[0]
            value = _dict[key]
            config.set_value(key, value)  
            
            # Initialize the scenario evidence widget
            action_list = al.dump()["marker-aggregator"]
            marker_list = mdt.dump()["marker-detectors"]
            sew.available_markers = scenario_evidence_widget.get_markers_names( \
                                    action_list, marker_list )
            sew.initialize(options["scenario-evidence"])
            _dict = sew.dump()
            
            config.set_value("scenario-evidence", _dict)
            
            # Finally the data displayer
            ddt.signal_components = sc_dict
            ddt.initialize(options)
            _dict = ddt.dump()
            key = list(_dict.keys())[0]
            value = _dict[key]
            config.set_value(key, value)        
            
            print("Initialization Completed!")
            
            
        # Now call the base constructor
        super().__init__([HTML("<B>Initialize all elements</B>"), 
                          self.wb_initialize])
