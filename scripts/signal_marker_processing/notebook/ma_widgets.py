#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2022 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Sat Feb 19 14:48:34 2022
from ipywidgets import (Text, Button, VBox, Layout, BoundedIntText, \
                        Dropdown, HBox, Label)

from ipyfilechooser import FileChooser

from pp_widgets import SelectMultipleOrdered
import config
import json


class base_action(VBox) :
    # Class variable defying the type of action
    _type = ""
    
    def __init__(self, mk_signals : list) :
        """
        Summary :
            Object constructor.
        
        Arguments :
            mk_signals : list of signals available for performing the action.
        
        Returns:
            Nothing.
        """
        
        # Add a selection box, to select the signals on which the action should
        # be performed
        
        self.label = Label("Action: " + self.__class__._type)
        
        self.wsm_signals = SelectMultipleOrdered(
                options=mk_signals,
                description="Signals:",
                placeholder="Signals",
                disabled=False
            )
        
        # Textbox with the name of the output signal
        self.wt_outsig = Text(
                description="Output name:",
                placeholder="output",
                disabled=False
            )
        
        super().__init__([self.label, self.wsm_signals, self.wt_outsig],
                         layout=Layout(border='1px solid black'))
        
    def dump(self) -> dict :
        
        out_dict = {"action" : self.__class__._type}
        
        signals = list(self.wsm_signals.ordered_value)
        if (len(signals) >= 1) and (signals[0] != "") :
            out_dict["signals"] = signals
        
        if self.wt_outsig.value != "" :
            out_dict["outname"] = self.wt_outsig.ordered_value
        
        return out_dict
    
    def initialize(self, options : dict) :
        
        if "signals" in options :
            self.wsm_signals.value = options["signals"]

    def get_output_signal(self) :
        return self.wt_outsig.value
    
class merge_action(base_action) :
    _type = "merge"
    
class confirm_action(base_action) :
    _type = "confirm"
    
class aggregate_action(base_action) :
    _type = "aggregate"
    
    def __init__(self, mk_signals : list) :
        
        # first call the base class constructor
        super().__init__(mk_signals)
        
        # add the "overlapping" box
        self.wt_overlap = BoundedIntText(
            value = 7,
            min=0,
            step=1,
            description='Overlap:',
            disabled=False
        )
        
        self.children = [*self.children, self.wt_overlap]
    
    def dump(self) :
        out_dict = super().dump()
        
        out_dict["overlap"] = self.wt_overlap.value
        
        return out_dict
    
    def initialize(self, options) :
        super().initialize(options)
        
        if "overlap" in options :
            self.wt_overlap.value = options["overlap"]
        
class action_line(VBox) :
    """
    Class implementing the list of actions to be performed for merging markers. 
    """
    
    # List of actions currently supported
    pro_supported = ["merge", "confirm", "aggregate"]
    
    def __init__(self, marker_signals : list ) :
        """
        Summary:
            Object constructor.
            
        Arguments:
            marker_signals : list of signals available for performing actions
                             Each signal identifies a marker
        """
        # list of available signals
        self.signals = marker_signals
        
        # list of action widgets
        self.action_list = []
                        
        self.wb_add = Button(
            description='Add',
            disabled=False,
            icon='Add'
        )
        
        self.wdd_types = Dropdown(
                options = action_line.pro_supported,
                disabled = False
            ) 
    
        self.wb_remove = Button(
                        description='Remove',
                        disabled=False,
                        icon='Remove'
                    )
        
        supported_types = [x._type for x in base_action.__subclasses__()]
               
        @self.wb_add.on_click
        def wb_add_on_click(b):
        
            # Add a new action as input
            ind = supported_types.index(self.wdd_types.value)
            
            signals = self.signals.copy()
            for ii, action in enumerate(self.action_list) :
                action_signal = action.get_output_signal()
                
                if action_signal == "" :
                    action_signal = "output_" + str(ii)
                
                signals.append(action_signal)
            
            # create the new widget
            new_w = base_action.__subclasses__()[ind](signals) 
            
            self.action_list.append(new_w)
                        
            self.children = [*self.action_list, \
                             HBox([self.wb_add, self.wdd_types]), \
                             self.wb_remove, self.wb_save, self.whb_load]
            
        @self.wb_remove.on_click
        def wd_remove_on_click(b):
            
            if len(self.action_list) > 0 :
                self.action_list.pop()
                
                self.children = [*self.action_list, \
                                 HBox([self.wb_add, self.wdd_types]), \
                                 self.wb_remove, self.wb_save, self.whb_load]
        
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
            
            # Add a default marker-sink (to be dealt with
            # in a second phase)
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
            
        super().__init__([*self.action_list, \
                          HBox([self.wb_add, self.wdd_types]), \
                          self.wb_remove, self.wb_save, self.whb_load])
            
    def dump(self) -> dict:
        """
        Summary:
            Build and return a dictiory descibing the marker aggregator actions 
            and its options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the marker aggregator.  
        """
        action_dicts = []
        
        for action in self.action_list :
            action_dicts.append(action.dump())
        
        out_dict = {"marker-aggregator" : action_dicts}
        
        return out_dict
    
    def initialize(self, options : list) :
        """
        Summary:
            Initialize the marker aggregator widget using a dictionary, 
            which needs to have the same format as that produced by the 
            dump function.
        
        Arguments:
            options - dictionary with the options to initialize the marker aggregator.

        Returns:
            Nothing.  
        """
        
        if ("marker-aggregator" not in options):
            return
        else : 
            # get the action list
            action_list = options["marker-aggregator"]
            
        # delete all the data readers
        self.action_list = []
        
        # supported types 
        supported_types = [x._type for x in base_action.__subclasses__()]
        
        signals = self.signals.copy()
        
        ii = 0
        for action in action_list :
            if ("action" in action) and (action["action"] in supported_types) : 
                ind = supported_types.index(action["action"])
                new_w = base_action.__subclasses__()[ind](signals)
                new_w.initialize(action)
                self.action_list.append(new_w)
                
                action_signal = new_w.get_output_signal()
                if action_signal == "" :
                    action_signal = "output_" + str(ii)
                signals.append(action_signal)
                ii += 1
            
        self.children = [*self.action_list, \
                          HBox([self.wb_add, self.wdd_types]), \
                          self.wb_remove, self.wb_save, self.whb_load]