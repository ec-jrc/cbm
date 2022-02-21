#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

from ipywidgets import (DatePicker, HBox, BoundedIntText, HTML, VBox, Tab,
                        Layout, SelectMultiple, Text, Checkbox, BoundedFloatText,
                        Button, Dropdown)
from ipyfilechooser import FileChooser

import datetime

import config
import json

class base_marker_detector_widget(VBox) :
    
    _type = ""    
    """
    Summary:
        Basic class defining the minimal interfaces for the marker detector
        widgets.        
    """
    def __init__(self, signal_components : dict, md_type = "", parent = None) :
        self.type = md_type
            
        self.parent = parent
        
        if self.parent is not None :
                try :
                    self.parent.set_title_from_widget(self)
                except :
                    print("Unable to set the Tab title.")
        
        # Retain only the signals (at this stage a single component should be present)
        self.signals = list(signal_components.keys())
        
        self.wsm_signals = SelectMultiple(
                options=["", *self.signals],
                value=[""],
                description="Signals:",
                placeholder="Signals",
                disabled=False
            )
        
        # Components
        self.components = signal_components
        
        # start date
        wdp_start_date = DatePicker(
                description='Start date:',
                disabled=False
            )
        
        # stop date
        wdp_stop_date = DatePicker(
                description='Stop date:',
                disabled=False
            )
        
        self.whb_dates = HBox([wdp_start_date, wdp_stop_date])
    
        # Max number of markers to detect
        self.wit_max_num = BoundedIntText(
            value = 0,
            min = 0,
            step = 1,
            description="Max Number of Markers:"
        )
        
        # Initialize the 
        super().__init__([HTML(value = f"<B>Processor type: {self.type}</B>"),
                         self.wsm_signals, self.whb_dates,
                         HTML(value = "<B>Options :</B>")
                         ],layout=Layout(border='1px solid black'))
        
        self.options = []
    
    def add_options(self, options = None) :
        """
        Summary:
            Add options related to a specific marker detector type.
        
        Arguments:
            options - list of widgets representing the options specific to 
            the marker detector
            
        Returns:
            Nothing.
        """
        
        if options is not None :
            self.children = [*self.children, *options]
            
            self.options = options
    
    def dump_header(self) -> dict :
        """
        Summary:
            Build and return the first part (header) of a dictionary descibing 
            the marker detector and its options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the marker detector.            
        """
        
        out_dict = {"type" : self.type}
        
        # Add the signal
        signals = list(self.wsm_signals.value)
        
        # Check if there is at list one signal
        if (len(signals) == 1) and (signals[0] != "") :
            out_dict["signals"] = signals
        else :
            return None
            
        # add the dates
        if self.whb_dates.children[0].value is not None :
            out_dict["start_date"] = self.whb_dates.children[0].value.strftime("%Y-%m-%d")
			
        if self.whb_dates.children[1].value is not None :
            out_dict["stop_date"] = self.whb_dates.children[1].value.strftime("%Y-%m-%d")
        
        # add the maximum number of markers
        max_num = self.wit_max_num.value
        
        if max_num > 0 :
            out_dict["max_number"] = max_num
            
        return out_dict
    
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictionary descibing the marker detector and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the marker detector.            
        """
        out_dict = self.dump_header()
            
        # Now add the options, if present
        for wd in self.options :
            key = wd.description
            
            # Eventually remove the last colon
            if key[-1] == ":" :
                key = key[:-1]
                
            value = wd.value
            
            if value is None :
                continue
            
            if (type(value) is str) and (value == "") :
                continue
            
            if type(value) is tuple :
                value = list(value)
                            
            out_dict[key] = value
        
        return out_dict
    
    def initialize(self, options) :
        """
        Summary:
            Initialize the marker detector using a dictionary, which needs to 
            have the same format has that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the marker detector.

        Returns:
            Nothing.  
        """        
        # Add the signal
        if ("signals" in options) :
            self.wsm_signals.value = list(set(options["signals"]) & set(self.wsm_signals.options))
        else :
            self.wsm_signals.value = tuple([""])
            
        # Start and stop dates
        if "start_date" in options :
           self.whb_dates.children[0].value = datetime.datetime.strptime(options["start_date"],
                                                                         "%Y-%m-%d")
        else :
            self.whb_dates.children[0].value = None
           
        if "stop_date" in options :
           self.whb_dates.children[1].value = datetime.datetime.strptime(options["stop_date"],
                                                                         "%Y-%m-%d")
        else :			
            self.whb_dates.children[1].value = None
        
        if "max_number" in options :
            self.wit_max_num.value = options["max_number"]
             
        # Now add specific options, if present
        for wd in self.options :
            key = wd.description
            
            # Eventually remove the last colon
            if key[-1] == ":" :
                key = key[:-1]
        
            if key in options :
                if isinstance(wd, Text) and isinstance(options[key], list) :
                    wd.value = ", ".join(options[key]) 
                else :
                    wd.value = options[key]
                    
        # Set the children of the widget
        self.children = [HTML(value = f"<B>Processor type: {self.type}</B>"),
                         self.wsm_signals, self.whb_dates,
                         HTML(value = "<B>Options :</B>"),
                         *self.options]
        
class gap_detector_widget(base_marker_detector_widget) :
    """
    Summary:
        Class defining the widget for the gap detector.        
    """
    
    _type = "data-gaps"
    
    def __init__(self, signal_components : dict, parent = None) :
        """
        Summary:
            Object constructor.
        
        Arguments :
            signal_components - dictionary with the signal/components names
        """    
        super().__init__(signal_components, gap_detector_widget._type, parent)
        
        wbit_min_gap_len = BoundedIntText(
                    description = "min_gap_len:",
                    value = 20,
                    min = 0,
                    step = 1,
                    disabled=False)
        
        self.add_options([wbit_min_gap_len])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictionary descibing the marker detector and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the marker detector.            
        """
        out_dict = self.dump_header()
        
        # Remark:
        #
        # self.options = [wbit_min_gap_len]
        if self.options[0].value > 0 :
            out_dict["min_gap_len"] = self.options[0].value
                   
        return out_dict    

