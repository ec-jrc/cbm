#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from os.path import normpath, join
from ipywidgets import (Label, VBox, HBox, Dropdown, Button, Layout)

from cbm.utils import config
from cbm.ipycbm.utils import settings_ds
from cbm.ipycbm.ipy_ext import ext_func, ext_card2db


def extract():

    l_connec = Label("1. Connect to database and object storage.")
    l_create = Label("2. Create the essential CbM tables. The parcels table name will be added as prefix.")
    l_upload = Label("3. Upload .shp, with all the required files (.shp, .cpg, .dbf, .prj, .shx).")
    l_carddb = Label("4. Add CARD metadata to databse tabel 'xx_dias_catalogue'.")
    l_extrac = Label("5. Run parcel extraction routines.")

    path_data = normpath(join(config.get_value(['paths', 'temp']), 'extract'))
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
    wbox = VBox([l_connec, VBox([db_box, db_conf_box]),
                 l_create, ext_func.create_tables(),
                 l_upload, ext_func.upload_shp(path_data),
                 l_carddb, ext_card2db.main(),
                 l_extrac, ext_func.extraction()])

    return wbox
