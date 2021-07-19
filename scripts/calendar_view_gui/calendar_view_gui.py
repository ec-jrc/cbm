# -*- coding: utf-8 -*-
"""
Created on Sat Mar 27 18:42:49 2021

@author: Csaba
"""

import ipywidgets as widgets
from ipywidgets import HBox, VBox, Layout
from ipyfilechooser import FileChooser
import datetime
import os
import sys
import geopandas
import pandas as pd
from pathlib import Path
home = str(Path.home())
#sys.path.insert(0, os.path.abspath(home + '/ownCloud/GTCAP/scripts/from_github/cbm/scripts/calendar_view'))

import run_calendar_view_from_jupyter

import importlib
importlib.reload(run_calendar_view_from_jupyter)

def get_options_for_column_selection(vector_file_name):
    # parcel_id_column
    if os.path.isfile(vector_file_name):
        parcels = geopandas.read_file(vector_file_name)
        #get columns of parcel shape to a list
        columns = parcels.columns.tolist()
        #get examples of the values in the different columns in a list
        example_values = parcels.iloc[0].tolist()

        # convert column names and example values to a pandas dataframe
        df = pd.DataFrame(list(zip(columns, example_values)),
                       columns =['columns', 'example_values'])

        # calculate the options column that we will use in the dropdown list
        df['options'] = df[['columns','example_values']].apply(lambda row: str(row[0]) + ' (eg.' + str(row[1])[0:20] +  ')', axis=1)

        # convert the 'options' and 'columns' columns to a list numpy records
        df_to_export = df[['options','columns']]
        records = df_to_export.to_records(index=False)
        result = list(records)

        #convert the list of numpy records to a list of tuples that we can direclty 
        # use as options to the dropdown list
        options_list_of_tuples = []
        for r in result:
            options_list_of_tuples.append(tuple(r))
            
    else:
        options_list_of_tuples = [("","")]
        
    return options_list_of_tuples

def calendar_view_gui(**kwargs):

    default_search_window_start_date=kwargs.get("default_search_window_start_date")   
    default_search_window_end_date=kwargs.get("default_search_window_end_date")     
    default_index_graph_start_date=kwargs.get("default_index_graph_start_date")
    default_index_graph_end_date=kwargs.get("default_index_graph_end_date")
    
    default_shapefile=kwargs.get("default_shapefile")   
    default_out_tif_folder_base=kwargs.get("default_out_tif_folder_base")
    
    
    layout1 = Layout(width='96%', height='35px')
    style1 = {'description_width': 'initial'}

    layout2= widgets.Layout(width='auto', height='40px') #set width and height
    layout3= widgets.Layout(width='auto', height='200px') #set width and height
    
    # function to run when Run button is clicked
    def on_button_clicked(b):
        #run the calendar view script with parameter defined here
        
        run_calendar_view_from_jupyter.run_calendar_view(
#        rcvfj.run_calendar_view_from_jupyter(
            get_scl = w_get_scl.value,
            get_bands = w_get_bands.value,
            merge_bands=w_merge_bands.value,
            lut_stretch_magic=w_lut_stretch_magic.value,
            cv_lut_magic=w_cv_lut_magic.value,
            lut_stretch_dynamic=w_lut_stretch_dynamic.value,
            cv_lut_dynamic=w_cv_lut_dynamic.value,
            stats_band=w_stats_band.value,
            graphs_band=w_graphs_band.value,

            create_ndvi=w_create_ndvi.value,
            cv_ndvi=w_cv_ndvi.value,
            stats_ndvi=w_stats_ndvi.value,
            graphs_ndvi=w_graphs_ndvi.value,
            create_bsi=w_create_bsi.value,
            cv_bsi=w_cv_bsi.value,
            stats_bsi=w_stats_bsi.value,
            graphs_bsi=w_graphs_bsi.value,
            cv_ndvi_hist=w_cv_ndvi_hist.value,
            cv_red_nir_scatter=w_cv_red_nir_scatter.value,

            get_coh=w_get_coh.value,
            stats_coh=w_stats_coh.value,
            graph_coh=w_graph_coh.value,
            get_bs=w_get_bs.value,
            cv_bs=w_cv_bs.value,
            stats_bs=w_stats_bs.value,
            graph_bs=w_graph_bs.value,

            search_window_start_date = w_search_window_start_date.value.strftime("%Y-%m-%d"),
            search_window_end_date = w_search_window_end_date.value.strftime("%Y-%m-%d"),
            index_graph_start_date = w_index_graph_start_date.value.strftime("%Y-%m-%d"),
            index_graph_end_date = w_index_graph_end_date.value.strftime("%Y-%m-%d"),

            vector_file_name = w_select_vector.value,
            out_tif_folder_base = w_select_out_tif_folder_base.value,
            parcel_id_column = w_select_parcel_id_column.value,
            crop_name_column = w_select_crop_name_column.value,

            list_of_parcel_ids_to_process = w_select_parcel_ids.value,
            
            plot_title = w_plot_title.value,
            exclude_cirrus = w_exclude_cirrus.value,
            buffer_size_meter = w_buffer_size_meter.value,
            centroid_shift_degrees = w_centroid_shift_degrees.value
            )


