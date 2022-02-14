#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio, Csaba WIRNHARDT
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Sun Oct 31 10:41:24 2021

from ipywidgets import (Text, VBox, Dropdown, Password, Checkbox,
                        Button, HBox, HTML, Tab, Layout )


import config
import pandas as pd

from ipyfilechooser import FileChooser
import json
import os


class BaseDataReaderWidget(VBox):
    _type = "" 
    """
    Summary:
        Basic class defining the minimal interfaces for the data reader
        widgets
    """
    def __init__(self, dr_type = "", parent = None) :
        """
        Summary:
            Object constructor for the base_data_reader_widget.
            
        Arguments:
            signal_components - dictionary with the signals available for plotting.
            
        Returns :
            The newly created object
            
        Note :
            Currently, a data reader has the following syntax
            
    		{
    			"type": "rest_s2",
    			"signal": "outreach_bands",
    			"connection_options": {
                                    "ms" : "bewa",
                                    "year": 2020,
                                    "api_user": "...",
                                    "api_pass": "...", 
                                    "ptype": ""
                            }
    		}
            These are the available source types:
            'csv', 'dir_csv', 'rest_s2', 'rest_c6', 'rest_bs'
        """     
        self.type = dr_type
        self.parent = parent
        
        if self.parent is not None :
                try :
                    self.parent.set_title_from_widget(self)
                except :
                    print("Unable to set the Tab title.")        
        
        self.wt_signal = Text(
                description="Signal:",
                placeholder="Signal",
                disabled=False
            )
        
        def on_signal_change(change) :
            if self.parent is not None :
                try :
                    self.parent.set_title_from_widget(self)
                except :
                    print("Unable to set the Tab title.")
                    
        self.wt_signal.observe(on_signal_change, 'value')

        # Initialize the 
        super().__init__([HTML(value = f"<B>Data reader type: {self.type}</B>"),
                         self.wt_signal, 
                         HTML(value = "<B>Options :</B>")
                         ],layout=Layout(border='1px solid black'))
        
        self.options = []                    

    def add_options(self, options = None) :
        """
        Summary:
            Add options related to a specific data reader widget.
        
        Arguments:
            options - list of widgets representing the options specific to 
            the data reader
            
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
        out_dict["signal"] = self.wt_signal.value
        
        return out_dict

    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the reader and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the reader.            
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
    
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data reader widget using a dictionary, which needs to 
            have the same format as that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data reader
            widget

        Returns:
            Nothing.  
        """
        # Add the signal
        if ("signal" in options) :
            self.wt_signal.value = options["signal"]
                         
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
        self.children = [HTML(value = f"<B>Data reader type: {self.type}</B>"),
                         self.wt_signal, 
                         HTML(value = "<B>Options :</B>"),
                         *self.options]
        
class CsvDataReaderWidget(BaseDataReaderWidget):
    _type = "csv"
    
    """
    Summary:
        Widget containing CSV data reader widget
    """
    def __init__(self, parent = None):
        """
        Summary:
            Object constructor.
        
        Arguments:
            None
            
        Returns:
            Nothing.
        """
        super().__init__(CsvDataReaderWidget._type, parent)
        
        
        # Path name
        wfc_path = FileChooser(
                placeholder='path',
                description='path:',
                disabled=False
            )

        wdd_fid_attrib = Dropdown(
            placeholder='fid attribute',
            description='fid attribute:',
            disabled=False
        )
        
        wdd_date_attrib = Dropdown(
            value="",
            options=[""],
            placeholder='date attribute',
            description='date attribute:',
            disabled=False
        )
        
        def on_upload_change():
            # load the dataframe and get the columns values
            df = pd.read_csv(wfc_path.selected)
        
            # get a list of columns in the geodataframe
            cols = list(df.columns)
        
            wdd_fid_attrib.options = cols
            wdd_date_attrib.options = ["", *cols]

        wfc_path.register_callback(on_upload_change) 
        
        # Add specific options
        self.add_options([wfc_path, wdd_fid_attrib, wdd_date_attrib])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the reader and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the reader.            
        """
        out_dict = self.dump_header()
        
        # Note:
        # self.options = [wfc_path, wdd_fid_attrib, wdd_date_attrib]
        if self.options[0].selected is not None :
            out_dict["path"] = self.options[0].selected
        
        out_dict["fidAttribute"] = self.options[1].value
        
        if self.options[2].value != "" :
            out_dict["date_column"] = self.options[2].value
        
        return out_dict

    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data reader widget using a dictionary, which needs to 
            have the same format as that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data reader
            widget

        Returns:
            Nothing.  
        """
        # Add the signal
        if ("signal" in options) :
            self.wt_signal.value = options["signal"]
            
        if "path" in options :
            try :
                full_path = options["path"].replace("\\","/")
                
                if os.path.isfile(full_path) :
                    base_path = full_path[:full_path.rfind("/")+1]
                    filename = full_path[full_path.rfind("/")+1:]
                    self.options[0].reset(path=base_path, filename = filename)
            except :
                print("Invalid path")
                
        if (self.options[0].selected is None) and \
           (os.path.isfile(self.options[0].default)) :
                
            # load the data frame
            df = pd.read_csv(self.options[0].default)
    
            # get a list of columns in the geodataframe
            cols = list(df.columns)
    
            self.options[1].options = cols
            self.options[2].options = ["", *cols]
               
        if ("fidAttribute" in options) and (options["fidAttribute"] in self.options[1].options) :
            self.options[1].value = options["fidAttribute"]
            
        if ("date_column" in options) and (options["date_column"] in self.options[2].options) :
            self.options[2].value = options["fidAttribute"]


