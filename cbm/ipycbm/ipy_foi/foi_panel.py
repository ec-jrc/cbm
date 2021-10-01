#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import glob
from ipywidgets import (Text, Label, HBox, VBox, Layout, Dropdown,
                        ToggleButtons, Output, HTML, Button,
                        FileUpload, IntText, RadioButtons)

from cbm.utils import config
from cbm.ipycbm.utils import settings_ds, cbm_widgets
from cbm.ipycbm.ipy_ext import ext_func
from cbm.foi import foi_v1
from cbm.datas import db
try:
    from cbm.foi import foi_v2
except Exception as err:
    print(err)


def foi_tab_v1():
    path_foi = "foi/"
    path_foi_func = foi_v1.path_foi_func

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    foi_info = HTML("""FOI procedures version 1 (requires access to a database).
        """, placeholder='FOI Information')

    # Connect to database

    config_info = HTML(value="""1. Connect to database and object storage.<br>
        FOI procedures need direct access to the database. In case there no
        image is provided, access to object storage will be needed as well
        to generate the base image from sentinel images.
        """, placeholder='FOI Information')
    config_conn = Button(
        value=False,
        button_style='info',
        tooltip='Configure db connection.',
        icon='cogs',
        layout=Layout(width='40px')
    )

    config_conn_box = HBox([])

    @config_conn.on_click
    def config_conn_on_click(b):
        if config_conn_box.children == ():
            config_conn_box.children = [settings_ds.direct_conn()]
        else:
            config_conn_box.children = ()

    config_box = VBox([config_info, config_conn,
                       config_conn_box])

    # Spatial data to be tested
    spatial_info = HTML(
        """2. Select the spatial data to be tested - parcels that will be
        checked for heterogeneity and cardinality.<br>
        - Select a table from the database""")

    db_tables = Dropdown(
        options=[],
        description='db Tables:'
    )
    refresh_db_tables = Button(
        value=False,
        button_style='info',
        tooltip='Get db tables.',
        icon='refresh',
        layout=Layout(width='40px')
    )

    @refresh_db_tables.on_click
    def refresh_db_tables_on_click(b):
        db_tables.options = db.tables(config.get_value(['set', 'db_conn']))

    db_tables_box = HBox([db_tables, refresh_db_tables])

    upload_shp = Button(
        description='Create new table',
        value=False,
        button_style='info',
        tooltip='upload_shp.',
        icon='up'
    )

    upload_box = VBox([])

    @upload_shp.on_click
    def upload_shp_on_click(b):
        if upload_box.children == ():
            upload_box.children = [ext_func.upload_shp(path_foi, True)]
        else:
            upload_box.children = ()
    spatial_box = VBox([spatial_info, upload_shp, upload_box, db_tables_box])

    # Thematic raster.
    img_info = HTML(
        """3. Thematic raster - classification raster, or raster from other
        source that will be used for testing heterogeneity and cardinality.<br>
        - Upload or generate raster base image.
        (Only upload is currently available)""")
    img_option = ToggleButtons(
        options=['Upload', 'Generate'],
        value=None,
        disabled=True,
        button_style='info',  # 'success', 'info', 'warning', 'danger' or ''
        tooltips=['Upnload your base image', 'Get from object storage']
    )

    def on_img_option_change(change):
        if img_option.value == 'Upload':
            img_box.children = [HBox([img_info, img_option, img_file])]
        else:
            img_box.children = ()
    img_option.observe(on_img_option_change, 'value')

    img_file = cbm_widgets.get_files_dropdown(
        f'{path_foi}raster', '.tif, .tiff', 'Select Raster')
    img_box = VBox([img_info, img_option, img_file])

    # YAML File upload
    yml_info = HTML(
        """4. YAML file that holds the classes form the thematic raster.<br>
            - This can be also a simple list of values in the notebook
            corespondence between pixel values and names for the classes""")

    yml_file = cbm_widgets.get_files_dropdown(path_foi, '.yml, .yaml',
                                              'Select YML')
    yml_box = VBox([yml_info, yml_file])

    # Database functions
    dbf_info = HTML("""5. Create database functions.<br>
    - Import required database functions for FOI analysis to the database""")

    dbf_insert = Button(
        value=False,
        button_style='info',
        tooltip='Create functions.',
        icon='fa-share-square'
    )

    @dbf_insert.on_click
    def dbf_insert_on_click(b):
        outlog('path_foi_func :', path_foi_func)
        progress.clear_output()
        try:
            functions = glob.glob(f"{path_foi_func}*.func")
            db = config.get_value(['set', 'db_conn'])
            schema = config.get_value(['db', db, 'schema'])
            user = config.get_value(['db', db, 'user'])

            for f in functions:
                db.insert_function(open(f).read().format(
                    schema=schema, owner=user))
                outlog(f"The '{f}' Was imported to the database.")
            finc_list = [
                f"ipycbm_{f.split('/')[-1].split('.')[0]}, " for f in functions]
            outlog(
                f"The functions: {('').join(finc_list)} where added to the database")
        except Exception as err:
            outlog("Could not add functions to dattabase.", err)

    dbf_box = VBox([dbf_info, dbf_insert])

    # FOI Parameters
    param_info = HTML(
        """6. Set FOI v1 Parameters""")

    # heterogeneity_threshold
    param_heto_info = HTML("""
    Minimum and maximum thresholds for heterogeneity checks. In the example,
    any parcel with percentage of pixels for one class between 30 and 70 from
    the total, will be considered heterogenous.
    """)
    param_min_het = IntText(
        value=30,
        description='MIN:',
        tooltip="Minimum threshold for heterogeneity checks",
        layout=Layout(width='150px')
    )
    param_max_het = IntText(
        value=70,
        description='MAX:',
        tooltip="Maximum threshold for heterogeneity checks",
        layout=Layout(width='150px')
    )

    param_area_info = HTML("""Minimum area for clusters selection -
    only clusters bigger from this threshold will be counted.
    """)
    param_area = IntText(
        value=2000,
        description='area:',
        tooltip="Minimum area for clusters selection.",
        layout=Layout(width='200px')
    )

    param_box = VBox([param_info,
                      param_heto_info, HBox([param_min_het, param_max_het]),
                      param_area_info, param_area
                      ])

    # Run FOI analysis
    run_info = Label("7. Run the FOI analysis.")
    run_analysis = Button(
        description='Run FOI v1',
        value=False,
        button_style='info',
        tooltip='Run FOI analysis version 1',
        icon='play',
    )
    run_box = VBox([run_info, run_analysis])

    @run_analysis.on_click
    def run_analysis_on_click(b):
        with progress:
            foi_v1.main(
                db_tables.value,
                f"{img_file.children[1].children[0].value}",
                f"{yml_file.children[1].children[0].value}",
                param_min_het.value, param_max_het.value, param_area.value)

    wbox = VBox([foi_info,
                 config_box,
                 spatial_box,
                 img_box,
                 yml_box,
                 dbf_box,
                 param_box,
                 run_box,
                 progress])

    return wbox


