#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import glob
from ipywidgets import (Text, Label, HBox, VBox, Layout, Tab, Dropdown,
                        ToggleButtons, Output, SelectMultiple, HTML, Button,
                        FileUpload, Checkbox, Accordion, IntText, RadioButtons)

from cbm.utils import config
from cbm.ipycbm.utils import settings
from cbm.sources import db
from cbm.ipycbm.ipy_ext import ext_func
from cbm.foi import foi_v1
from cbm.foi import foi_v2


def foi_tab_v1():
    path_foi = "cbm/foi/foi_db_func/"
    path_data = f"{config.get_value(['paths', 'temp'])}foi/"

    progress = Output()
    def outlog(*text):
        with progress:
            print(*text)

    foi_info = HTML(
        value="""FOI procedures need direct access to the database. <br>
        """,
        placeholder='FOI Information',
    )
#         In case there no image is provided, access to object storage will be needed to generate the base image from sentinel images.

    # Connect to database
    db_info = Label(
        f"1. Connect to database and object storage.")
    db_select = Dropdown(
        options=[db for db in config.get_value(['db'])],
        description='Configure:',
        disabled=True,
        layout=Layout(width='140px')
    )
    db_config = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Configure db connection.',
        icon='cogs',
        layout=Layout(width='40px')
    )
    db_box = HBox([db_select, db_config])

    parcels_table = RadioButtons(
        options=[('Upload .shp', 0), ('From database', 1)],
    #    value='pineapple', # Defaults to 'pineapple'
    #    layout={'width': 'max-content'}, # If the items' names are long
#         description='Pizza topping:',
        disabled=False
    )
    par_box = HBox([])
    def on_parcels_table(method):
        if method.new == 0:
            par_box.children = []
        elif method.new == 1:
            par_box.children = []
    parcels_table.observe(on_parcels_table, 'value')

    # Generate or upload image.
    img_info = Label(
        f"3. Upload or generate raster base image. (Only upload is currently available)")
    img_option = ToggleButtons(
        options=['Upload', 'Generate'],
        value=None,
        disabled=True,
        button_style='info', # 'success', 'info', 'warning', 'danger' or ''
        tooltips=['Upnload your base image', 'Get from object storage']
    )

    img_dist_folder = Text(
        value=f"{path_data}raster/",
        placeholder='tmp/',
        description='Folder:',
        disabled=False
    )
    img_select = FileUpload(
        description='Select file:',
        icon='plus',
        accept='.tif, .tiff',
        multiple=True  # True to accept multiple files upload else False
    )
    img_clear = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Clear selections.',
        icon='broom',
        layout=Layout(width='40px')
    )
    img_upload = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Upload foi base image (.tif)',
        icon='fa-upload',
        layout=Layout(width='40px')
    )

    img_box = HBox([HBox([img_dist_folder, img_select,
                          img_clear, img_upload])])

    # YAML File upload
    yml_select = FileUpload(
        description='Select file:',
        icon='plus',
        accept='.yml, .yaml, .txt',
        multiple=False
    )
    yml_clear = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Clear selection.',
        icon='broom',
        layout=Layout(width='40px')
    )
    yml_upload = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Upload yaml file.',
        icon='fa-upload',
        layout=Layout(width='40px')
    )
    yml_box = HBox([yml_select, yml_clear, yml_upload])

    # FOI Prerequisites
    pre_info = Label("4. FOI v1 Prerequisites.")
    pre_ins_func = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Insert functions to database.',
        icon='fa-share-square',
        layout=Layout(width='40px')
    )
    pre_ins_func_box = HBox([Label("Add functions to database:"), pre_ins_func])
    vector_file = Dropdown(
        options=[s for s in glob.glob(f'{path_data}vector/*'
                                      ) if '.shp' in s],
        description='Vector file:',
        disabled=False,
    )
    raster_file = Dropdown(
        options=[s for s in glob.glob(f'{path_data}raster/*'
                                      ) if '.tif' in s],
        description='Raster file:',
        disabled=False,
    )

    yaml_file = Dropdown(
        options=[s for s in glob.glob(f'{path_data}/*'
                                      ) if '.yml' in s],
        description='yaml file:',
        disabled=False,
    )

    # heterogeneity_threshold
    pre_heto_chec = HTML("""
    Minimum and maximum thresholds for heterogeneity checks. In the example,
    any parcel with percentage of pixels for one class between 30 and 70 from
    the total, will be considered heterogenous.
    """)
    pre_min_het = IntText(
        value=30,
        description='MIN:',
        tooltip="Minimum threshold for heterogeneity checks",
        disabled=False,
        layout=Layout(width='150px')
    )
    pre_max_het = IntText(
        value=70,
        description='MAX:',
        tooltip="Maximum threshold for heterogeneity checks",
        disabled=False,
        layout=Layout(width='150px')
    )
    pre_heto_chec_box = HBox([pre_min_het, pre_max_het])
    pre_min_area = IntText(
        value=2000,
        description='area:',
        tooltip="Minimum area for clusters selection.",
        disabled=False,
        layout=Layout(width='200px')
    )

    refresh_selections = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh'
    )

    pre_box = VBox([
        pre_info, pre_ins_func_box,
        HBox([Label("Select the requared files:"), refresh_selections]),
        HTML("""a. Spatial data to be tested - parcels that will
            be checked for heterogeneity and cardinality."""),
        HBox([vector_file]),
        HTML("""b. Thematic raster - classification raster, or raster 
            from other source that will be used for testing heterogeneity and cardinality."""),
        HBox([raster_file]),
        HTML("""c. YAML file that holds the classes form the thematic raster file - 
            can be also a simple list of values in the notebook 
            corespondence between pixel values and names for the classes"""),
        HBox([yaml_file, yml_box]),
        pre_heto_chec, pre_heto_chec_box,
        HBox([pre_min_area, HTML(
            "Minimum area for clusters selection - only clusters bigger from this threshold will be counted.")])
    ])

    # Run FOI analysis
    run_info = Label("5. Run the FOI analysis.")
    run_analysis = Button(
        description='Run FOI v1',
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Run FOI analysis version 1',
        icon='play',
    )
    run_box = HBox([run_analysis])

    def on_img_option_change(change):
        if img_option.value == 'Upload':
            img_box.children = [HBox([img_dist_folder, img_select,
                                      img_clear, img_upload])]
        else:
            img_box.children = ()
    img_option.observe(on_img_option_change, 'value')

    @refresh_selections.on_click
    def refresh_selections_on_click(b):
        vector_file.options = [s for s in glob.glob(f'{path_data}vector/*'
                                      ) if '.shp' in s]
        raster_file.options = [s for s in glob.glob(f'{path_data}raster/*'
                                      ) if '.tif' in s]
        yaml_file.options = [s for s in glob.glob(f'{path_data}/*'
                                      ) if '.yml' in s]

    @img_clear.on_click
    def img_clear_on_click(b):
        img_select.value.clear()
        img_select._counter = 0

    @img_upload.on_click
    def img_upload_on_click(b):
        progress.clear_output()
        os.makedirs(img_dist_folder.value, exist_ok=True)
        for key in img_select.value:
            content = img_select.value[key]['content']
            with open(f'{img_dist_folder.value}{key}', 'wb') as f:
                f.write(content)
        outlog("All files are uploaded.")

    @yml_clear.on_click
    def yml_clear_on_click(b):
        yml_select.value.clear()
        yml_select._counter = 0

    @yml_upload.on_click
    def yml_upload_on_click(b):
        progress.clear_output()
        yml_dist_folder = f'{path_data}'
        os.makedirs(yml_dist_folder, exist_ok=True)
        for key in yml_select.value:
            content = yml_select.value[key]['content']
            with open(f'{yml_dist_folder}{key}', 'wb') as f:
                f.write(content)
        outlog("The yaml file is uploaded.")

    db_conf_box = HBox([])
    @db_config.on_click
    def db_config_on_click(b):
        if db_conf_box.children == ():
            db_conf_box.children = [settings.direct_conn()]
        else:
            db_conf_box.children = ()

    @pre_ins_func.on_click
    def pre_ins_func_on_click(b):
        progress.clear_output()
        try:
            functions = glob.glob(f"{path_foi}*.func")
            db = config.get_value(['set', 'db_conn'])        
            sche = config.get_value(['db', db, 'sche'])
            user = config.get_value(['db', db, 'user'])

            for f in functions:
                db.insert_function(open(f).read().format(
                    schema=sche, owner=user))
            finc_list = [f"ipycbm_{f.split('/')[-1].split('.')[0]}, " for f in functions]
            outlog(f"The functions: {('').join(finc_list)}where added to the database")
        except Exception as err:
            outlog("Could not add functions to dattabase.", err)

    @run_analysis.on_click
    def run_analysis_on_click(b):
        with progress:
            foi_v1.main(vector_file.value, raster_file.value, yaml_file.value,
                pre_min_het.value, pre_max_het.value, pre_min_area.value)


    wbox = VBox([foi_info,
                 db_info, db_box, db_conf_box,
                 ext_func.upload_shp(path_data),
                 img_info, img_option, img_box,
                 pre_box,
                 run_info, 
                 run_box,
                 progress])

    return wbox