##############################################################    
#Define the elements of the "What to run?" tab
##############################################################
    def set_minimum_options_what_to_run():       
        w_get_scl.value = True
        w_get_bands.value = True
        w_merge_bands.value = True
        w_lut_stretch_magic.value = True
        w_cv_lut_magic.value = True
        w_lut_stretch_dynamic.value = False
        w_cv_lut_dynamic.value = False
        w_stats_band.value = False
        w_graphs_band.value = False
        #second column
        w_create_ndvi.value = True
        w_cv_ndvi.value = False
        w_stats_ndvi.value = True
        w_graphs_ndvi.value = True
        w_create_bsi.value = False
        w_cv_bsi.value = False
        w_stats_bsi.value = False
        w_graphs_bsi.value = False
        w_cv_ndvi_hist.value = False
        w_cv_red_nir_scatter.value = False
        #third column
        w_get_coh.value = False
        w_stats_coh.value = False
        w_graph_coh.value = False
        w_get_bs.value = False
        w_cv_bs.value = False
        w_stats_bs.value = False
        w_graph_bs.value = False    

    #define check box widgets for the first column
    w_get_scl = widgets.Checkbox(
        value=True,
        description='Get and download SCL imagettes',
        disabled=False,
        indent=False
    )

    w_get_bands = widgets.Checkbox(
        value=True,
        description='Get and download band imagettes',
        disabled=False,
        indent=False
    )

    w_merge_bands = widgets.Checkbox(
        value=True,
        description='Merge band imagettes',
        disabled=False,
        indent=False
    )

    w_lut_stretch_magic = widgets.Checkbox(
        value=True,
        description='LUT stretch magic',
        disabled=False,
        indent=False
    )

    w_cv_lut_magic = widgets.Checkbox(
        value=True,
        description='Calendar view LUT magic',
        disabled=False,
        indent=False
    )

    w_lut_stretch_dynamic = widgets.Checkbox(
        value=True,
        description='LUT stretch dynamic',
        disabled=False,
        indent=False
    )

    w_cv_lut_dynamic = widgets.Checkbox(
        value=True,
        description='Calendar view LUT dynamic',
        disabled=False,
        indent=False
    )

    w_stats_band = widgets.Checkbox(
        value=True,
        description='Calculate band statistics',
        disabled=False,
        indent=False
    )

    w_graphs_band = widgets.Checkbox(
        value=True,
        description='Create band graphs',
        disabled=False,
        indent=False
    )

    #check boxes for second column
    w_create_ndvi = widgets.Checkbox(
        value=True,
        description='Create NDVI imagettes',
        disabled=False,
        indent=False
    )

    w_cv_ndvi = widgets.Checkbox(
        value=True,
        description='Calendar view of NDVI imagettes',
        disabled=False,
        indent=False
    )

    w_stats_ndvi = widgets.Checkbox(
        value=True,
        description='Calculate NDVI statistics',
        disabled=False,
        indent=False
    )

    w_graphs_ndvi = widgets.Checkbox(
        value=True,
        description='Create NDVI graphs',
        disabled=False,
        indent=False
    )

    w_create_bsi = widgets.Checkbox(
        value=True,
        description='Create BSI imagettes',
        disabled=False,
        indent=False
    )

    w_cv_bsi = widgets.Checkbox(
        value=True,
        description='Calendar view of BSI imagettes',
        disabled=False,
        indent=False
    )

    w_stats_bsi = widgets.Checkbox(
        value=True,
        description='Calculate BSI statistics',
        disabled=False,
        indent=False
    )

    w_graphs_bsi = widgets.Checkbox(
        value=True,
        description='Create BSI graphs',
        disabled=False,
        indent=False
    )

    w_cv_ndvi_hist = widgets.Checkbox(
        value=True,
        description='Calendar view of NDVI histograms',
        disabled=False,
        indent=False
    )

    w_cv_red_nir_scatter = widgets.Checkbox(
        value=True,
        description='Calendar view of Red-NIR scatterplot',
        disabled=False,
        indent=False
    )


    # check boxes for third column
    w_get_coh = widgets.Checkbox(
        value=True,
        description='Get coherence imagettes',
        disabled=False,
        indent=False
    )

    w_stats_coh = widgets.Checkbox(
        value=True,
        description='Calculate coherence statistics',
        disabled=False,
        indent=False
    )

    w_graph_coh = widgets.Checkbox(
        value=True,
        description='Create coherence graphs',
        disabled=False,
        indent=False
    )

    w_get_bs = widgets.Checkbox(
        value=True,
        description='Get backscatter imagettes',
        disabled=False,
        indent=False
    )

    w_cv_bs = widgets.Checkbox(
        value=True,
        description='Calendar view of backscatter',
        disabled=False,
        indent=False
    )

    w_stats_bs = widgets.Checkbox(
        value=True,
        description='Calculate backscatter statistics',
        disabled=False,
        indent=False
    )

    w_graph_bs = widgets.Checkbox(
        value=True,
        description='Create backscatter graphs',
        disabled=False,
        indent=False
    )
    
    #define check box widget containers for the first, "What to run?" tab
    what_to_run_first_column = VBox(children=[w_get_scl,
                                              w_get_bands,
                                              w_merge_bands,
                                              w_lut_stretch_magic,
                                              w_cv_lut_magic,
                                              w_lut_stretch_dynamic,
                                              w_cv_lut_dynamic,
                                              w_stats_band,
                                              w_graphs_band
                                              ])

    what_to_run_second_column = VBox(children=[w_create_ndvi,
                                               w_cv_ndvi,
                                               w_stats_ndvi,
                                               w_graphs_ndvi,
                                               w_create_bsi,
                                               w_cv_bsi,
                                               w_stats_bsi,
                                               w_graphs_bsi,                                           
                                               w_cv_ndvi_hist,
                                               w_cv_red_nir_scatter
                                              ])

    what_to_run_third_column = VBox(children=[w_get_coh,
                                              w_stats_coh,
                                              w_graph_coh,
                                              w_get_bs,
                                              w_cv_bs,
                                              w_stats_bs,
                                              w_graph_bs
                                               ])
    what_to_run_first_widget = HBox(children=[what_to_run_first_column,
                                     what_to_run_second_column,
                                     what_to_run_third_column])    
    
    w_set_minimum_options_for_what_to_run_button = widgets.Button(
        description='Select minimum',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Select a minimum set of what to run',
        layout=layout1
    )


    w_set_maximum_options_for_what_to_run_button = widgets.Button(
        description='Select all',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Select a maximum set of what to run',
        layout=layout1
    )
    
    what_to_run_second_widget = HBox(children=[w_set_minimum_options_for_what_to_run_button,
                                               w_set_maximum_options_for_what_to_run_button])


    tab_what_to_run = VBox(children=[what_to_run_first_widget,
                                    what_to_run_second_widget])    

    #set selected options for minimum at startup
    set_minimum_options_what_to_run()
    
    #call back functions for the what to run tab
    def w_set_minimum_options_for_what_to_run_button_clicked(b):
        #first column
        w_get_scl.value = True
        w_get_bands.value = True
        w_merge_bands.value = True
        w_lut_stretch_magic.value = True
        w_cv_lut_magic.value = True
        w_lut_stretch_dynamic.value = False
        w_cv_lut_dynamic.value = False
        w_stats_band.value = False
        w_graphs_band.value = False
        #second column
        w_create_ndvi.value = True
        w_cv_ndvi.value = False
        w_stats_ndvi.value = True
        w_graphs_ndvi.value = True
        w_create_bsi.value = False
        w_cv_bsi.value = False
        w_stats_bsi.value = False
        w_graphs_bsi.value = False
        w_cv_ndvi_hist.value = False
        w_cv_red_nir_scatter.value = False
        #third column
        w_get_coh.value = False
        w_stats_coh.value = False
        w_graph_coh.value = False
        w_get_bs.value = False
        w_cv_bs.value = False
        w_stats_bs.value = False
        w_graph_bs.value = False    

    def w_set_maximum_options_for_what_to_run_button_clicked(b):
        #first column
        w_get_scl.value = True
        w_get_bands.value = True
        w_merge_bands.value = True
        w_lut_stretch_magic.value = True
        w_cv_lut_magic.value = True
        w_lut_stretch_dynamic.value = True
        w_cv_lut_dynamic.value = True
        w_stats_band.value = True
        w_graphs_band.value = True
        #second column
        w_create_ndvi.value = True
        w_cv_ndvi.value = True
        w_stats_ndvi.value = True
        w_graphs_ndvi.value = True
        w_create_bsi.value = True
        w_cv_bsi.value = True
        w_stats_bsi.value = True
        w_graphs_bsi.value = True
        w_cv_ndvi_hist.value = True
        w_cv_red_nir_scatter.value = True
        #third column
        w_get_coh.value = True
        w_stats_coh.value = True
        w_graph_coh.value = True
        w_get_bs.value = True
        w_cv_bs.value = True
        w_stats_bs.value = True
        w_graph_bs.value = True     
        
    #event handlers within the "What to run?" tab
    w_set_maximum_options_for_what_to_run_button.on_click(w_set_maximum_options_for_what_to_run_button_clicked) 
    w_set_minimum_options_for_what_to_run_button.on_click(w_set_minimum_options_for_what_to_run_button_clicked) 
        
 
    
