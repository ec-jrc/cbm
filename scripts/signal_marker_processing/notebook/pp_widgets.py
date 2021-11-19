#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (Text, VBox, Dropdown, SelectMultiple,
                        Button, HBox, HTML, Tab, Layout, BoundedIntText,
                        BoundedFloatText, Checkbox, FloatText )

import config
from ipyfilechooser import FileChooser
import json

class SelectMultipleOrdered(SelectMultiple) :
    """
    Summary:
        Extension of the SelectMultiple widget which takes into account
        the selection order
    """
    
    def __init__(self, **kwargs) :
        """
        Object constructor.
        """
        super().__init__(**kwargs)
        
        # Now build the infrastructure to keep track of the selection order
        self.ordered_value = []
        
        def on_change(change):
            if change['type'] == 'change' and change['name'] == 'value':
                for elem in change['new']:
                    if elem not in self.ordered_value:
                        self.ordered_value.append(elem)
                for elem in self.ordered_value:
                    if elem not in change['new']:
                        self.ordered_value.remove(elem)

        self.observe(on_change)
        
        
class base_processor_widget(VBox) :
    """
        Summary:
            
    """
    def __init__(self, signal_components : dict, _type = "") :
        """
            Summary:
                
        """        
        self.type = _type
        
        # Create the list of signals available
        # Include an empty option
        self.signals = ["", *list(signal_components)]
        
        self.wsm_signals = SelectMultiple(
                options=self.signals,
                value=[""],
                description="Signals:",
                placeholder="Signals",
                disabled=False
            )
        
        # Components
        self.components = signal_components
        components = [""]
        for key in signal_components :
            components = [*components, *signal_components[key]]
        
        self.wsm_components = SelectMultipleOrdered(
                options=components,
                value=[""],
                description="Components:",
                placeholder="Components",
                disabled=False
            )
        
        def on_signal_change(change) :
            components = [""]
                
            if "" in self.wsm_signals.value :
                for key in self.components :
                    components = [*components, *self.components[key]]
            else :
                for key in self.wsm_signals.value :
                    components = [*components, *self.components[key]]
            
            self.wsm_components.options = components
            
        self.wsm_signals.observe(on_signal_change, 'value')
        
        super().__init__([HTML(value = f"<B>Processor type: {self.type}</B>"),
                         HBox([self.wsm_signals, self.wsm_components]),
                         HTML(value = "<B>Options :</B>")
                         ],layout=Layout(border='1px solid black'))
        
        self.options = []
    
    def add_options(self, options = None) :
        """
        Summary:
            Add options related to a specific processor type.
        
        Arguments:
            options - list of widgets representing the options specific to 
            the preprocessor
            
        Returns:
            Nothing.
        """
        
        if options is not None :
            self.children = [*self.children, *options]
            
            self.options = options
    
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the preprocessor and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the preprocessor.            
        """
        out_dict = {"type" : self.type}
        
        # Add the signal
        signals = list(self.children[1].children[0].value)
        
        # Check if there is at list one signal
        if (len(signals) == 1) and (signals[0] != "") :
            out_dict["signals"] = signals
            
        # Add the components
        components = list(self.wsm_components.ordered_value)
        
        # Check if there is at list one component
        if (len(components) >= 1) and (components[0] != "") :
            out_dict["components"] = components
            
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
    
    def get_signal_components(self) -> dict :
       """
       Summary:
           Return the dictionary with signal and components at the output of 
           processor.         
       """        
       
       out_dict = {}
       if "" in self.wsm_signals.value :
           signals = list(self.components.keys())
       else:
           signals = self.wsm_signals.value
       
       for signal in signals :
           if "" in self.wsm_components.value :
               out_dict[signal] = self.components[signal]
           else:
               out_dict[signal] = list(set(self.components[signal]) & \
                                       set(self.wsm_components.value))
                   
       return out_dict
   
    def initialize(self, options) :
        """
        Summary:
            Initialize the processor using a dictionary, which needs to 
            have the same format has that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the processor

        Returns:
            Nothing.  
        """        
        # Add the signal
        if "signals" in options :
            self.wsm_signals.value = options["signals"]
        else :
            self.wsm_signals.value = tuple([""])
            
        # Add the components
        if "components" in options :
            compo_list = []
            for component in options["components"] :
                if component in self.wsm_components.options :
                    compo_list.append(component)
            
            self.wsm_components.value = compo_list
            
        else :
            self.wsm_components.value = tuple([""])
                    
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
                         HBox([self.wsm_signals, self.wsm_components]),
                         HTML(value = "<B>Options :</B>"),
                         *self.options]
        
class data_filter_widget(base_processor_widget) :
    """
    Summary:
       Widget for the data filter processor.         
    """ 
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "filter")
        
        # Add specific options
        self.wdd_by = Dropdown(
            description = "by",
            options = self.wsm_components.options,
            disabled = False)
        
        # Modify the on change function for the signal
        def on_signal_change(change) :
            components = [""]
                
            if "" in self.wsm_signals.value :
                for key in self.components :
                    components = [*components, *self.components[key]]
            else :
                for key in self.wsm_signals.value :
                    components = [*components, *self.components[key]]
            
            self.wsm_components.options = components
            self.wdd_by.options = components
            
        self.wsm_signals.observe(on_signal_change, 'value')    
        
        wdd_criterion = Dropdown(
            options = ['equal', 'greater','greater_equal','lower','lower_equal', \
                       'not_equal'],
            description = "criterion:",
            disabled = False)
            
        wft_threshold = FloatText(
            value = 0,
            description = "threshold:",
            disabled = False)
        
        self.add_options([self.wdd_by, wdd_criterion, wft_threshold])

class data_merger_widget(base_processor_widget) :
    """
    Summary:
       Widget for the splitter processor.         
    """ 
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "merge")
        
    def get_signal_components(self) -> dict :
       """
       Summary:
           Return the dictionary with signal and components at the output of 
           processor.         
       """
       # Check the signal selected
       if "" in self.wsm_signals.value :
           signals = list(self.components.keys()) 
       else :
           signals = self.wsm_signals.value
           
       if len(signals) < 2 :
            return {}
        
       # keep only the first two signals 
       signals = signals[:2]

       signal_name = signals[0] + '_' + signals[1]

       components_0 = [signals[0] + '_' + compo for compo in self.components[signals[0]]]
       components_1 = [signals[1] + '_' + compo for compo in self.components[signals[1]]]
       
       out_dic = {signal_name : [*components_0, *components_1]}
       
       return out_dic
        
class data_function_widget(base_processor_widget) :
    """
    Summary:
       Widget for the data function processor.         
    """ 
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        super().__init__(signal_components, "math_function")
        
        # Now add additional options
        wt_function = Text(
            description="function:",
            disabled= False)
        
        self.add_options([wt_function])
        

class lut_strector_widget(base_processor_widget) :
    """
    Summary:
       Widget for the lut_strector processor.         
    """ 
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "lut_strect")
        
        # Add specific options
        # "min_val": [1200, 800, 150],
		# "max_val": [5700, 4100, 2800]
        wt_minval = Text(
            description="min_val:",
            value = "1200, 800, 150",
			disabled = False)
        
        wt_maxval = Text(
            description="max_val:",
            value = "5700, 4100, 2800",
			disabled = False)
            
        self.add_options([wt_minval, wt_maxval])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the preprocessor and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the preprocessor.            
        """
        out_dict = {"type" : self.type}
        
        # Add the signal
        signals = list(self.children[1].children[0].value)
        
        # Check if there is at list one signal
        if (len(signals) == 1) and (signals[0] != "") :
            out_dict["signals"] = signals
            
        # Add the components
        components = list(self.children[1].children[1].ordered_value)
        
        # Check if there is at list one component
        if (len(components) >= 1) and (components[0] != "") :
            out_dict["components"] = components
            
        # Now add the options, if present
        for wd in self.options :
            key = wd.description
            
            # Eventually remove the last colon
            if key[-1] == ":" :
                key = key[:-1]
            
            # value should be string
            value = wd.value.split(",")
        
            # strip white spaces
            value = [int(name.strip()) for name in value]
                            
            out_dict[key] = value
        
        return out_dict
    
    def initialize(self, options) :
        """
        Summary:
            Initialize the processor using a dictionary, which needs to 
            have the same format has that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the processor

        Returns:
            Nothing.  
        """        
        # Add the signal
        if "signals" in options :
            self.wsm_signals.value = options["signals"]
        else :
            self.wsm_signals.value = tuple([""])
            
        # Add the components
        if "components" in options :
            self.wsm_components.value = list(set(options["components"]) & \
                                             set(self.wsm_components.options))
        else :
            self.wsm_components.value = tuple([""])
                    
        # Now add specific options, if present
        for wd in self.options :
            key = wd.description
            
            # Eventually remove the last colon
            if key[-1] == ":" :
                key = key[:-1]
        
            if key in options :
                if isinstance(wd, Text) and isinstance(options[key], list) :
                    wd.value = ", ".join([str(a) for a in options[key]]) 
                else :
                    wd.value = options[key]
                    
        # Set the children of the widget
        self.children = [HTML(value = f"<B>Processor type: {self.type}</B>"),
                         HBox([self.wsm_signals, self.wsm_components]),
                         HTML(value = "<B>Options :</B>"),
                         *self.options]

