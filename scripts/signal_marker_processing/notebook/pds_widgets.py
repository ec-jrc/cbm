#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import geopandas as gpd
from ipyfilechooser import FileChooser

from ipywidgets import (VBox, Label, Dropdown,
                        Button, Layout, HBox,
                        RadioButtons, Box)
import config
import json
import os
from dr_widgets import connection_widget


class parcel_data_source_widget(VBox) :
    

    def __init__(self) :    
        # Radio buttons allowing one to select the type of parcel data source
        # to use
        self.sources = RadioButtons(
                options=[
                ("Text File", 'txt'),
                ("Text File and RESTful API", 'txt_rest'),
                ("From SHAPE File", 'shape'),
                ("From GeoJSON File", 'json')
            ],
            value='txt',
            layout={'width': 'max-content'}
        )
    
        # Cosmetic element, it will be place close to the radio buttons 
        self.sources_box = Box([
            Label(value="Parcel Data sources:"),
            self.sources]
        )
        
        info_txt = Label("From Text File only")
        info_txt_rest = Label("From Text File and RESTFul")
        info_shape = Label("From Shape File")
        info_json = Label("From GeoJSON File")

        # default option
        view_options = VBox([info_txt, source_from_txt()])
       
        def on_source_change(change):
            view_options.children = []
            if self.sources.value == 'txt':
                view_options.children = [info_txt, source_from_txt()]
            elif self.sources.value == 'txt_rest':
                view_options.children = [info_txt_rest, source_from_txt_rest()]
            elif self.sources.value == 'shape':
                view_options.children = [info_shape, source_from_shape()]
            elif self.sources.value == 'json':
                view_options.children = [info_json, source_from_shape('json')]
    
        self.sources.observe(on_source_change, 'value')
        
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
    
        super().__init__([self.sources_box, view_options, self.wb_save, self.whb_load],
                         layout=Layout(border='1px solid black'))
   
    def dump(self) -> dict:
        _dict = self.children[1].children[1].dump()
        
        out_dict = {"parcelSource" : _dict}
        
        return out_dict
        
    def initialize(self, options : dict) :
        
        if "parcelSource" not in options :
            return
        
        # keep only the relevant information
        ps_opt = options["parcelSource"]
        
        if "type" not in ps_opt :
            return 
        
        source_opt = [a[1] for a in self.sources.options]
        
        if ps_opt["type"] in source_opt :
                        
            self.sources.value = ps_opt["type"]
            view_options = VBox()
            
            info_txt = Label("From Text File only")
            info_txt_rest = Label("From Text File and RESTFul")
            info_shape = Label("From Shape File")
            info_json = Label("From GeoJSON File")
            
            if self.sources.value == 'txt':
                source = source_from_txt()
                source.initialize(ps_opt)
                view_options.children = [info_txt, source]
            elif self.sources.value == 'txt_rest':
                source = source_from_txt_rest()
                source.initialize(ps_opt)
                view_options.children = [info_txt_rest, source]
            elif self.sources.value == 'shape':
                source = source_from_shape()
                source.initialize(ps_opt)
                view_options.children = [info_shape, source]
            elif self.sources.value == 'json':
                source = source_from_shape('json')
                source.initialize(ps_opt)
                view_options.children = [info_json, source]
            
            self.children = [self.sources_box, view_options, self.wb_save, self.whb_load]
        
        def on_source_change(change):
            view_options.children = []
            if self.sources.value == 'txt':
                view_options.children = [info_txt, source_from_txt()]
            elif self.sources.value == 'txt_rest':
                view_options.children = [info_txt_rest, source_from_txt_rest()]
            elif self.sources.value == 'shape':
                view_options.children = [info_shape, source_from_shape()]
            elif self.sources.value == 'json':
                view_options.children = [info_json, source_from_shape('json')]
    
        self.sources.observe(on_source_change, 'value')

class source_from_txt(VBox) :
    
    def __init__(self) :
        self.wt_text_file = FileChooser( 
            filter_pattern = '*.txt',
            multiple=False)
                            
        super().__init__([self.wt_text_file])
        
    def dump(self) -> dict :
        out_dict = {}
        
        out_dict["type"] = "txt"
        
        if self.wt_text_file.selected is not None :
            out_dict["fid_list_file"] = self.wt_text_file.selected
        else :
            if self.wt_text_file.default is not None :
                out_dict["fid_list_file"] = self.wt_text_file.default
        
        return out_dict
    
    def initialize(self, options : dict) :
        
        if "fid_list_file" in options :
            try :
                full_path = options["fid_list_file"].replace("\\","/")
                
                if os.path.isfile(full_path) :                                
                    base_path = full_path[:full_path.rfind("/")+1]
                    filename = full_path[full_path.rfind("/")+1:]
                    self.wt_text_file.reset(path=base_path, filename = filename)
                                
            except :
                print("Unable to set path")

