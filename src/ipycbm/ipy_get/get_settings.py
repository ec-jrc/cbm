#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (Text, VBox, HBox, Label, Password, RadioButtons,
                        Button, Layout, Box, Tab, Output, Dropdown,
                        FloatText, BoundedIntText, Combobox)

from src.utils import config, data_options
from src.ipycbm.utils import settings
from src.sources import database


def widget_box():

    source = int(config.get_value(['set', 'data_source']))

    sources = RadioButtons(
        options=[
            ("JRC RESTful API.", 0),
            ("Direct access to database and object storage.", 1)
        ],
        value=source,
        layout={'width': 'max-content'}
    )

    sources_box = Box([
        Label(value="Data sources:"),
        sources]
    )

    info_api = Label("RESTful API Settings.")
    info_direct = Label("Direct access settings")

    view_options = VBox([info_direct])

    if source == 0:
        view_options.children = [info_api, rest_api()]
    elif source == 1:
        view_options.children = [info_direct, direct()]

    def on_source_change(change):
        view_options.children = []
        if sources.value == 0:
            view_options.children = [info_api, rest_api()]
        elif sources.value == 1:
            view_options.children = [info_direct, direct()]
        config.update(['set', 'data_source'], str(sources.value))

    sources.observe(on_source_change, 'value')

    wbox_sources = VBox([sources_box, view_options],
                        layout=Layout(border='1px solid black'))

    info_general = Label(value="General settings:")

    wbox = VBox([wbox_sources, info_general, settings.widget_box()])

    return wbox