##############################################################    
#Define the elements of the "Set dates" tab
##############################################################
    # define widgets for window parameters (start and end dates)
    w_search_window_start_date = widgets.DatePicker(
        description='Search window start date',
        disabled=False,
        value = datetime.datetime.strptime(default_search_window_start_date, '%Y-%m-%d').date(),
        layout=layout1,
        style=style1
    )

    w_search_window_end_date = widgets.DatePicker(
        description='Search window end date',
        disabled=False,
        value = datetime.datetime.strptime(default_search_window_end_date, '%Y-%m-%d').date(),
        layout=layout1,
        style=style1
    )

    w_index_graph_start_date = widgets.DatePicker(
        description='Index graph start date',
        disabled=False,
        value = datetime.datetime.strptime(default_index_graph_start_date, '%Y-%m-%d').date(),
        size = 1,
        layout=layout1,
        style=style1
    )

    w_index_graph_end_date = widgets.DatePicker(
        description='Index graph end date',
        disabled=False,
        value = datetime.datetime.strptime(default_index_graph_end_date, '%Y-%m-%d').date(),
        size =1,
        layout=layout1,
        style=style1
    )


    # This will be the second tab with all the start and end dates
    search_window_column = VBox(children=[w_search_window_start_date,
                                          w_search_window_end_date])
    index_graph_column = VBox(children=[w_index_graph_start_date,
                                        w_index_graph_end_date])
    tab_dates = HBox(children=[search_window_column,index_graph_column])
    
