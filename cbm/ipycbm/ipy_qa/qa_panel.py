#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from os.path import normpath, join
from ipywidgets import (HBox, VBox, Layout, Dropdown,
                        Output, HTML, Button, Accordion)

from cbm.utils import config
from cbm.ipycbm.utils import settings, settings_ds

from cbm.ipycbm.ipy_view import view_panel
from cbm.ipycbm.ipy_ext import ext_func, ext_card2db
from cbm.ipycbm.ipy_get import get_panel


def qa():
    # path_plug = "cbm/foi/foi_db_func/"
    path_data = normpath(join(config.get_value(['paths', 'temp']), 'qa'))

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    qa_info = HTML(
        value="""The CbM Quality Assurance (QA) is a framework intended to enable
        the Member State (MS) to report to the Commission about the state of one of
        the components inside the control and management system.<br>
        To run the Quality Assessment (QA) procedures direct access to the
        database and the object storage with CARD data is required.<br>
        """,
        placeholder='QA Information',
    )

    # Connect
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

    db_conf_box = HBox([])

    @db_config.on_click
    def db_config_on_click(b):
        if db_conf_box.children == ():
            db_conf_box.children = [settings_ds.direct_conn()]
        else:
            db_conf_box.children = ()

    accor = Accordion(children=[
        VBox([db_box, db_conf_box]),
        ext_func.upload_shp(path_data),
        ext_func.create_tables(),
        ext_card2db.dias_cat(),
        settings_ds.direct(),
        ext_func.extraction(),
        VBox([get_panel.get()],
             layout=Layout(border='1px solid black')),
        view_panel.view()])

    def on_tb_name(change):
        # Get to the widget that is inside the accordion widget
        # Any change of the order of the widgets within the widgets
        # box will break this connection.
        new_value = accor.children[1].children[3].children[0].value
        accor.children[2].children[1].value = new_value
    accor.children[1].children[3].children[0].observe(on_tb_name, 'value')

    def on_start(change):
        new_value = accor.children[3].children[2].children[0].value
        accor.children[5].children[0].children[0].value = new_value
    accor.children[3].children[2].children[0].observe(on_start, 'value')

    def on_end(change):
        new_value = accor.children[3].children[2].children[1].value
        accor.children[5].children[0].children[1].value = new_value
    accor.children[3].children[2].children[1].observe(on_end, 'value')

    accor.set_title(0, "1. Connect to database and object storage.")
    accor.set_title(
        1, "2. Upload .shp, with all the required files (cpg, dbf, prj, shx).")
    accor.set_title(2, "3. Create the essential CbM tables.")
    accor.set_title(
        3, "4. Add CARD metadata to database table 'xx_dias_catalogue'.")
    accor.set_title(4, "5. Configure database tables.")
    accor.set_title(5, "6. Run parcel extraction routines.")
    accor.set_title(6, "7. Get parcel information, time series and images.")
    accor.set_title(7, "8. View parcel data.")

    wbox = VBox([qa_info, accor])

    return wbox
