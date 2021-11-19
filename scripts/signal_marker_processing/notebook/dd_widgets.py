#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Sun Oct 31 10:41:24 2021

from ipywidgets import (Text, VBox, Dropdown, SelectMultiple, DatePicker,
                        Button, HBox, HTML, Tab, Layout, Checkbox, ColorPicker,
                        IntText, FloatText)

import config
from ipyfilechooser import FileChooser
import json
import datetime
import os


class base_data_displayer_widget(VBox) :
    
    basic_colors = {"b" : "#0000ff",
                    "g" : "#00ff00",
                    "r" : "#ff0000",
                    "c" : "#00ffff",
                    "m" : "#ff00ff",
                    "y" : "#ffff00",
                    "k" : "#000000",
                    "w" : "#ffffff"}

    colors_to_keys = {"#0000ff" : "b",
                      "#00ff00" : "g",
                      "#ff0000" : "r",
                      "#00ffff" : "c",
                      "#ff00ff" : "m",
                      "#ffff00" : "y",
                      "#000000" : "k",
                      "#ffffff" : "w"}    
    """
    Summary:
        Base class for the widget associated to a data displayer.    
    """
    def __init__(self, signal_components : dict) :
        """
        Summary:
            Object constructor for the base_data_displayer_widget.
            
        Arguments:
            signal_components - dictionary with the signals available for plotting.
            
        Returns :
            The newly created object
            
        Note :
            Currently, a data displayer has the following syntax
            
            {
			"signals": ["ndvi","coh_norm"],
			"bottom_bar": "b08_b11_b04",
			"bottom_bar_components": ["B08_mean","B11_mean","B04_mean"],
			"start_date": "2018-04-01",
		    "stop_date": "2018-10-31",
		    "output_folder" : "./nl/results_rest", 
		    "file_name_prefix" : "s1_s2_compo",
		    "legend" : ["NDVI","Coherence Norm"],
		    "resolution" : 72,
		    "marker_signals" : ["coh_norm"],
		    "marker_plot_type" : "tl",
        	"marker_colors" : {"drop" : "b", "peak" : "y"},
            "ylabel" : "label",
            "add_months" : true,
            }
        """     
        
        # start creating the different widgets forming the base_data_displayer_widget
        self.signals = ["", *list(signal_components.keys())]
        
        self.wsm_signals = SelectMultiple(
                options=self.signals,
                value=[""],
                description="Signals:",
                placeholder="Signals",
                disabled=False
            )

        self.wdd_bottom_bar = Dropdown(
                options=self.signals,
                value="",
                description="Bottom Bar Signal:",
                placeholder="Bottom Bar Signal",
                disabled=False,
                layout={'width': 'max-content'}
            )
        
        self.wdd_red = Dropdown(
                options=[""],
                description="RED:",
                placeholder="RED",
                disabled=False,
                layout={'width': 'max-content'}
            )
        
        self.wdd_green = Dropdown(
                options=[""],
                description="GREEN:",
                placeholder="GREEN",
                disabled=False,
                layout={'width': 'max-content'}
            )

        self.wdd_blue = Dropdown(
                options=[""],
                description="BLUE:",
                placeholder="BLUE",
                disabled=False,
                layout={'width': 'max-content'}
            )                
        
        def on_bottom_bar_change(change) :
            components = [""]
                
            if self.wdd_bottom_bar.value in signal_components:
                components = signal_components[self.wdd_bottom_bar.value]
            
            self.wdd_red.options = components
            self.wdd_green.options = components
            self.wdd_blue.options = components
            
        self.wdd_bottom_bar.observe(on_bottom_bar_change, 'value')
        
        self.wh_bb_components = HBox([self.wdd_red,self.wdd_green,self.wdd_blue])
        
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
        
        # output folder
        self.wfc_outdir = FileChooser(
            placeholder='Output directory',
            description='Output directory:',
            disabled=False            
        )
        
        self.wfc_outdir.show_only_dirs = True

		# file name prefix
        self.wt_prefix = Text(
            placeholder='File name prefix',
            description='File name prefix:',
            disabled=False
            )
        
        self.whb_output_prop = HBox([VBox([HTML(value="<B>Output folder:<B>"), 
                                           self.wfc_outdir]), self.wt_prefix])

        self.wsm_markers = SelectMultiple(
                options=self.signals,
                value=[""],
                description="Marker signals:",
                placeholder="Marker signals",
                disabled=False,
                layout={'width': 'max-content'}
            )
        
        # Marker plot type
        self.whb_marker_plot_type = VBox(
            [ HTML(value="<B>Marker plot type:</B>"), 
              Checkbox(value=False, description='Triangle',disabled=False,indent=False),
              Checkbox(value=False, description='Line',disabled=False,indent=False)
            ], layout=Layout(border='1px solid black',width='25%'))

        self.whb_marker_colors = VBox([
            HTML(value="<B>Marker color:</B>"),
            ColorPicker(concise=True, description='Drop', value = "#ffffff", disabled=False,
                        indent=False),
            ColorPicker(concise=True, description='Peak', value = "#ffffff", disabled=False,
                        indent=False)],
            layout=Layout(border='1px solid black',width='25%'))

        self.whb_markers = HBox([self.wsm_markers, self.whb_marker_plot_type,
                                 self.whb_marker_colors],
                                 layout=Layout(align_items='center',
                                 justify_content='space-around'))

        self.wit_resolution = IntText(
            value=72,
            description='Image Resolution:',
            disabled=False,
            layout=Layout(width='25%', height='35px')
            )
        
        self.wt_ymin = FloatText(
            value=0,
            description='Y min:',
            disabled=False,
            tooltip="Minimum vertical value in plot",
            layout=Layout(width='25%', height='35px')
        )
        
        self.wt_ymax = FloatText(
            value=0,
            description='Y max:',
            disabled=False,
            tooltip="Maximum vertical value in plot",
            layout=Layout(width='25%', height='35px')    
            )
        
        self.wcb_add_months = Checkbox(
            description='Add month names', 
            value=True, 
            indent=False,
            layout=Layout(width='25%', height='35px'))

        self.whb_plot_prop = HBox([self.wit_resolution,
            Text(description='Legend', disabled=False,layout=Layout(width='25%', height='35px')),
            Text(description='Y label', disabled=False,layout=Layout(width='25%', height='35px'))],
            layout = Layout(align_items='center', justify_content='space-around'))                      

        self.whb_plot_prop2 = HBox(
            [self.wt_ymin, self.wt_ymax, self.wcb_add_months],
            layout = Layout(align_items='center', justify_content='space-around'))
        
        super().__init__([self.wsm_signals,
                          self.wdd_bottom_bar, self.wh_bb_components,
                          self.whb_dates,
                          self.whb_output_prop,
                          self.whb_markers,
                          self.whb_plot_prop,
                          self.whb_plot_prop2])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the displayer and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the displayer.            
        """
        out_dict = {}
        
        out_dict["signals"] = list(self.wsm_signals.value)
        
        if self.wdd_bottom_bar.value != "" :
            out_dict["bottom_bar"] = self.wdd_bottom_bar.value
            out_dict["bottom_bar_components"] = [self.wdd_red.value,
                                                 self.wdd_green.value,
                                                 self.wdd_blue.value]
            
        if self.whb_dates.children[0].value is not None :
            out_dict["start_date"] = self.whb_dates.children[0].value.strftime("%Y-%m-%d")
			
        if self.whb_dates.children[1].value is not None :
            out_dict["stop_date"] = self.whb_dates.children[1].value.strftime("%Y-%m-%d")
            
            
        
        if self.wfc_outdir.selected_path is not None :
            out_dict["output_folder"] = self.wfc_outdir.selected_path
        else :            
            out_dict["output_folder"] = "./results"
            if not os.path.exists("./results") :
                try :
                    os.makedirs("./results")
                except :
                    print("Unable to create output folder")
        
        if self.wt_prefix.value != "" :
            out_dict["file_name_prefix"] = self.wt_prefix.value
        
        if self.whb_plot_prop.children[1].value != "" :
            leg_val = self.whb_plot_prop.children[1].value.split(",")
            leg_val = [name.strip() for name in leg_val]
            out_dict["legend"] = leg_val
            
        if self.whb_plot_prop.children[2].value != "" :
            out_dict["ylabel"] = self.whb_plot_prop.children[2].value
            
        if self.wcb_add_months.value :
            out_dict["add_months"] = True

        if self.wt_ymin.value < self.wt_ymax.value :
            out_dict["ylim"] = [self.wt_ymin.value, self.wt_ymax.value]
            
        out_dict["resolution"] = self.wit_resolution.value       
        
        if "" not in self.wsm_markers.value :
            out_dict["marker_signals"] = list(self.wsm_markers.value)
            
        color_dict = {}
        if self.whb_marker_colors.children[1].value != "#ffffff" :
            if self.whb_marker_colors.children[1].value in \
                base_data_displayer_widget.colors_to_keys :
            
                color_dict["drop"] = \
                base_data_displayer_widget.colors_to_keys[self.whb_marker_colors.children[1].value]
            else :
                color_dict["drop"] = self.whb_marker_colors.children[1].value
            
        if self.whb_marker_colors.children[2].value != "#ffffff" :
            if self.whb_marker_colors.children[2].value in \
                base_data_displayer_widget.colors_to_keys :
            
                color_dict["peak"] = \
                base_data_displayer_widget.colors_to_keys[self.whb_marker_colors.children[2].value]
            else :
                color_dict["peak"] = self.whb_marker_colors.children[2].value
                
        if len(color_dict) > 0 :
            out_dict["marker_colors"] = color_dict
            
        mp_type = ""
        if self.whb_marker_plot_type.children[1].value :
            mp_type = mp_type + "t"

        if self.whb_marker_plot_type.children[2].value :
            mp_type = mp_type + "l"        

        if mp_type != "" :        
            out_dict["marker_plot_type"] = mp_type
        
        return out_dict
    
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data displayer widget using a dictionary, which needs to 
            have the same format has that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data displayer
            widget

        Returns:
            Nothing.  
        """
        
        # Add the signal
        if "signals" in options :
            self.wsm_signals.value = options["signals"]
        else :
            self.wsm_signals.value = tuple([""])
            
        # Bottom bar
        if "bottom_bar" in options :
            self.wdd_bottom_bar.value = options["bottom_bar"]
        else :
            self.wdd_bottom_bar.value = ""
            
        if "bottom_bar_components" in options :
            bb_components = options["bottom_bar_components"]

            if len(bb_components) >= 1 :
                self.wdd_red.value = bb_components[0]

            if len(bb_components) >= 2 :
                self.wdd_green.value = bb_components[1]
                
            if len(bb_components) >= 3 :
                self.wdd_blue.value = bb_components[2]
                
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

        # Output folder/files parameters        
        if "output_folder" in options :
            # create the output directory if it does not exist
            try :
                if not os.path.exists(options["output_folder"]) :
                    os.makedirs(options["output_folder"])
                    
                self.wfc_outdir.reset(path = options["output_folder"])
            except :
                print("Unable di set output folder")
        else :
            self.wfc_outdir.reset()

        if "file_name_prefix" in options :
            self.wt_prefix.value = options["file_name_prefix"]
        else :
            self.wt_prefix.value = ""

        # Legend
        if "legend" in options :
            self.whb_plot_prop.children[1].value = ", ".join(options["legend"])
        
        # ylabel
        if "ylabel" in options :
            self.whb_plot_prop.children[2].value = options["ylabel"]
        else :
            self.whb_plot_prop.children[2].value = ""
        
        # resolution
        if "resolution" in options :
            self.wit_resolution.value = options["resolution"]
        else :
            self.wit_resolution.value = 72
        
        if "marker_signals" in options :
            self.wsm_markers.value = options["marker_signals"]
        else : 
            self.wsm_markers.value = tuple([""])
            
        # marker colors
        if "marker_colors" in options :
            color_dict = options["marker_colors"]
            
            if "drop" in color_dict :
                if color_dict["drop"][0] != "#" :
                    if color_dict["drop"][0] in base_data_displayer_widget.basic_colors :
                        color = base_data_displayer_widget.basic_colors[color_dict["drop"][0]]
                    else :
                        color = "#ffffff"
                    self.whb_marker_colors.children[1].value = color
                else :
                    self.whb_marker_colors.children[1].value = color_dict["drop"]
            else :
                self.whb_marker_colors.children[1].value = "#ffffff"
            
            if "peak" in color_dict :
                if color_dict["peak"][0] != "#" :
                    if color_dict["peak"][0] in base_data_displayer_widget.basic_colors :
                        color = base_data_displayer_widget.basic_colors[color_dict["peak"][0]]
                    else :
                        color = "#ffffff"
                    self.whb_marker_colors.children[2].value = color
                else :
                    self.whb_marker_colors.children[2].value = color_dict["peak"]
            else :
                self.whb_marker_colors.children[2].value = "#ffffff"
            
        else :
            self.whb_marker_colors.children[1].value = "#ffffff"
            self.whb_marker_colors.children[2].value = "#ffffff"
            
        mp_type = ""
        if "marker_plot_type" in options :
            mp_type = options["marker_plot_type"]
            
        if "t" in mp_type :
            self.whb_marker_plot_type.children[1].value = True
        else :
            self.whb_marker_plot_type.children[1].value = False

        if "l" in mp_type :
            self.whb_marker_plot_type.children[2].value = True
        else :
            self.whb_marker_plot_type.children[2].value = False
        
        # Add months 
        if ("add_months" in options) and options["add_months"] :
            self.wcb_add_months.value = True
        else :
            self.wcb_add_months.value = False
            
        # y limits
        if ("ylim" in options) and (len(options["ylim"]) == 2)  :
            ymin = options["ylim"][0]
            ymax = options["ylim"][1]
            
            if ymin < ymax :
                self.wt_ymin.value = ymin
                self.wt_ymax.value = ymax
        