##############################################################    
#Define the elements of the Vector/Output folder selector tab
##############################################################
    #text widget holding the full path of the selected vector shapefile
    w_select_vector = widgets.Text(
        value=default_shapefile,
        placeholder='Type something',
        description='Vector filename:',
        disabled=False, 
        style=style1,
        layout=layout2
    )

    #text widget holding the output base folders full path
    w_select_out_tif_folder_base = widgets.Text(
        value=default_out_tif_folder_base,
        placeholder='Type something',
        description='Base folder for outputs:',
        disabled=False, 
        style=style1,
        layout=layout2
    )

    #dropdown widget for holding the list of columns in the shapefile
    options_list_of_tuples = get_options_for_column_selection(default_shapefile)  
    w_select_parcel_id_column = widgets.Dropdown(
        options=options_list_of_tuples,
        value=options_list_of_tuples[0][1],
        description='Parcel id column:',
        style = {'description_width': 'initial'}
    )
    
    w_select_crop_name_column = widgets.Dropdown(
        options=options_list_of_tuples,
        value=options_list_of_tuples[0][1],
        description='Crop name column:',
        style = {'description_width': 'initial'}
    )

    if os.path.isfile(w_select_vector.value):
        parcels = geopandas.read_file(w_select_vector.value)
        parcel_id_column = w_select_parcel_id_column.value
        default_list_of_parcel_ids_to_process = parcels[parcel_id_column].to_list()
        default_list_of_parcel_ids_to_process.sort()
    else:
        default_list_of_parcel_ids_to_process = [""]

    #multiple select list widget holding the list of parcel ids
    w_select_parcel_ids = widgets.SelectMultiple(
        options=default_list_of_parcel_ids_to_process,
    #     value=['Oranges'],
        rows=10,
        description='Parcel ids',
        disabled=False,
        layout=layout3,
        tyle=style1,
    )


    # Create and display a FileChooser widget
    # fc = FileChooser('c:/Users/Csaba/ownCloud')
    default_shapefile_path = os.path.dirname(w_select_vector.value)
    default_out_tif_folder_base_path = os.path.dirname(w_select_out_tif_folder_base.value)

    fc_shapefile = FileChooser(default_shapefile_path)
    fc_shapefile.filter_pattern = '*.shp'
    
    fc_out_tif_folder_base = FileChooser(default_out_tif_folder_base_path)
    fc_out_tif_folder_base.show_only_dirs = True

    #put the 2 column selector dropdown list widgets in the HBox container
    select_columns_hbox = HBox(children=[w_select_parcel_id_column, w_select_crop_name_column])
    
    # vector_file_name selection tab
    tab_vector = VBox(children=[fc_shapefile, w_select_vector,
                                fc_out_tif_folder_base, w_select_out_tif_folder_base,
                                select_columns_hbox,
                                w_select_parcel_ids])    
    
    #call back functions within the "Vector/Output folder" tab
    def select_parcel_ids(vector_file_name, parcel_id_column):
        parcels = geopandas.read_file(vector_file_name)
        selected_parcel_ids = parcels[parcel_id_column].to_list()
        selected_parcel_ids.sort()
        return selected_parcel_ids

    # callback functions for file selectors
    def add_selected_shapefile_to_widget_value(chooser):
        # Print the selected path, filename, or both
        vector_file_name = fc_shapefile.selected.replace("\\","/")
        w_select_vector.value=vector_file_name

        parcel_id_column = w_select_parcel_id_column.value
        w_select_parcel_ids.options = select_parcel_ids(vector_file_name, parcel_id_column)
        

    def add_selected_out_tif_folder_base_to_widget_value(chooser):
        # Print the selected path, filename, or both
    #     print(fc.selected_path)
        out_tif_folder_base = fc_out_tif_folder_base.selected_path.replace("\\","/")
        w_select_out_tif_folder_base.value=out_tif_folder_base

    
    # Function to apply to drop box object
    def add_parcel_ids_to_widget_value(x):
        parcel_id_column = w_select_parcel_id_column.value
        vector_file_name = w_select_vector.value
        w_select_parcel_ids.options = select_parcel_ids(vector_file_name, parcel_id_column)
        
    def add_column_names_to_dropdowns(x):
        options_list_of_tuples = get_options_for_column_selection(w_select_vector.value)
        w_select_parcel_id_column.options = options_list_of_tuples    
        w_select_crop_name_column.options = options_list_of_tuples
        

    #Register callback function for the file selector widgets
    fc_shapefile.register_callback(add_selected_shapefile_to_widget_value)
    fc_out_tif_folder_base.register_callback(add_selected_out_tif_folder_base_to_widget_value)

    #when parcel id column selector widget is changed (other value selected)
    w_select_parcel_id_column.observe(add_parcel_ids_to_widget_value,names='value') 
    
    #if shapefile name in the shapefile text widget changes for some reason we have to update
    #2 things: the list of column names and the list of parcel ids
    #first we change the list of column names
    w_select_vector.observe(add_column_names_to_dropdowns)

