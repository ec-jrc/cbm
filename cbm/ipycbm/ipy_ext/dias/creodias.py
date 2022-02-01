#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import datetime
from IPython.display import display
from ipywidgets import (Text, Label, HBox, VBox, Layout, Dropdown,
                        Output, Button, DatePicker, RadioButtons,
                        BoundedIntText)

from cbm.utils import config, data_options
from cbm.card2db import creodias as meta2DB
from cbm.ipycbm.ipy_ext import ext_func
from cbm.datas import db

def main():

    aoi_method = RadioButtons(
#         options=[('Predefined MS polygons', 1), ('Get polygon from dataset extent', 2), ('Draw polygon on a map', 3)],
        options=[('Predefined MS polygons', 1), ('Get polygon from dataset extent', 2)],
        value=2,
        description='AOI:',
        disabled=False,
    )

    mss = data_options.ms_polygons()
    ms = Dropdown(
        options=[(m, mss[m]) for m in mss],
        tooltip="AOI",
        description='AOI:',
    )
    tb = Dropdown(
        options=db.tables(),
        tooltip="Select table",
        description='Table:',
    )
    tb_refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh'
    )

    aoi_box = VBox([HBox([tb, tb_refresh])])



    year = BoundedIntText(
            value=2020,
            min=2010,
            max=2100,
            step=1,
            description='Year:',
            disabled=False
        )

    plevel = RadioButtons(
        options=['LEVEL2A', 'LEVEL2AP'],
        value='LEVEL2A',
        description='pLevel:',
        disabled=False,
    )
    ptype = RadioButtons(
        options=['CARD-COH6', 'CARD-BS'],
        description='pType:',
        disabled=False,
    )
    card_options = VBox([plevel])
    card = RadioButtons(
        options=[('Sentinel 1', 's1'),('Sentinel 2', 's2')],
        value='s2',
        description='card:',
        disabled=False,
    )

    bt_card2db = Button(
        description='Add CARD to db',
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Add CARD catalogue to database',
        icon='database'
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    def on_aoi_method_change(change):
        if aoi_method.value == 1:
            aoi_box.children = [ms]
        elif aoi_method.value == 2:
            aoi_box.children = [HBox([tb, tb_refresh])]
        elif aoi_method.value == 3:
            aoi_box.children = []
    aoi_method.observe(on_aoi_method_change, 'value')

    def on_card_change(change):
        if card.value == 's2':
            card_options.children = [plevel]
        else:
            card_options.children = [ptype]
    card.observe(on_card_change, 'value')

    @tb_refresh.on_click
    def tb_refresh_on_click(b):
        tb.options = db.tables()

    @bt_card2db.on_click
    def bt_card2db_on_click(b):
        progress.clear_output()
        try:
            with open(f"{config.get_value(['paths','temp'])}tb_prefix", 'r') as f:
                tb_prefix = f.read()
        except Exception:
            tb_prefix = ''

        dc_table = f'dias_catalogue'
        if db.tb_exist(dc_table) is True:
            if aoi_method.value == 1:
                polygon = ms.value.replace(' ','+')
            elif aoi_method.value == 2:
                polygon = db.tb_extent(tb.value)
            elif aoi_method.value == 3:
                polygon = ms.value.replace(' ','+')

#             print(polygon)
            if card.value == 's2':
                option = plevel.value
            else:
                option = ptype.value

            outlog("Inserting CARD catalogue to database ...")
            with progress:
                meta2DB.dias_cat(tb_prefix,
                                f"POLYGON(({polygon}))",
                                datetime.datetime(year.value, 1, 1),
                                datetime.datetime(year.value, 12, 31),
                                card.value, option)
            outlog("Completed.")
        else:
            outlog(f"Table {dc_table} does not exist.")

    wbox = VBox([HBox([aoi_method, aoi_box]),
                 year,
                 HBox([card, card_options]),
                 bt_card2db, progress])

    return wbox