class DirCsvDataReaderWidget(BaseDataReaderWidget):
    _type = "dir_csv"
    
    """
    Summary:
        Widget for the dir_csv data reader widget
    """
    def __init__(self, parent = None):
        """
        Summary:
            Object constructor.
        
        Arguments:
            None
            
        Returns:
            Nothing.
        """
        super().__init__(DirCsvDataReaderWidget._type, parent)
        
        # Additional options
        
        # Path name
        wfc_path = FileChooser(
                placeholder='path',
                description='path:',
                disabled=False,
                
            )
        
        wfc_path.show_only_dirs = True

        wdd_fid_attrib = Dropdown(
            placeholder='fid attribute',
            description='fid attribute:',
            disabled=False
        )
        
        wdd_date_attrib = Dropdown(
            value="",
            options=[""],
            placeholder='date attribute',
            description='date attribute:',
            disabled=False
        )
        
        def on_upload_change():
            # firt check if wfc_path.selected is a directory
            if not os.path.isdir(wfc_path.selected) :
                return
            
            # list all csv file in dir 
            csv_files = [f for f in os.listdir(wfc_path.selected) if f.endswith('.csv')]
            
            # load the dataframe from the first csv file and get the columns values
            if len(csv_files) == 0 :
                return 
            
            df = pd.read_csv(wfc_path.selected + "/" + csv_files[0])
        
            # get a list of columns in the geodataframe
            cols = list(df.columns)
        
            wdd_fid_attrib.options = cols
            wdd_date_attrib.options = ["", *cols]

        wfc_path.register_callback(on_upload_change) 
        
        wt_suffixes = Text(
            placeholder='suffixes_to_col',
            description='suffixes_to_col:',
            disabled=False
            )
        
        wt_same_date = Text(
            placeholder='Same dates:',
            description='Same dates:',
            disabled=False
            )
        
        wt_suffix_sep = Text(
            placeholder='suffix_sep',
            description='suffix_sep:',
            disabled=False
            )
        
         # Add specific options
        self.add_options([wfc_path, wdd_fid_attrib, wdd_date_attrib,
                          wt_suffixes, wt_same_date, wt_suffix_sep])

    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the reader and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the reader.            
        """
        out_dict = self.dump_header()
        
        # Note:
        # self.options = [wfc_path, wdd_fid_attrib, wdd_date_attrib,
        #                 wt_suffixes, wt_same_date, wt_suffix_sep]
        if self.options[0].selected is not None :
            out_dict["path"] = self.options[0].selected
        
        out_dict["fidAttribute"] = self.options[1].value
        
        if self.options[2].value != "" :
            out_dict["date_column"] = self.options[1].value
        
        # wt_suffixes
        if self.options[3].value != "" :
            # convert the text into a list
            suf_list = self.options[3].value.split(",")
            suf_list = [value.strip() for value in suf_list]
            
            out_dict["suffixes_to_col"] = suf_list
        
        # wt_same_date
        if self.options[4].value != "" :
            # convert the text into a list
            date_list = self.options[4].value.split(",")
            date_list = [(value.strip().lower() == "true") for value in date_list]
            
            out_dict["same_dates"] = date_list
    
        # wt_same_date
        if self.options[5].value != "" :
            out_dict["suffix_sep"] = self.options[5].value
        
        return out_dict
        
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data reader widget using a dictionary, which needs to 
            have the same format as that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data reader
            widget

        Returns:
            Nothing.  
        """
        # Add the signal
        if ("signal" in options) :
            self.wt_signal.value = options["signal"]
            
        if "path" in options :
            try :
                full_path = options["path"].replace("\\","/")
                if os.path.isdir(full_path) :
                    self.options[0].reset(path=full_path)
            except :
                print("Invalid path")
                
        if ("fidAttribute" in options) and (options["fidAttribute"] in self.options[1].options) :
            self.options[1].value = options["fidAttribute"]
            
        if ("date_column" in options) and (options["date_column"] in self.options[2].options) :
            self.options[2].value = options["fidAttribute"]    
    
    	# wt_suffixes
        if "suffixes_to_col" in options :
            self.options[3].value = ", ".join(options["suffixes_to_col"]) 	 
                 
        # wt_same_date
        if "same_dates" in options :
            date_str = str(options["same_dates"]).lower()
            if date_str[0] == "[" :
            	date_str = date_str[1:]
            if date_str[-1] == "]" :
            	date_str = date_str[:-1]
            
            self.options[4].value = date_str

        # wt_same_date
        if "suffix_sep" in options :
            self.options[5].value = options["suffix_sep"]