class red_nir_swir_processor_widget(base_processor_widget) :
    """
    Summary:
       Widget for the red_nir_swir processor.         
    """ 
    
    # classes considered in this specific implementation    
    class_labels = ['cloudy', 'hazy', 'shady', 'maintained', 'vegetated (O)',
                        'vegetated (Y)', 'vegetated (D)', 'other']
    
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        
            This is a quite specific processor and has a dedicated constructor.
        """
        
        self.type = "band_filter"
        
        # Create the list of signals available
        # Include an empty option
        self.signals = list(signal_components.keys())
        
        # In this case, only one signal can be selected
        self.wdd_signals = Dropdown(
                options=self.signals,
                description="Signals:",
                placeholder="Signals",
                disabled=False
            )
        
        self.components = signal_components
        
        components = signal_components[self.wdd_signals.value]
        self.wdd_nir = Dropdown(
            options = components,
            description="NIR:",
            disabled=False
        )

        self.wdd_swir = Dropdown(
            options=components,
            description="SWIR:",
            disabled=False
        )
        
        self.wdd_red = Dropdown(
            options=components,
            description="RED:",
            disabled=False
        )
 
        self.nsr_bar = HBox([self.wdd_nir, self.wdd_swir, self.wdd_red])    

        self.wsm_components = SelectMultiple(
                options=["", *components],
                value=[""],
                description="Components:",
                placeholder="Components",
                disabled=False
            )
        
        def on_signal_change(change) :
            components = self.components[self.wdd_signals.value]
            self.wdd_nir.options = components
            self.wdd_swir.options = components
            self.wdd_red.options = components
            
            self.wsm_components.options = ["", *components]
            
        self.wdd_signals.observe(on_signal_change, 'value')

        
        super(type(self).__bases__[0], self).__init__(
                         [HTML(value = f"<B>Processor type: {self.type}</B>"),
                         HBox([self.wdd_signals, self.wsm_components]),
                         self.nsr_bar,
                         HTML(value = "<B>Options :</B>")
                         ],layout=Layout(border='1px solid black'))
        
        self.options = []
        
        # Add specific options
        wsm_cat = SelectMultiple(
            description="excluded_categories:",
            options=red_nir_swir_processor_widget.class_labels,
            disabled=False)
        
        # "min_val": [1200, 800, 150],
		# "max_val": [5700, 4100, 2800]
#         wt_minval = Text(
#             description="min_val:",
#             value = "1200, 800, 150",
# 			disabled = False)
        
#         wt_maxval = Text(
#             description="max_val:",
#             value = "5700, 4100, 2800",
# 			disabled = False)
        
#         wfc_trainingfile = FileChooser(
#             description = "training_file:",
#             disabled = False
#         )
        
        # self.add_options([wsm_cat, wt_minval, wt_maxval, wfc_trainingfile])
        self.add_options([wsm_cat])
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictionary describing the preprocessor and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the preprocessor.            
        """
        out_dict = {"type" : self.type}
        
        # Add the signal
        signals = [self.wdd_signals.value]
        
        out_dict["signals"] = signals
            
        # Add the components
        components = [self.wdd_nir.value, self.wdd_swir.value, self.wdd_red.value]
        
        if "" in self.wsm_components.value :
            additional_components = self.wsm_components.options[1:]
        else :
            additional_components = self.wsm_components.value

        for compo in additional_components :
            if compo not in components :
                components.append(compo)
            
        out_dict["components"] = components
            
        # Now add the options
        # wsm_cat - "excluded_categories:"
        out_dict["excluded_categories"] = self.options[0].value
                
        return out_dict
    
    def get_signal_components(self) -> dict :
       """
       Summary:
           Return the dictionary with signal and components at the output of 
           processor.         
       """
       # Assume that all three output components will be provided
       out_names = ["filt_compo","filtered_b08_b11_b04","band_classes"]
       
       if "" in self.wsm_components.value :
            filt_compo = list(self.wsm_components.options[1:])
       else :
            filt_compo = list(self.wsm_components.value)
       
       nsr_components = [self.wdd_nir.value, self.wdd_swir.value, self.wdd_red.value]
       
       out_dict = {out_names[0] : filt_compo,
                   out_names[1] : nsr_components,
                   out_names[2] : ["classes"]}
       
       return out_dict
   
    def initialize(self, options) :
        """
        Summary:
            Initialize the processor line using a dictionary, which needs to 
            have the same format has that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the processing tab
        
        Returns:
            Nothing.  
        """        
        # Add the signal
        if "signals" in options :
            self.wdd_signals.value = options["signals"][0]
            
        # Add the components
        if "components" in options :
            components = options["components"]
            
            if len(components) > 3 :
                self.wdd_nir.value = components[0] 
                self.wdd_swir.value = components[1] 
                self.wdd_red.value = components[2]
                self.wsm_components.value = components[3:]
        
        if "excluded_categories" in options :
            self.options[0].value = options["excluded_categories"]
                    
        # Set the children of the widget
        self.children = [HTML(value = f"<B>Processor type: {self.type}</B>"),
                         HBox([self.wdd_signals, self.wsm_components]),
                         self.nsr_bar,
                         HTML(value = "<B>Options :</B>"),
                         self.options[0]]