class state_change_detector_widget(base_marker_detector_widget) :
    """
    Summary:
        Class defining the widget for the state change detector.        
    """
    
    _type = "state_change"
    
    def __init__(self, signal_components : dict, parent = None) :
        """
        Summary:
            Object constructor.
        
        Arguments :
            signal_components - dictionary with the signal/components names
            parent - reference to the parent widget
        """
        super().__init__(signal_components, state_change_detector_widget._type, parent)
        
        wbit_min_duration = BoundedIntText(
                    description = "min_duration:",
                    value = 7,
                    min = 0,
                    step = 1,
                    disabled=False)
        
        wbit_to_state = BoundedIntText(
                    description = "to_state:",
                    value = 4,
                    min = 0,
                    step = 1,
                    disable = False)
        
        self.add_options([wbit_min_duration, wbit_to_state])

    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictionary descibing the marker detector and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the marker detector.            
        """
        out_dict = self.dump_header()
        
        # Remark:
        #
        # self.options = [wbit_min_duration, wbit_to_state]
        if self.options[0].value > 0 :
            out_dict["min_duration"] = self.options[0].value
            
        out_dict["to_state"] = self.options[1].value
                   
        return out_dict       
class drop_detector_widget(base_marker_detector_widget) :
    """
    Summary:
        Class defining the widget for the drop detector.        
    """
    
    _type = "drop-detector"
    
    def __init__(self, signal_components : dict, parent = None) :
        """
        Summary:
            Object constructor.
        
        Arguments :
            signal_components - dictionary with the signal/components names
        """    
        super().__init__(signal_components, drop_detector_widget._type, parent)
        
        # Add specific options
        wbit_aggregate = BoundedIntText(
                            description = "aggregate:",
                            value = 0,
                            min = 0,
                            step = 1,
                            disabled=False)
        
        wcb_filter_by_angle = Checkbox(value=False, description='filter_by_angle:',disabled=False)

        wbit_min_duration = BoundedIntText(
                            description = "min_duration:",
                            value = -1,
                            min = -1,
                            step = 1,
                            disabled=False)
        
        wbit_min_drop = BoundedFloatText(
                            description = "min_drop:",
                            value = -1,
                            min = -1,
                            step = 1,
                            disabled=False)
        
        self.add_options([wbit_min_duration, wbit_min_drop, wcb_filter_by_angle,
                          wbit_aggregate])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictionary descibing the marker detector and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the marker detector.            
        """

        out_dict = self.dump_header()
        
        # Remark:
        #
        # self.options = [wbit_min_duration, wbit_min_drop, wcb_filter_by_angle,
        #                   wbit_aggregate]
        if self.options[0].value > 0 :
            out_dict["min_duration"] = self.options[0].value
            
        if self.options[1].value > 0 :
            out_dict["min_drop"] = self.options[1].value
            
        if self.options[2].value == True :
            out_dict["filter_by_angle"] = True
            
        if self.options[3].value > 0 :
            out_dict["aggregate"] = self.options[3].value
        
        return out_dict
    