class cloud_classification_widget(VBox) :
    
    def __init__(self) :
        # Default values [3,8,9,10,11]
        # Just a block of check boxes
        super().__init__([
            Checkbox(value=False, description='0 - No data',disabled=False),
            Checkbox(value=False, description='1 - Saturated or Defective',disabled=False),
            Checkbox(value=False, description='2 - Dark Area Pixels',disabled=False),
            Checkbox(value=True, description='3 - Cloud Shadows',disabled=False),
            Checkbox(value=False, description='4 - Vegetation',disabled=False),
            Checkbox(value=False, description='5 - Not Vegetated',disabled=False),
            Checkbox(value=False, description='6 - Water',disabled=False),
            Checkbox(value=False, description='7 - Unclassified',disabled=False),
            Checkbox(value=True, description='8 - Cloud Medium Probability',disabled=False),
            Checkbox(value=True, description='9 - Cloud High Probability',disabled=False),
            Checkbox(value=True, description='10 - Thin Cirrus',disabled=False),
            Checkbox(value=True, description='11 - Snow',disabled=False)
            ])
        
    def dump(self) -> dict :
        cloud_cat_list = []
        
        for ii, wd in enumerate(self.children) :
            if wd.value :
                cloud_cat_list.append(ii)
        
        return {"cloud_categories" : cloud_cat_list}
    
    def initialize(self, options : dict) :
        if "cloud_categories" in options :
            cloud_cat_list = options["cloud_categories"]
            
            for ii in cloud_cat_list :
                self.children[ii].value = True
                
class connection_widget(VBox) :
    
    def __init__(self) :
        
        # Add the required widgets
        self.wt_url = Text(
            placeholder='Add URL',
            description='API URL:',
            disabled=False
        )
        self.wt_user = Text(
            placeholder='Username',
            description='API User:',
            disabled=False
        )
        self.wt_pass = Password(
            placeholder='******',
            description='API Password:',
            disabled=False
        )
    
        self.wt_ms = Text(
            placeholder='Member State',
            description='Member State:',
            disabled=False
        )
        
        self.wdd_year = Dropdown(
            options = ['2020', '2019', '2018'],
            placeholder='Year',
            description='Year:',
            disabled=False
        )
        
        self.wdd_ptype = Dropdown(
            options = ['', 'm', 'g', 'b'],
            placeholder='Type',
            description='Type:',
            disabled=False
        )
        
        super().__init__([self.wt_url, self.wt_user, self.wt_pass, self.wt_ms, \
                         self.wdd_year, self.wdd_ptype])
        
    def dump(self) -> dict :
        
        out_dict = {}
        if self.wt_url.value != "" :
            out_dict["api_url"] = self.wt_url.value
            
        if self.wt_user.value != "" :
            out_dict["api_user"] = self.wt_user.value
            
        if self.wt_pass.value != "" :
            out_dict["api_pass"] = self.wt_pass.value
            
        if self.wt_ms != "" :
            out_dict["ms"] = self.wt_ms.value
            
        if self.wdd_year != "" :
            out_dict["year"] = self.wdd_year.value

        if self.wdd_ptype != "" :
            out_dict["ptype"] = self.wdd_ptype.value
            
        return out_dict
    
    def initialize(self, options : dict) :
    
        if "api_url" in options :
            self.wt_url.value = options["api_url"]
        
        if ("ptype" in options) and (options["ptype"] in self.wdd_ptype.options) :
            self.wdd_ptype.value = options["ptype"]
            
        if "ms" in options :
            self.wt_ms.value = options["ms"]
        
        if "api_pass" in options :
            self.wt_pass.value = options["api_pass"]
        
        if "api_user" in options :
            self.wt_user.value = options["api_user"]
        
        if ("year" in options) and (options["year"] in self.wdd_year.options) :
            self.wdd_year.value = options["year"]

            