class split_widget(base_processor_widget) :
    """
    Summary:
       Widget for the splitter processor.         
    """ 
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "split")
        
        # Add specific options
        split_components = []
        if (len(self.wsm_signals.value) == 1) and (self.wsm_signals.value[0] == "") :
            signals = list(self.components.keys())
        else :
            signals = list(self.wsm_signals.value)
            
        if "" in signals :
            signals.remove("")
        
        for signal in signals :
            for component in self.components[signal] :
                if component not in self.wsm_components.value :
                    split_components.append(component)
            
        self.wdd_by = Dropdown(
                options=split_components,
                placeholder='by',
                description='by:',
                disabled=False
            )
        
        self.wt_by_values = Text(
                placeholder='Values',
                description='Values:',
                disabled=False
            )
        
        
        def on_signal_component_change(change) :
            # Add specific options
            split_components = []
            if (len(self.wsm_signals.value) == 1) and (self.wsm_signals.value[0] == "") :
                signals = list(self.components.keys())
            else :
                signals = list(self.wsm_signals.value)
                
            if "" in signals :
                signals.remove("")
            
            for signal in signals :
                for component in self.components[signal] :
                    if component not in self.wsm_components.value :
                        split_components.append(component)
            
            self.wdd_by.options = split_components
            
        self.wsm_signals.observe(on_signal_component_change, 'value')
        self.wsm_components.observe(on_signal_component_change, 'value')        
        
        self.add_options([self.wdd_by, self.wt_by_values])

    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the preprocessor and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the preprocessor.            
        """
        wd = self.options.pop() 
        out_dict = super().dump()
        self.options.append(wd)

        return out_dict
    
    def get_signal_components(self) -> dict :
       """
       Summary:
           Return the dictionary with signal and components at the output of 
           processor.         
       """        
       
       out_dict = {}
       if "" in self.wsm_signals.value :
           signals = list(self.components.keys())
       else:
           signals = self.wsm_signals.value
       
       if self.wt_by_values.value == "" :
           split_values = ["1", "2"]
       else :    
           split_values = self.wt_by_values.value.split(",")
           split_values = [value.strip() for value in split_values]
                
       
       for signal in signals :
           if "" in self.wsm_components.value :
               components = self.components[signal]
           else:
               components = list(set(self.components[signal]) & \
                                 set(self.wsm_components.value))
                   
           if self.wdd_by.value in components :
               components.remove(self.wdd_by_value)
               
           for values in split_values :
               out_dict[signal + "_" + values] = components
                   
       return out_dict
     

class interpolator_widget(base_processor_widget) :
    """
    Summary:
       Widget for the interpolator widget.         
    """
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "interp")
        
        wdd_method = Dropdown(
            options=["linear", "nearest"],
            description="method:",
            disabled=False
            )
        
        wit_sampling_int = BoundedIntText(
            value = 1,
            min = 0,
            step = 1,
            description="Ts:"
        )
        
        self.add_options([wdd_method, wit_sampling_int])
    
    def get_signal_components(self) -> dict :
       """
       Summary:
           Return the dictionary with signal and components at the output of 
           processor.         
       """
       
       if "" in self.wsm_signals.value :
           signals = list(self.components.keys())
       else:
           signals = self.wsm_signals.value
           
       out_components = []
       
       for signal in signals :
           if "" in self.wsm_components.value :
               components = self.components[signal]
           else:
               components = list(set(self.components[signal]) & \
                                 set(self.wsm_components.value))
                   
           for compo in components :
               if len(signals) == 1 :
                   out_components.append(compo)
               else :
                   out_components.append(signal + '_' + compo)
               
       out_dict = {"lininterp" : out_components}
        
       return out_dict
       
       
class butterworth_widget(base_processor_widget) :
    """
    Summary:
       Widget for the butterworth_smoother.         
    """
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "butter_smoother")
        
        wbft_fc = BoundedFloatText(
            description = "fc:",
            value = 0.05,
            min = 0,
            max = 0.5,
            step = 0.01,
            disabled = False
            )
        
        self.add_options([wbft_fc])
        
class norm_widget(base_processor_widget) :
    """
    Summary:
       Widget for the norm widget.         
    """
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "norm")
        
        wcb_normalize = Checkbox(
            value=False,
            description = "normalize:",
            disabled = False
            )
        
        self.add_options([wcb_normalize])
        
    def get_signal_components(self) -> dict :
       """
       Summary:
           Return the dictionary with signal and components at the output of 
           processor.         
       """        
       
       out_dict = {}
       if "" in self.wsm_signals.value :
           signals = list(self.components.keys())
       else:
           signals = self.wsm_signals.value
       
       for signal in signals :
           out_dict[signal] = ["norm"]
                   
       return out_dict
        
class all_pass_widget(base_processor_widget) :
    """
    Summary:
       Widget for the all_pass processor.         
    """ 
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "all_pass")
    
class index_adder_widget(base_processor_widget) :
    """
    Summary:
       Widget for the index_adder processor.         
    """ 
    def __init__(self, signal_components : dict) :
        """
            Summary:
                Object constructor.                
        """
        
        super().__init__(signal_components, "index_adder")
        
        # Add specific options
        self.wt_as = Text(
            placeholder='as',
            description='as:',
            disabled=False
        )
        
        function_list = ["diff_div_by_sum"]
        wdd_function = Dropdown(
                options=function_list,
                description="function:",
                placeholder="function",
                disabled=False
            )
        
        self.add_options([self.wt_as, wdd_function])

    def get_signal_components(self) -> dict :
       """
       Summary:
           Return the dictionary with signal and components at the output of 
           processor.         
       """        
       
       out_dict = {}
       if "" in self.wsm_signals.value :
           signals = list(self.components.keys())
       else:
           signals = self.wsm_signals.value
       
       for signal in signals :
           out_dict[signal] = [*self.components[signal], self.wt_as.value]
                   
       return out_dict
        
class processing_line(VBox) :
    """
    Summary:
            
    """
    
    # List of processors currently supported
    pro_supported = ["all_pass", "band_filter", "butter_smoother", "filter", "lut_strect", \
                     "index_adder", "interp", "math_function", "merge", "norm",\
                     "split"]
    
    
    def __init__(self, signal_components : dict, parent = None)  :        
        """
        Summary:
            Object constructor for the processing line.
        """
        
        self.parent = parent
        
        self.signal_components = signal_components
        
        # list of processor widgets
        self.processor_list = []
        
        # Now initialize the widget
        wh_title = HTML(value = "<B>Processing Line</B>")
        
        self.wt_outname = Text(
                placeholder='Output names',
                description='Output names:',
                disabled=False
            )
        
        def on_outname_change(change) :
            if self.parent is not None :
                try :
                    self.parent.set_title_from_widget(self)
                except :
                    print("Unable to set the Tab title.")
                    
        self.wt_outname.observe(on_outname_change, 'value')
        
        self.wb_add = Button(
            description='Add',
            disabled=False,
            icon='Add'
        )
        
        self.wdd_types = Dropdown(
                options = processing_line.pro_supported,
                disabled = False
            ) 
    
        self.wb_remove = Button(
                        description='Remove',
                        disabled=False,
                        icon='Remove'
                    )
    
        @self.wb_add.on_click
        def wb_add_on_click(b):
        
            # Add a new processor as input
            if len(self.processor_list) == 0 :
                input_signals = self.signal_components
            else :
                input_signals = self.processor_list[-1].get_signal_components()
            
            new_w = None
            if self.wdd_types.value == "all_pass" :
                new_w = all_pass_widget(input_signals)
                
            elif self.wdd_types.value == "index_adder" :
                new_w = index_adder_widget(input_signals)
                
            elif self.wdd_types.value == "split" :
                new_w = split_widget(input_signals)
                
            elif self.wdd_types.value == "interp" :
                new_w = interpolator_widget(input_signals)
                
            elif self.wdd_types.value == "butter_smoother" :
                new_w = butterworth_widget(input_signals)
                
            elif self.wdd_types.value == "norm" :
                new_w = norm_widget(input_signals)
                
            elif self.wdd_types.value == "filter" :
                new_w = data_filter_widget(input_signals)
                
            elif self.wdd_types.value == "merge" :
                new_w = data_merger_widget(input_signals)
            
            elif self.wdd_types.value == "math_function" :
                new_w = data_function_widget(input_signals)
            
            elif self.wdd_types.value == "lut_strect" :
                new_w = lut_strector_widget(input_signals)
                
            elif self.wdd_types.value == "band_filter" :
                new_w = red_nir_swir_processor_widget(input_signals)
                
            if new_w is not None :
                self.processor_list.append(new_w)
                
            self.children = [wh_title, self.wt_outname, *self.processor_list, \
                             HBox([self.wb_add, self.wdd_types]), \
                             self.wb_remove]
            
        @self.wb_remove.on_click
        def wd_remove_on_click(b):
            
            if len(self.processor_list) > 0 :
                self.processor_list.pop()
                
                self.children = [wh_title, self.wt_outname, *self.processor_list, \
                                 HBox([self.wb_add, self.wdd_types]), \
                                 self.wb_remove]
            
        super().__init__([wh_title, self.wt_outname, *self.processor_list, \
                          HBox([self.wb_add, self.wdd_types]), self.wb_remove])
    
    def get_outnames(self) :
        return self.wt_outname.value.replace(",","/")
    
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the processor line and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the preprocessor.            
        """
        # get the output names
        outnames = self.wt_outname.value.split(",")
        
        # strip white spaces
        outnames = [name.strip() for name in outnames]
        
        # build the list of processors
        processor_list = []
        for wd in self.processor_list :
            processor_list.append(wd.dump())
            
        # Finally build the output database
        outdic = {"outnames" : outnames,
                  "processors" : processor_list}
        
        return outdic

    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the processor line using a dictionary, which needs to 
            have the same format has that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the processing tab

        Returns:
            Nothing.  
        """
        
        # get the output names
        if "outnames" in options :
            outnames = ", ".join(options["outnames"])
            
            self.wt_outname.value = outnames
        
        # Now add the preprocessors
        self.processor_list = []
        
        for prepro in options["processors"] :
            
            # Add a new processor as input
            if len(self.processor_list) == 0 :
                input_signals = self.signal_components
            else :
                input_signals = self.processor_list[-1].get_signal_components()
            
            new_w = None
            if prepro["type"] == "all_pass" :
                new_w = all_pass_widget(input_signals)
                
            elif prepro["type"] == "index_adder" :
                new_w = index_adder_widget(input_signals)
                
            elif prepro["type"] == "split" :
                new_w = split_widget(input_signals)
            
            elif prepro["type"] == "interp" :
                new_w = interpolator_widget(input_signals)
                
            elif prepro["type"] == "butter_smoother" :
                new_w = butterworth_widget(input_signals)
                
            elif prepro["type"] == "norm" :
                new_w = norm_widget(input_signals)
            
            elif prepro["type"] == "filter" :
                new_w = data_filter_widget(input_signals)

            elif prepro["type"] == "merge" :
                new_w = data_merger_widget(input_signals)
                
            elif prepro["type"] == "math_function" :
                new_w = data_function_widget(input_signals)

            elif prepro["type"] == "lut_strect" :
                new_w = lut_strector_widget(input_signals)
                
            elif prepro["type"] == "band_filter" :
                new_w = red_nir_swir_processor_widget(input_signals)
                
            if new_w is not None :
                new_w.initialize(prepro)
                self.processor_list.append(new_w)
                
            wh_title = HTML(value = "<B>Processing Line</B>")
            self.children = [wh_title, self.wt_outname, *self.processor_list, \
                             HBox([self.wb_add, self.wdd_types]), \
                             self.wb_remove]
                
    def get_signal_components(self) -> dict :
        """
        Summary:
            Return the dictionary with signal and components at the output of 
            processing tab.         
        """
        # get the output names
        outnames = self.wt_outname.value.split(",")
        
        # strip white spaces
        outnames = [name.strip() for name in outnames]

        # if there are no processors, return an empty dictionary
        if len(self.processor_list) == 0 :
            return {}
        
        # get the signals from the last processor in the list
        signal_components = self.processor_list[-1].get_signal_components()

        outdic = {}
    
        for ii, signal in enumerate(signal_components.keys()) :
            
            if ii >= len(outnames) :
                break
            else :
                outdic[outnames[ii]] = signal_components[signal]        
            
        return outdic

class processing_tab(VBox) :
    """
    Summary:
            
    """
    def __init__(self, signal_components : dict)  :      
        
        # Tab counter
        self.tab_counter = 0

        
        self.signal_components = signal_components
        
        # List of processing lines
        self.pro_lines = [processing_line(signal_components, self)]
        
        self.wt_pro_lines = Tab(self.pro_lines)
        self.set_title(self.tab_counter, f"Pro Line {self.tab_counter}")
        self.tab_counter += 1        
        
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
            # Append a new processing line tab
            self.pro_lines.append(processing_line({**signal_components, \
                                                   **(self.get_signal_components())},
                                                  self))
            
            self.wt_pro_lines.children = self.pro_lines
            self.set_title(self.tab_counter, f"Pro Line {self.tab_counter}")
            self.tab_counter += 1    
        
        @self.wb_remove.on_click
        def wd_remove_on_click(b):
            
            if len(self.pro_lines) > 1 :
                self.pro_lines.pop()
                self.tab_counter -= 1    
            else :
                # Empty tab
                self.pro_lines = [processing_line(signal_components)]
                
            self.wt_pro_lines.children = self.pro_lines
         
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
            
        super().__init__([self.wt_pro_lines, HBox([self.wb_add, self.wb_remove]),\
                          self.wb_save, self.whb_load])
   
    
    def set_title(self, tab_index : int , title : str) :
        self.wt_pro_lines.set_title(tab_index, title)
        
    def set_title_from_widget(self, child_line : processing_line) :
        
        # check if  the child_line is a real children of the widget
        if child_line not in self.pro_lines :
            return
        
        index = self.pro_lines.index(child_line)
        title = child_line.get_outnames()
        
        self.set_title(index, title)
        
    def dump(self) -> dict :
        """
        Summary:
            Build and return a dictiory descibing the processor tab and its
            options.
        
        Arguments:
            None.

        Returns:
            Dictionary describing the preprocessor.  
        """
        tab_list = []
        
        # Build the list of processing lines
        for line in self.pro_lines :
            tab_list.append(line.dump())
            
        out_dict = {"pre-processors" : tab_list}
        
        return out_dict
    
    def initialize(self, options : dict ) :
        """
        Summary:
            Initialize the processor tab using a dictionary, which needs to 
            have the same format has that produced by the dump function.
        
        Arguments:
            options - dictionary with the options to initialize the processing tab

        Returns:
            Nothing.  
        """
        
        if "pre-processors" not in options :
            return
        
        # get the tab list
        tab_list = options["pre-processors"]
        
        # delete all the processing lines
        self.pro_lines = []
        names = []
        
        for tab in tab_list :
            pro_line = processing_line({**self.signal_components, 
                                        **self.get_signal_components()},
                                       self)
            pro_line.initialize(tab)
            self.pro_lines.append(pro_line)
            names.append("/".join(tab["outnames"]))
            
        self.wt_pro_lines.children = self.pro_lines
                
        self.children = [self.wt_pro_lines, HBox([self.wb_add, self.wb_remove]),\
                          self.wb_save, self.whb_load]
        
        [self.set_title(i, title) for i, title in enumerate(names)]
        
        self.tab_counter = len(tab_list)
        
    def get_signal_components(self) -> dict :
        """
        Summary:
            Return the dictionary with signal and components at the output of 
            processing tab.         
        """
        out_dict = {}
        
        for pro_line in self.pro_lines :
            out_dict = {**out_dict, **(pro_line.get_signal_components())}
            
        return out_dict