class peak_detector_widget(base_marker_detector_widget) :
    """
    Summary:
        Class defining the widget for the drop detector.        
    """
    _type = "peak-detector"
    
    def __init__(self, signal_components : dict, parent = None) :
        """
        Summary:
            Object constructor.
        
        Arguments :
            signal_components - dictionary with the signal/components names
        """    
        super().__init__(signal_components, peak_detector_widget._type, parent)
        
        # Add specific options
        wbit_aggregate = BoundedIntText(
                            description = "aggregate:",
                            value = 0,
                            min = 0,
                            step = 1,
                            disabled=False)
        
        wcb_filter_by_angle = Checkbox(value=False, description='filter_by_angle:',disabled=False)

        wbit_min_duration = BoundedIntText(
                            description = "min_duration:",
                            value = -1,
                            min = -1,
                            step = 1,
                            disabled=False)
        
        wbit_min_increase = BoundedFloatText(
                            description = "min_increase:",
                            value = -1,
                            min = -1,
                            step = 1,
                            disabled=False)
        
        self.add_options([wbit_min_duration, wbit_min_increase, wcb_filter_by_angle,
                          wbit_aggregate])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictionary descibing the marker detector and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the marker detector.            
        """
        out_dict = self.dump_header()
        
        # Remark:
        #
        # self.options = [wbit_min_duration, wbit_min_drop, wcb_filter_by_angle,
        #                   wbit_aggregate]
        if self.options[0].value > 0 :
            out_dict["min_duration"] = self.options[0].value
            
        if self.options[1].value > 0 :
            out_dict["min_increase"] = self.options[1].value
            
        if self.options[2].value == True :
            out_dict["filter_by_angle"] = True
            
        if self.options[3].value > 0 :
            out_dict["aggregate"] = self.options[3].value
        
        return out_dict
    
class marker_detector_tab(VBox) :
    """
    Summary:
        Widget containing several marker detector widgets        
    """
    def __init__(self, signal_components : dict)  :      
        """
        Summary:
            Object constructor.
        
        Arguments:
            signal_components - dictionary with the signal components.
            
        Returns:
            Nothing.
        """
        self.signal_components = signal_components
        self.count = 0
        
        # List of marker detectors
        self.marker_detectors = []
        
        self.wt_marker_detectors = Tab()
        
        self.wb_add = Button(
            description='Add',
            disabled=False,
            icon='Add'
        )
        
        supported_types = [x._type for x in base_marker_detector_widget.__subclasses__()]
        self.wdd_types = Dropdown(
                options = supported_types,
                disabled = False
            ) 
    
        self.wb_remove = Button(
                        description='Remove',
                        disabled=False,
                        icon='Remove'
                    )
    
        @self.wb_add.on_click
        def wb_add_on_click(b):
            
            new_w = None
            
            md_type = self.wdd_types.value
            
            if md_type in supported_types : 
                ind = supported_types.index(md_type)
                new_w = base_marker_detector_widget.__subclasses__()[ind](self.signal_components)
                                
            if new_w is not None :
                self.marker_detectors.append(new_w)
                self.wt_marker_detectors.children = self.marker_detectors
                self.wt_marker_detectors.set_title(self.count, new_w.type)
                self.count += 1
        
        @self.wb_remove.on_click
        def wd_remove_on_click(b):
            
            if len(self.marker_detectors) :
                self.marker_detectors.pop()
                self.count -= 1
                
            self.wt_marker_detectors.children = self.marker_detectors
         
        self.wb_save = Button(
             description='Save',
             disabled=False,
             icon='save'
             )
    
        @self.wb_save.on_click
        def wb_save_on_click(b):
        
            # Create the output element in the JSON file
            _dict = self.dump()
            
            key = list(_dict.keys())[0]
            value = _dict[key]
           
            config.set_value(key, value)
            
            # Add an empty key for the marker-aggregator (to be dealt with
            # in a second phase)
            if config.get_value("marker-aggregator") is None :
                config.set_value("marker-aggregator", [{}])
            
                # Add a default marker-sink (to be dealt with
                # in a second phase)
                config.set_value("marker-sink", [
                    {"output_file": "./marker_output.csv",
                     "include_header": True}])
            else :
                config.set_value("marker-sink", [
                    {"output_file": "./marker_output.csv",
                     "include_header": True},
                    {"output_file": "./agg_marker_output.csv",
                     "include_header": True}
                    ])
                
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
                
                self.initialize(options)
            
        super().__init__([self.wt_marker_detectors, HBox([self.wb_add, self.wdd_types]), 
                          self.wb_remove, self.wb_save, self.whb_load])
            
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the data displayer tab and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the preprocessor.  
        """
        tab_list = []
        
        # Build the list of data displayers
        for data_disp in self.marker_detectors :
            tab_list.append(data_disp.dump())
            
        out_dict = {"marker-detectors" : tab_list}
        
        return out_dict
    
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data displayer tab using a dictionary, which needs to 
            have the same format has that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data displayer tab

        Returns:
            Nothing.  
        """
        
        if "marker-detectors" not in options :
            return
        else : 
            tab_list = options["marker-detectors"]
                    
        # delete all the marker detectors
        self.marker_detectors = []
        self.count = 0
        
        # supported types 
        supported_types = [x._type for x in base_marker_detector_widget.__subclasses__()]
        
        for tab in tab_list :
            if ("type" in tab) and (tab["type"] in supported_types) : 
                ind = supported_types.index(tab["type"])
                marker_detector = base_marker_detector_widget.__subclasses__()[ind](\
                                                        self.signal_components, self)
                marker_detector.initialize(tab)
                self.marker_detectors.append(marker_detector)
            
        self.wt_marker_detectors.children = self.marker_detectors
        for ii, wmd in enumerate(self.marker_detectors) :
            self.wt_marker_detectors.set_title(ii, wmd.type)
            
        self.count = len(self.marker_detectors)
        
        self.children = [self.wt_marker_detectors, HBox([self.wb_add, self.wdd_types]), 
                          self.wb_remove, self.wb_save, self.whb_load]
            
    def set_title(self, tab_index : int , title : str) :
        self.wt_marker_detectors.set_title(tab_index, title)
        
    def set_title_from_widget(self, child_tab) :
        
        # check if  the child_tab is a real children of the widget
        if child_tab not in self.marker_detectors :
            return
        
        index = self.marker_detectors.index(child_tab)
        title = child_tab.type
        
        self.set_title(index, title)