##############################################################    
#Define the elements of the "Other parameters" tab
##############################################################
    #text widget holding the title of the graphs
    w_plot_title = widgets.Text(
        value='',
        placeholder='eg. DK 2019',
        description='Title for graphs:',
        disabled=False, 
        style={'description_width': 'initial'}
    )    
    
    #define check box widget for cloud mask selection
    w_exclude_cirrus = widgets.Checkbox(
        value=True,
        description='Exclude cirrus from stats calculation',
        disabled=False,
        indent=False
    )
    
    w_buffer_size_meter = widgets.BoundedIntText(
            value = 50,
            min=0,
            max=1000,
            step=50,
            description='Buffer size around parcel: ',
            disabled=False,
            style={'description_width': 'initial'})
    
    w_centroid_shift_degrees = widgets.BoundedFloatText(
            value=0.00001,
            min=0,
            max=0.0001,
            step=0.00001,
            description='Centroid shift (degrees): ',
            disabled=False,
            style={'description_width': 'initial'}
    )

        # Other parametrs selection tab
    tab_other = VBox(children=[w_plot_title, w_exclude_cirrus,
                               w_buffer_size_meter,
                               w_centroid_shift_degrees])    
    

###########################################################    
#    Let's put together the main gui from the defined tabs
###########################################################    
    w_title = widgets.HTML(
        value="<h1>Run calendar view script</h1"
    )

    tab = widgets.Tab(children=[tab_what_to_run, tab_dates, 
                                tab_vector,tab_other])
    tab.set_title(0, 'What to run?')
    tab.set_title(1, 'Set dates')
    tab.set_title(2, 'Vector/Output folder')
    tab.set_title(3, 'Other parameters')

    # run button widget
    run_button = widgets.Button(
        description='Run',
    )

    main_first_widget = HBox(children=[w_title])
    main_second_widget=VBox(children=[tab, run_button])
    
    
    #event handler for Run button clicked
    run_button.on_click(on_button_clicked)     
    
    

    
    return VBox(children=[main_first_widget,main_second_widget])