class S2RestfulDataReaderWidget(BaseDataReaderWidget):
    _type = 'rest_s2' 
    """
    Summary:
        Widget containing Restful S2 data reader widget
    """
    
    def __init__(self, parent = None):
        """
        Summary:
            Object constructor.
        
        Arguments:
            None
            
        Returns:
            Nothing.
        """
        super().__init__(S2RestfulDataReaderWidget._type, parent)
        
        # Add options
        self.connection_opt = connection_widget()
        
        # Add cloud cover mask
        self.cloud_mask = cloud_classification_widget()
        
        self.add_options([HBox([self.connection_opt, 
                          VBox([HTML("<center><B>SCL Mask: </B></center>"), self.cloud_mask])])])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the reader and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the reader.            
        """
        out_dict = self.dump_header()
        
        # add the connection options
        out_dict["connection_options"] = self.connection_opt.dump()
        
        # eventually add the cloud mask option
        cloud_dict = self.cloud_mask.dump()
        if len(cloud_dict["cloud_categories"]) > 0 :
            out_dict["cloud_categories"] = cloud_dict["cloud_categories"]
            
        return out_dict
        
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data reader widget using a dictionary, which needs to 
            have the same format as that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data reader
            widget

        Returns:
            Nothing.  
        """
        # Add the signal
        if ("signal" in options) :
            self.wt_signal.value = options["signal"]
        
        if "connection_options" in options :
            self.connection_opt.initialize(options["connection_options"])
            
        if "cloud_categories" in options :
            self.cloud_mask.initialize(options)
                      
class C6RestfulDataReaderWidget(BaseDataReaderWidget) :
    _type = 'rest_c6'
    
    """
    Summary:
        Widget containing Restful COH6 data reader widget.
        It is essentially the same as the S2 widget
    """
    
    def __init__(self, parent = None):
        """
        Summary:
            Object constructor.
        
        Arguments:
            None
            
        Returns:
            Nothing.
        """
        super().__init__(C6RestfulDataReaderWidget._type, parent)
        
        # Add options
        self.connection_opt = connection_widget()
        
        self.add_options([self.connection_opt])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the reader and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the reader.            
        """
        out_dict = self.dump_header()
        
        # add the connection options
        out_dict["connection_options"] = self.connection_opt.dump()
        
        return out_dict
        
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data reader widget using a dictionary, which needs to 
            have the same format as that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data reader
            widget

        Returns:
            Nothing.  
        """
        # Add the signal
        if ("signal" in options) :
            self.wt_signal.value = options["signal"]
        
        if "connection_options" in options :
            self.connection_opt.initialize(options["connection_options"])

class BsRestfulDataReaderWidget(BaseDataReaderWidget) :
    _type = 'rest_bs'
    
    """
    Summary:
        Widget containing Restful back scattering data reader widget.
        It is essentially the same as the S2 widget
    """
    
    def __init__(self, parent = None):
        """
        Summary:
            Object constructor.
        
        Arguments:
            None
            
        Returns:
            Nothing.
        """
        super().__init__(BsRestfulDataReaderWidget._type, parent)
        
        # Add options
        self.connection_opt = connection_widget()
        
        self.add_options([self.connection_opt])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the reader and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the reader.            
        """
        out_dict = self.dump_header()
        
        # add the connection options
        out_dict["connection_options"] = self.connection_opt.dump()
        
        return out_dict
        
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data reader widget using a dictionary, which needs to 
            have the same format as that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data reader
            widget

        Returns:
            Nothing.  
        """
        # Add the signal
        if ("signal" in options) :
            self.wt_signal.value = options["signal"]
        
        if "connection_options" in options :
            self.connection_opt.initialize(options["connection_options"])