class source_from_txt_rest(VBox) :
        
    def __init__(self) :
        
        self.wt_text_file = FileChooser( 
            filter_pattern = '*.txt',
            multiple=False)
         
        self.wc_connection = connection_widget()
        
        super().__init__([self.wt_text_file, self.wc_connection])
        
    def dump(self) -> dict :
        out_dict = {}
        
        out_dict["type"] = "txt_rest"
    
        if self.wt_text_file.selected is not None :
            out_dict["fid_list_file"] = self.wt_text_file.selected
            
        out_dict["connection_options"] = self.wc_connection.dump()
        
        return out_dict
    
    def initialize(self, options : dict) :
        
        if "fid_list_file" in options :
            try :
                full_path = options["fid_list_file"].replace("\\","/")
                
                if os.path.isfile(full_path) :
                    base_path = full_path[:full_path.rfind("/")+1]
                    filename = full_path[full_path.rfind("/")+1:]
                    self.wt_text_file.reset(path=base_path, filename = filename)
            except :
                print("Unable to set path")
    
        if "connection_options" in options :
            self.wc_connection.initialize(options["connection_options"])
            
class source_from_shape(VBox) :
        
    def __init__(self, _type : str = "shape") :
        
        self.type = _type
        
        if _type == 'shape' :
            accept = '*.shp'
        elif _type == 'json' :
            accept = '*.json'
            
        self.wfu_text_file = FileChooser( 
            filter_pattern = accept,
            multiple=False)
        
        self.wdd_fid_attrib = Dropdown(
            placeholder='Fid Attribute',
            description='Fid Attribute:',
            disabled=False
        )
        
        self.wt_ext_fid_list = FileChooser(
            placeholder='External Fid List (Optional)',
            description='External Fid List:',
            disabled=False
        )
                
        def on_upload_change():
            
            # load the geodataframe and get the columns values
            gdf = gpd.read_file(self.wfu_text_file.selected)
            
            # get a list of columns in the geodataframe
            cols = list(gdf.columns)
            
            self.wdd_fid_attrib.options = cols
    
    
        self.wfu_text_file.register_callback(on_upload_change)
        
        super().__init__([self.wfu_text_file, self.wdd_fid_attrib, self.wt_ext_fid_list])

    def dump(self) -> dict :
        out_dict = {}
        
        out_dict["type"] = self.type
    
        if self.wfu_text_file.selected is not None :
            out_dict["parcelFile"] = self.wfu_text_file.selected
        else :
            if os.path.isfile(self.wfu_text_file.default) :
                out_dict["parcelFile"] = self.wfu_text_file.default    
            
        if self.wdd_fid_attrib.value is not None :
            out_dict["fidAttribute"] = self.wdd_fid_attrib.value
            
        if self.wt_ext_fid_list.selected is not None :
            out_dict["externalFid"] = self.wt_ext_fid_list.selected

        return out_dict
    
    def initialize(self, options : dict) :
        
        if "parcelFile" in options :
            try :
                full_path = options["parcelFile"].replace("\\","/")
                
                if os.path.isfile(full_path) :
                    base_path = full_path[:full_path.rfind("/")+1]
                    filename = full_path[full_path.rfind("/")+1:]
                    self.wfu_text_file.reset(path=base_path, filename = filename)
            except :
                print("Unable to set path")
                
        if "externalFid" in options :
            try :
                full_path = options["externalFid"].replace("\\","/")
                
                if os.path.isfile(full_path) :
                    base_path = full_path[:full_path.rfind("/")+1]
                    filename = full_path[full_path.rfind("/")+1:]
                    self.wt_ext_fid_list.reset(path=base_path, filename = filename)
            except :
                print("Unable to set path")
    
        if (self.wfu_text_file.selected is None) and \
           (os.path.isfile(self.wfu_text_file.default)) :
                # load the geodataframe and get the columns values
                gdf = gpd.read_file(self.wfu_text_file.default)
                
                # get a list of columns in the geodataframe
                cols = list(gdf.columns)
                
                self.wdd_fid_attrib.options = cols
    
        if ("fidAttribute" in options) and \
           (options["fidAttribute"] in self.wdd_fid_attrib.options) :
               
            self.wdd_fid_attrib.value = options["fidAttribute"]