def foi_tab_v2():
    path_data = f"{config.get_value(['paths', 'temp'])}foi/"

    progress = Output()
    def outlog(*text):
        with progress:
            print(*text)


    imp_refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh'
    )

    foi_info = HTML(
        value="""FOI procedures version 2 does not need direct access to the database.
        """,
        placeholder='FOI Information',
    )

    # Generate or upload image.
    img_info = Label(
        f"3. Upload or generate raster base image. (Only upload is currently available)")
    img_option = ToggleButtons(
        options=['Upload', 'Generate'],
        value=None,
        disabled=True,
        button_style='info', # 'success', 'info', 'warning', 'danger' or ''
        tooltips=['Upnload your base image', 'Get from object storage']
    )

    img_dist_folder = Text(
        value=f"{path_data}raster/",
        placeholder='tmp/',
        description='Folder:',
        disabled=False
    )
    img_select = FileUpload(
        description='Select file:',
        icon='plus',
        accept='.tif, .tiff',
        multiple=True  # True to accept multiple files upload else False
    )
    img_clear = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Upload foi reference data (.shp)',
        icon='broom',
        layout=Layout(width='40px')
    )
    img_upload = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Upload foi base image (.tif)',
        icon='fa-upload',
        layout=Layout(width='40px')
    )

    img_box = HBox([HBox([img_dist_folder, img_select,
                          img_clear, img_upload])])
    
    # YAML File upload
    yml_select = FileUpload(
        description='Select file:',
        icon='plus',
        accept='.yml, .yaml, .txt',
        multiple=False
    )
    yml_clear = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Clear selection.',
        icon='broom',
        layout=Layout(width='40px')
    )
    yml_upload = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Upload yaml file.',
        icon='fa-upload',
        layout=Layout(width='40px')
    )
    yml_box = HBox([yml_select, yml_clear, yml_upload])

    # FOI Prerequisites
    pre_info = Label("4. FOI v2 Prerequisites.")
    vector_file = Dropdown(
        options=[s for s in glob.glob(f'{path_data}vector/*'
                                      ) if '.shp' in s],
        description='Vector file:',
        disabled=False,
    )
    raster_file = Dropdown(
        options=[s for s in glob.glob(f'{path_data}raster/*'
                                      ) if '.tif' in s],
        description='Raster file:',
        disabled=False,
    )
    yaml_file = Dropdown(
        options=[s for s in glob.glob(f'{path_data}/*'
                                      ) if '.yml' in s],
        description='yaml file:',
        disabled=False,
    )

    # heterogeneity_threshold
    pre_heto_chec = HTML("""
    Minimum and maximum thresholds for heterogeneity checks. In the example,
    any parcel with percentage of pixels for one class between 30 and 70 from
    the total, will be considered heterogenous.
    """)
    pre_min_het = IntText(
        value=30,
        description='MIN:',
        tooltip="Minimum threshold for heterogeneity checks",
        disabled=False,
        layout=Layout(width='150px')
    )
    pre_max_het = IntText(
        value=70,
        description='MAX:',
        tooltip="Maximum threshold for heterogeneity checks",
        disabled=False,
        layout=Layout(width='150px')
    )
    pre_heto_chec_box = HBox([pre_min_het, pre_max_het])
    pre_min_cluster_size = IntText(
        value=20,
        description='pixels:',
        tooltip="Minimum area for clusters selection.",
        disabled=False,
        layout=Layout(width='200px')
    )
    pre_pixel_connectivity = IntText(
        value=8,
        description='connectivity type:',
        tooltip="Type of pixel connectivity in analysis. Accepted values: 4 or 8.",
        disabled=False,
        layout=Layout(width='200px')
    )
    pre_negative_buffer = IntText(
        value=-10,
        description='negative buffer:',
        tooltip="Negative buffer to be applied on the FOI",
        disabled=False,
        layout=Layout(width='200px')
    )
    
    refresh_selections = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh'
    )
    pre_box = VBox([
        pre_info, Label("Select the requared files:"),
        HBox([vector_file, HTML(
            "Spatial data to be tested - parcels that will be checked for heterogeneity and cardinality.")]),
        HBox([raster_file, HTML("""Thematic raster - classification raster, or raster 
            from other source that will be used for testing heterogeneity and cardinality.""")]),
        HTML("""YAML file that holds the classes form the thematic raster file - 
            can be also a simple list of values in the notebook 
            corespondence between pixel values and names for the classes"""),
        HBox([yaml_file, yml_box]),
        pre_heto_chec, pre_heto_chec_box, pre_pixel_connectivity, pre_negative_buffer,
        HBox([pre_min_cluster_size, HTML(
            "Minimum area for clusters selection - only clusters bigger from this threshold will be counted.")])
    ])

    # Run FOI analysis
    run_info = Label("5. Run the FOI analysis.")
    run_analysis = Button(
        description='Run FOI v2',
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Run FOI analysis version 2',
        icon='play',
    )
    run_box = HBox([run_analysis])

    def on_img_option_change(change):
        if img_option.value == 'Upload':
            img_box.children = [HBox([img_dist_folder, img_select,
                                      img_clear, img_upload])]
        else:
            img_box.children = ()
    img_option.observe(on_img_option_change, 'value')
    
    @refresh_selections.on_click
    def refresh_selections_on_click(b):
        vector_file.options = [s for s in glob.glob(f'{path_data}vector/*'
                                      ) if '.shp' in s]
        raster_file.options = [s for s in glob.glob(f'{path_data}raster/*'
                                      ) if '.tif' in s]
        yaml_file.options = [s for s in glob.glob(f'{path_data}/*'
                                      ) if '.yml' in s]

    @img_clear.on_click
    def img_clear_on_click(b):
        img_select.value.clear()
        img_select._counter = 0

    @img_upload.on_click
    def img_upload_on_click(b):
        progress.clear_output()
        os.makedirs(img_dist_folder.value, exist_ok=True)
        for key in img_select.value:
            content = img_select.value[key]['content']
            with open(f'{img_dist_folder.value}{key}', 'wb') as f:
                f.write(content)
        outlog("All files are uploaded.")
        
    @yml_clear.on_click
    def yml_clear_on_click(b):
        yml_select.value.clear()
        yml_select._counter = 0

    @yml_upload.on_click
    def yml_upload_on_click(b):
        progress.clear_output()
        yml_dist_folder = f'{path_data}'
        os.makedirs(yml_dist_folder, exist_ok=True)
        for key in yml_select.value:
            content = yml_select.value[key]['content']
            with open(f'{yml_dist_folder}{key}', 'wb') as f:
                f.write(content)
        outlog("The yaml file is uploaded.")

    @run_analysis.on_click
    def run_analysis_on_click(b):
        with progress:
            foi_v2.main(vector_file.value, raster_file.value, yaml_file.value, pre_negative_buffer.value, pre_min_het.value, pre_max_het.value, pre_pixel_connectivity.value, pre_min_cluster_size.value)            


    wbox_v2 = VBox([ext_func.upload_shp(path_data),
                 img_info, img_option, img_box,
                 pre_box,
                 run_info, 
                 run_box,
                 progress])

    return wbox_v2