class DataReaderTab(VBox) :
    
    dt_types_descr = {'csv' : 'CSV file',
                      'dir_csv' : 'Directory with CSV files',
                      'rest_s2' : 'S2 from RESTFul server', 
                      'rest_c6' : 'S1 coherence from RESTFul server',
                      'rest_bs' : 'S1 backscatter from RESTFul server'} 
    
    """
    Summary:
        Widget containing several data reader widgets        
    """
    def __init__(self)  :      
        """
        Summary:
            Object constructor.
        
        Arguments:
            None
            
        Returns:
            Nothing.
        """
        self.count = 0
        # List of data readers
        self.data_readers = []
        
        self.wt_data_readers = Tab()

        # Add and remove buttons
        self.wb_add = Button(
            description='Add',
            tooltip='Add a new data source',
            disabled=False,
            icon='Add'
        )

        supported_types = [x._type for x in BaseDataReaderWidget.__subclasses__()]
        type_descr = [DataReaderTab.dt_types_descr[x] for x in supported_types]
        
        self.wdd_types = Dropdown(
            options=type_descr,
            description='Data source type:',
            disabled=False
        )
        
        self.wb_remove = Button(
                        description='Remove',
                        disabled=False,
                        tooltip='Remove the last data source',
                        icon='remove'
        )
        
        @self.wb_add.on_click
        def wb_add_on_click(b):
            new_w = None
            ind = type_descr.index(self.wdd_types.value)

            new_w = BaseDataReaderWidget.__subclasses__()[ind](self)
                                                
            if new_w is not None :
                self.data_readers.append(new_w)
                self.wt_data_readers.children = self.data_readers
                self.wt_data_readers.set_title(self.count, new_w.type)
                self.count += 1            
            
        @self.wb_remove.on_click
        def wd_remove_on_click(b):
            
            if len(self.data_readers) > 0 :
                self.data_readers.pop()
                self.count -= 1
                
            self.wt_data_readers.children = self.data_readers
         
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

        # the superclass of this class is a VBox, so we use the constructor of the VBox here
        super().__init__([self.wt_data_readers, HBox([self.wb_add, self.wdd_types]),
                          self.wb_remove, self.wb_save, self.whb_load])
                    
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the data reader tab and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the data readers.  
        """
        tab_list = []
        
        # Build the list of data readers
        for data_reader in self.data_readers :
            tab_list.append(data_reader.dump())
            
        out_dict = {"dataReaders" : tab_list}
        
        return out_dict
    
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the data reader tab using a dictionary, which needs to 
            have the same format as that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the data reader tab

        Returns:
            Nothing.  
        """
        
        if ("dataReaders" not in options):
            return
        
        if "dataReaders" in options :
            # get the tab list
            tab_list = options["dataReaders"]
            
        
        # delete all the data readers
        self.data_readers = []
        self.count = 0
        
        # supported types 
        supported_types = [x._type for x in BaseDataReaderWidget.__subclasses__()]
        
        for tab in tab_list :
            if ("type" in tab) and (tab["type"] in supported_types) : 
                ind = supported_types.index(tab["type"])
                data_reader = BaseDataReaderWidget.__subclasses__()[ind](self)
                data_reader.initialize(tab)
                self.data_readers.append(data_reader)
            
        self.wt_data_readers.children = self.data_readers
        for ii, wmd in enumerate(self.data_readers) :
            self.wt_data_readers.set_title(ii, wmd.wt_signal.value)
            
        self.count = len(self.data_readers)
        
        self.children = [self.wt_data_readers, HBox([self.wb_add, self.wdd_types]), 
                          self.wb_remove, self.wb_save, self.whb_load]
        
    def set_title(self, tab_index : int , title : str) :
        self.wt_data_readers.set_title(tab_index, title)
        
    def set_title_from_widget(self, child_tab) :
        
        # check if  the child_tab is a real children of the widget
        if child_tab not in self.data_readers :
            return
        
        index = self.data_readers.index(child_tab)
        title = child_tab.wt_signal.value
        
        self.set_title(index, title)