def rest_api(mode=None):
    """"""
    values = config.read()

    wt_url = Text(
        value=values['api']['url'],
        placeholder='Add URL',
        description='API URL:',
        disabled=False
    )
    wt_user = Text(
        value=values['api']['user'],
        placeholder='Username',
        description='API User:',
        disabled=False
    )
    wt_pass = Password(
        value=values['api']['pass'],
        placeholder='******',
        description='API Password:',
        disabled=False
    )

    wb_save = Button(
        description='Save',
        disabled=False,
        icon='save'
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    @wb_save.on_click
    def wb_save_on_click(b):
        config.update(['api', 'url'], str(wt_url.value))
        config.update(['api', 'user'], str(wt_user.value))
        if wt_pass.value != '':
            config.update(['api', 'pass'], str(wt_pass.value))
        outlog("API information is updated")

    wbox = VBox([wt_url, wt_user, wt_pass, wb_save, progress])

    return wbox


def direct():
    #     try:
    tab_box = Tab(children=[settings.direct_conn(), direct_settings()])

    tab_box.set_title(0, 'Connection')
    tab_box.set_title(1, 'db Configuration')
#     except:
#         tab_box = Tab(children=[direct_conn()])
#         tab_box.set_title(0, 'Connection')
#         print("!WARNING! Can not load direct configuration settings.")
    return tab_box


def direct_settings():
    values = config.read()
    ds_def = values['set']['ds_conf']
    ds_dye = values['set']['ds_year']
    if ds_def not in [d for d in values['ds_conf']]:
        ds_def = [d for d in values['ds_conf']][0]

    dsc = Dropdown(
        options=[d for d in values['ds_conf']],
        value=ds_def,
        description='Default:',
        disabled=False,
        layout=Layout(width='200px')
    )

    dsy = Dropdown(
        options=[int(y) for y in values['ds_conf'][dsc.value]['years']],
        value=int(ds_dye),
        description='Dataset year:',
        disabled=False,
        layout=Layout(width='180px')
    )

    btn_refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh')

    @btn_refresh.on_click
    def btn_refresh_on_click(b):
        values = config.read()
        ds_c = values['set']['ds_conf']
        ds_y = values['set']['ds_year']
        dsc.options = [d for d in values['ds_conf']]
        dsy.options = [int(y) for y in values['ds_conf'][ds_c]['years']]
        dsc.value = ds_c
        dsy.value = int(ds_y)

    def on_dsc_change(change):
        config.update(['set', 'ds_conf'], dsc.value)
        values = config.read()
        ds_c = values['set']['ds_conf']
        dsy.options = [int(y) for y in values['ds_conf'][ds_c]['years']]
    dsc.observe(on_dsc_change, 'value')

    def on_dsy_change(change):
        config.update(['set', 'ds_year'], str(dsy.value))
    dsy.observe(on_dsy_change, 'value')

    bt_set = Button(layout=Layout(width='40px'), icon='cogs',
                    tooltip="Configure this dataset")
    bt_new = Button(layout=Layout(width='40px'), icon='plus',
                    tooltip="Add new dataset configuration")
    bt_rec = Button(layout=Layout(width='40px'), icon='trash-alt',
                    tooltip='Delete dataset configuration')
    bt_rey = Button(layout=Layout(width='40px'), icon='trash-alt',
                    tooltip='Delete only the selected year.')
    dsc_box = HBox([dsc, btn_refresh, bt_rec, dsy, bt_set, bt_rey, bt_new])

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    def dsc_config(dsc_value):
        values = config.read()
        ds_db = Dropdown(
            options=["1"],
            value="1",
            description='Database:',
            disabled=False,
            layout=Layout(width='140px')
        )

        try:
            with open(f"{config.get_value(['paths','temp'])}tb_prefix", 'r') as f:
                code_value = f.read()
        except Exception:
            code_value = dsc_value

        ds_code = Combobox(
            value=code_value,
            placeholder='abc',
            options=[m for m in data_options.eu_ms()]+[''],
            description='AOI code:',
            ensure_option=False,
            disabled=False,
            layout=Layout(width='200px'),
            tooltip='Lowercase AOI code name for the dataset (5chr max).'
        )
        ds_year = BoundedIntText(
            value=int(dsy.value),
            min=1980,
            max=2100,
            step=1,
            description='Dataset year:',
            disabled=False,
            layout=Layout(width='180px')

        )
        ds_desc = Text(
            value=values['ds_conf'][dsc_value]['desc'],
            description='Description:',
            disabled=False
        )

        info_map_text = ["Set default map view options. ",
                         "You can get automatically the dataset ",
                         "center coordinates."]

        lat, lon = values['ds_conf'][dsc_value]['center'].split(",")
        map_cent_lat = FloatText(
            value=float(lat),
            description='Lat:',
            disabled=False,
            layout=Layout(width='160px')
        )
        map_cent_lon = FloatText(
            value=float(lon),
            description='Lon:',
            disabled=False,
            layout=Layout(width='160px')
        )
        map_zoom = BoundedIntText(
            value=values['ds_conf'][dsc_value]['zoom'],
            min=0,
            max=20,
            step=1,
            description='Zoom:',
            disabled=False,
            layout=Layout(width='140px')
        )
        bt_get_center = Button(
            layout=Layout(width='40px'),
            icon='bullseye',
            tooltip='Get center point from database.'
        )

        ds_box = HBox([ds_code, ds_year, ds_desc])
        map_box = HBox([Label("Map center: "), map_cent_lat,
                        map_cent_lon, bt_get_center, map_zoom])

        info_config = Label(
            """Change 'AOI code' value to create a new configuration set or 
            leave the same 'AOI code' value to configure the selected one.""")

        db = int(values['ds_conf'][dsc_value]['db'])

        def get_tb_list():
            tbls = database.tables(db, None, False)
            if tbls is None:
                return []
            else:
                return tbls

        tb_dc = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['ds_conf'][dsc_value]['years'][
                    str(ds_year.value)]['tables']['dias_catalog'],
                get_tb_list(), False),
            description='DIAS catalog:',
            disabled=False
        )
        tb_pr = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['ds_conf'][dsc_value]['years'][
                    str(ds_year.value)]['tables']['parcels'],
                get_tb_list(), False),
            description='Parcels:',
            disabled=False
        )

        def get_pr_columns():
            try:
                colms = database.table_columns(tb_pr.value, 1, None)
                if colms is None:
                    return []
                else:
                    return colms
            except Exception:
                return []

        tc_id = Dropdown(
            options=get_pr_columns(),
            value=config.autoselect(
                values['ds_conf'][dsc_value]['years'][
                    str(ds_year.value)]['columns']['parcels_id'],
                get_pr_columns(), False),
            description='Parcels ID:',
            disabled=False,
            layout=Layout(width='180px')
        )
        tc_cn = Dropdown(
            options=get_pr_columns(),
            value=config.autoselect(
                values['ds_conf'][dsc_value]['years'][
                    str(ds_year.value)]['columns']['crop_names'],
                get_pr_columns(), False),
            description='Crop names:',
            disabled=False,
            layout=Layout(width='180px')
        )
        tc_cc = Dropdown(
            options=get_pr_columns(),
            value=config.autoselect(
                values['ds_conf'][dsc_value]['years'][
                    str(ds_year.value)]['columns']['crop_codes'],
                get_pr_columns(), False),
            description='Crop codes:',
            disabled=False,
            layout=Layout(width='180px')
        )

        def on_tb_pr_change(change):
            tc_id.options = get_pr_columns()
            tc_cn.options = get_pr_columns()
            tc_cc.options = get_pr_columns()
        tb_pr.observe(on_tb_pr_change, 'value')

        parcel_box = HBox([tb_pr, tc_id, tc_cn, tc_cc])

        tb_s2 = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['ds_conf'][dsc_value]['years'][
                    str(ds_year.value)]['tables']['s2'],
                get_tb_list(), False),
            description='S2 signatures:',
            disabled=False
        )
        tb_bs = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['ds_conf'][dsc_value]['years'][
                    str(ds_year.value)]['tables']['bs'],
                get_tb_list(), False),
            description='Backscattering:',
            disabled=False
        )
        tb_6c = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['ds_conf'][dsc_value]['years'][
                    str(ds_year.value)]['tables']['c6'],
                get_tb_list(), False),
            description='6 day coherence:',
            disabled=False
        )

        wb_save = Button(
            description='Save',
            disabled=False,
            icon='save'
        )

        @bt_get_center.on_click
        def bt_get_center_on_click(b):
            import json
            center_json = json.loads(
                database.getTableCentroid(tb_pr.value)['center'][0])
            map_cent_lat.value = round(center_json['coordinates'][1], 2)
            map_cent_lon.value = round(center_json['coordinates'][0], 2)
            map_zoom.value = 10

        @wb_save.on_click
        def wb_save_on_click(b):
            progress.clear_output()
            dscode = ds_code.value
            config.update(['ds_conf', dscode, 'years', str(ds_year.value),
                           'tables', 'dias_catalog'], str(tb_dc.value))
            config.update(['ds_conf', dscode, 'years', str(ds_year.value),
                           'tables', 'parcels'], str(tb_pr.value))
            config.update(['ds_conf', dscode, 'years', str(ds_year.value),
                           'columns', 'parcels_id'], str(tc_id.value))
            config.update(['ds_conf', dscode, 'years', str(ds_year.value),
                           'columns', 'crop_names'], str(tc_cn.value))
            config.update(['ds_conf', dscode, 'years', str(ds_year.value),
                           'columns', 'crop_codes'], str(tc_cc.value))
            config.update(['ds_conf', dscode, 'years', str(ds_year.value),
                           'tables', 's2'], str(tb_s2.value))
            config.update(['ds_conf', dscode, 'years', str(ds_year.value),
                           'tables', 'bs'], str(tb_bs.value))
            config.update(['ds_conf', dscode, 'years', str(ds_year.value),
                           'tables', 'c6'], str(tb_6c.value))
            config.update(['ds_conf', dscode,
                           'db'], str(ds_db.value))
            config.update(['ds_conf', dscode,
                           'desc'], str(ds_desc.value))
            config.update(['ds_conf', dscode, 'center'],
                          f"{map_cent_lat.value},{map_cent_lon.value}")
            config.update(['ds_conf', dscode,
                           'zoom'], str(map_zoom.value))
            config.update(['set', 'ds_conf'], str(dscode))
            config.update(['set', 'ds_year'], str(ds_year.value))
            values = config.read()
            ds_c = values['set']['ds_conf']
            ds_y = values['set']['ds_year']
            dsc.options = [d for d in values['ds_conf']]
            dsy.options = [int(y) for y in values['ds_conf'][ds_c]['years']]
            dsc.value = ds_c
            dsy.value = int(ds_y)
            outlog("The configurations are saved.")

        return VBox([info_config, ds_box, parcel_box,
                     tb_dc, tb_s2, tb_bs, tb_6c,
                     Label(''.join(info_map_text)), map_box, wb_save])

    dsc_new_box = HBox([])

    @bt_set.on_click
    def bt_set_on_click(b):
        if dsc_new_box.children == ():
            dsc_new_box.children = [dsc_config(dsc.value)]
            bt_set.icon = 'chevron-up'
        else:
            dsc_new_box.children = ()
            bt_set.icon = 'cogs'

    @bt_new.on_click
    def bt_new_on_click(b):
        if dsc_new_box.children == ():
            dsc_new_box.children = [dsc_config(dsc.value)]
            bt_set.icon = 'chevron-up'
        else:
            dsc_new_box.children = ()
            bt_set.icon = 'cogs'

    @bt_rec.on_click
    def bt_rec_on_click(b):
        progress.clear_output()
        if len(dsc.options) > 1:
            config.delete(['ds_conf', dsc.value])
            outlog(f"Dataset configuration '{dsc.value}' is deleted.")
            values = config.read()
            dsc.options = [d for d in values['ds_conf']]
        else:
            outlog("Can not remove last configuration.")

    @bt_rey.on_click
    def bt_rey_on_click(b):
        progress.clear_output()
        if len(dsy.options) > 1:
            config.delete(['ds_conf', dsc.value, 'years', str(dsy.value)])
            outlog(f"Year {dsy.value} of dataset '{dsc.value}' is deleted.")
            values = config.read()
            dsy.options = [int(y) for y in values['ds_conf']
                           [str(dsc.value)]['years']]
        else:
            outlog("Can not remove last configuration.")

    wbox = VBox([Label("Datasets configurations."), dsc_box,
                 dsc_new_box, progress])

    return wbox