def foi_tab_v2():
    path_foi = "foi/"
    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    foi_info = HTML("""FOI procedures version 2 (does not require access to a database).
        """, placeholder='FOI Information')

    # Vector file
    shp_info = HTML(
        """1. Spatial data to be tested -
        parcels that will be checked for heterogeneity and cardinality.""")
    shp_file = cbm_widgets.get_files_dropdown(
        f'{path_foi}vector', '', 'Select .shp', True, True)
    shp_box = VBox([shp_info, shp_file])

    # Thematic raster.
    img_info = HTML(
        """2. Thematic raster - classification raster, or raster from other
        source that will be used for testing heterogeneity and cardinality.<br>
        - Upload or generate raster base image.
        (Only upload is currently available)""")
    img_option = ToggleButtons(
        options=['Upload', 'Generate'],
        value=None,
        disabled=True,
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltips=['Upnload your base image', 'Get from object storage']
    )

    def on_img_option_change(change):
        if img_option.value == 'Upload':
            img_box.children = [HBox([img_info, img_option, img_file])]
        else:
            img_box.children = ()
    img_option.observe(on_img_option_change, 'value')
    img_file = cbm_widgets.get_files_dropdown(
        f'{path_foi}raster', '.tif, .tiff', 'Select Raster')
    img_box = VBox([img_info, img_option, img_file])

    # YAML File upload
    yml_info = HTML(
        """3. YAML file that holds the classes form the thematic raster.<br>
            - This can be also a simple list of values in the notebook
            corespondence between pixel values and names for the classes""")
    yml_file = cbm_widgets.get_files_dropdown(path_foi, '.yml, .yaml',
                                              'Select YML')
    yml_box = VBox([yml_info, yml_file])

    # FOI Prerequisites
    pre_info = Label("4. Set FOI v2 Parameters.")

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

    pre_box = VBox([
        pre_info, pre_heto_chec, pre_heto_chec_box,
        pre_pixel_connectivity, pre_negative_buffer,
        HBox([pre_min_cluster_size,
              HTML("""Minimum area for clusters selection - only clusters bigger
                    from this threshold will be counted.""")])
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

    @run_analysis.on_click
    def run_analysis_on_click(b):
        with progress:
            foi_v2.main(
                f"{shp_file.children[1].children[0].value}",
                f"{img_file.children[1].children[0].value}",
                f"{yml_file.children[1].children[0].value}",
                pre_negative_buffer.value,
                pre_min_het.value,
                pre_max_het.value,
                pre_pixel_connectivity.value,
                pre_min_cluster_size.value)

    wbox_v2 = VBox([foi_info,
                    shp_box,
                    img_box,
                    yml_box,
                    pre_box,
                    run_info,
                    run_box,
                    progress])

    return wbox_v2