class data_displayer_tab(VBox) :
    """
    Summary:
        Widget containing several data displayer widgets        
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
        # Tab count (to keep track of the tab)
        self.count = 0
        
        self.signal_components = signal_components
        
        # List of data displayers
        self.data_displayers = [base_data_displayer_widget(signal_components)]
        
        self.wt_data_displayers = Tab(self.data_displayers)
        self.wt_data_displayers.set_title(self.count, f"Figure {self.count+1}")
        self.count += 1
        # Add and remove buttons
        self.wb_add = Button(
            description='Add',
            disabled=False,
            icon='Add'
        )
    
        self.wb_remove = Button(
                        description='Remove',
                        disabled=False,
                        icon='Remove'
        )
        
        @self.wb_add.on_click
        def wb_add_on_click(b):
            # Append a new data displayer
            self.data_displayers.append(base_data_displayer_widget(signal_components))
            
            self.wt_data_displayers.children = self.data_displayers
            self.wt_data_displayers.set_title(self.count, f"Figure {self.count+1}")
            self.count += 1
            
        @self.wb_remove.on_click
        def wd_remove_on_click(b):
            
            if len(self.data_displayers) > 1 :
                self.data_displayers.pop()
                self.count -= 1
            else :
                # Empty tab
                self.data_displayers = [base_data_displayer_widget(signal_components)]
                
            self.wt_data_displayers.children = self.data_displayers
         
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
            
        super().__init__([self.wt_data_displayers, HBox([self.wb_add, self.wb_remove]),\
                          self.wb_save, self.whb_load])
            
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
        for data_disp in self.data_displayers :
            tab_list.append(data_disp.dump())
            
        out_dict = {"data-displayers" : tab_list}
        
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
        
        if ("data-displayers" not in options) and ("data-displayer" not in options) :
            return
        
        if "data-displayers" in options :
            # get the tab list
            tab_list = options["data-displayers"]
            
        elif "data-displayer" in options :
            # get the tab list
            tab_list = [options["data-displayer"]]
        
        # delete all the data displayers
        self.data_displayers = []
        
        for tab in tab_list :
            data_disp = base_data_displayer_widget(self.signal_components)
            data_disp.initialize(tab)
            self.data_displayers.append(data_disp)
            
        self.wt_data_displayers.children = self.data_displayers
        
        self.count = 0
        for ii in range(len(tab)) :
            self.wt_data_displayers.set_title(self.count, f"Figure {self.count+1}")
            self.count += 1
            
        self.children = [self.wt_data_displayers, HBox([self.wb_add, self.wb_remove]),\
                          self.wb_save, self.whb_load]
