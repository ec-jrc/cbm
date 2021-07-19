#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from os.path import join, normpath
from ipywidgets import (Text, VBox, HBox, Label, Password, Button, Layout, Tab,
                        Output, Dropdown, FloatText, BoundedIntText, Combobox)

from cbm.utils import config, data_options
from cbm.datas import db, db_queries


def api(mode=None):
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
        progress.clear_output()
        config.set_value(['api', 'url'], str(wt_url.value).replace(' ', ''))
        config.set_value(['api', 'user'], str(wt_user.value).replace(' ', ''))
        if wt_pass.value != '':
            config.set_value(['api', 'pass'], str(
                wt_pass.value).replace(' ', ''))
        outlog("The RESTful API credentials are saved.")

    wbox = VBox([HBox([wt_url,
                       Label("Format: http://0.0.0.0/ or https://0.0.0.0/")]),
                 wt_user, wt_pass,
                 HBox([wb_save, progress])])

    return wbox


def direct():
    tab_box = Tab(children=[direct_conn(), direct_settings()])

    tab_box.set_title(0, 'Connection')
    tab_box.set_title(1, 'db Configuration')

    return tab_box


def direct_conn(db='main'):
    values = config.read()

    info_db = Label("Database connection settings.")

    db_host = Text(
        value=values['db'][db]['host'],
        placeholder='Database host',
        description='db Host:',
        disabled=False
    )
    db_port = Text(
        value=values['db'][db]['port'],
        placeholder='Database port',
        description='db Port:',
        disabled=False
    )
    db_name = Text(
        value=values['db'][db]['name'],
        placeholder='Database name',
        description='db Name:',
        disabled=False
    )
    db_user = Text(
        value=values['db'][db]['user'],
        placeholder='Database user',
        description='db User:',
        disabled=False
    )
    db_pass = Password(
        value=values['db'][db]['pass'],
        placeholder='******',
        description='db Pass:',
        disabled=False
    )

    info_os = Label("Object storage connection settings.")
    os_dias = Dropdown(
        options=['EOSC', 'CREODIAS', 'SOBLOO', 'MUNDI', 'ONDA', 'WEKEO', ''],
        value=values['s3']['dias'],
        description='DIAS:',
        disabled=False,
    )
    os_host = Text(
        value=values['s3']['host'],
        placeholder='Storage host',
        description='s3 Host:',
        disabled=False
    )
    os_bucket = Text(
        value=values['s3']['bucket'],
        placeholder='Bucket name',
        description='Bucket name:',
        disabled=False
    )
    os_access_key = Text(
        value=values['s3']['access_key'],
        placeholder='Access key',
        description='Access Key:',
        disabled=False
    )
    os_secret_key = Password(
        value=values['s3']['secret_key'],
        placeholder='Secret key',
        description='Secret Key:',
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
        progress.clear_output()
        # Save database connection information
        config.set_value(['db', db, 'host'], str(db_host.value))
        config.set_value(['db', db, 'port'], str(db_port.value))
        config.set_value(['db', db, 'name'], str(db_name.value))
        config.set_value(['db', db, 'user'], str(db_user.value))
        config.set_value(['db', db, 'pass'], str(db_pass.value))
        # Save Object storage connection information
        config.set_value(['s3', 'dias'], str(os_dias.value))
        config.set_value(['s3', 'host'], str(os_host.value))
        config.set_value(['s3', 'bucket'], str(os_bucket.value))
        config.set_value(['s3', 'access_key'], str(os_access_key.value))
        config.set_value(['s3', 'secret_key'], str(os_secret_key.value))

        outlog("All changes are saved.")

    wbox = VBox([info_db, db_host, db_port, db_name, db_user, db_pass,
                 info_os, os_dias, os_host, os_bucket, os_access_key,
                 os_secret_key, wb_save, progress])

    return wbox


def direct_settings():
    values = config.read()
    ds_def = values['set']['dataset']
    # ds_dye = values['set']['ds_year']
    if ds_def not in [d for d in values['dataset']]:
        ds_def = [d for d in values['dataset']][0]

    dsc = Dropdown(
        options=[d for d in values['dataset']],
        value=ds_def,
        description='Default:',
        disabled=False,
        layout=Layout(width='200px')
    )

    btn_refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh')

    @btn_refresh.on_click
    def btn_refresh_on_click(b):
        values = config.read()
        ds_c = values['set']['dataset']
        dsc.options = [d for d in values['dataset']]
        dsc.value = ds_c

    def on_dsc_change(change):
        config.set_value(['set', 'dataset'], dsc.value)
    dsc.observe(on_dsc_change, 'value')

    bt_set = Button(layout=Layout(width='40px'), icon='cogs',
                    tooltip="Configure this dataset")
    bt_new = Button(layout=Layout(width='40px'), icon='plus',
                    tooltip="Add new dataset configuration")
    bt_del = Button(layout=Layout(width='40px'), icon='trash-alt',
                    tooltip='Delete dataset configuration')
    dsc_box = HBox([dsc, btn_refresh, bt_del, bt_set, bt_new])

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    def dsc_config(dsc_value):
        values = config.read()
        ds_db = Dropdown(
            options=list(values['db'].keys()),
            value="main",
            description='Database:',
            disabled=False,
            layout=Layout(width='200px')
        )

        try:
            with open(normpath(join(f"{values['paths']['temp']}", 'tb_prefix')),
                      'r') as f:
                code_value = f.read().split('_')[0]
        except Exception:
            code_value = dsc_value.split('_')[0]

        ds_code = Combobox(
            value=code_value,
            placeholder='abc',
            options=[m for m in data_options.eu_ms()] + [''],
            description='AOI code:',
            ensure_option=False,
            disabled=False,
            layout=Layout(width='200px'),
            tooltip='Lowercase AOI code name for the dataset (5chr max).'
        )
        ds_year = BoundedIntText(
            value=int(dsc_value.split('_')[1]),
            min=1980,
            max=2100,
            step=1,
            description='Dataset year:',
            disabled=False,
            layout=Layout(width='180px')

        )
        ds_desc = Text(
            value=values['dataset'][dsc_value]['description'],
            description='Description:',
            disabled=False
        )

        info_map_text = ["Set default map view options. ",
                         "You can get automatically the dataset ",
                         "center coordinates."]

        lat, lon = values['dataset'][dsc_value]['center'].split(",")
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
            value=values['dataset'][dsc_value]['zoom'],
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

        ds_box = HBox([ds_code, ds_year, ds_desc, ds_db])
        map_box = HBox([Label("Map center: "), map_cent_lat,
                        map_cent_lon, bt_get_center, map_zoom])

        info_config = Label(
            """Change 'AOI code' or 'Year' value to create a new configuration set or
            leave the same 'AOI code' value to configure the selected one.""")

        db_set = values['dataset'][dsc_value]['db']

        def get_tb_list():
            tbls = db.tables(db_set, None, False)
            if tbls is None:
                return []
            else:
                return tbls

        tb_dc = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['dataset'][dsc_value]['tables']['dias_catalog'],
                get_tb_list(), False),
            description='DIAS catalog:',
            disabled=False
        )
        tb_pr = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['dataset'][dsc_value]['tables']['parcels'],
                get_tb_list(), False),
            description='Parcels:',
            disabled=False
        )

        def get_pr_columns():
            try:
                colms = db.table_columns(tb_pr.value, ds_db.value, None)
                if colms is None:
                    return []
                else:
                    return colms
            except Exception:
                return []

        tc_id = Dropdown(
            options=get_pr_columns(),
            value=config.autoselect(
                values['dataset'][dsc_value]['pcolumns']['parcels_id'],
                get_pr_columns(), False),
            description='Parcels ID:',
            disabled=False,
            layout=Layout(width='180px')
        )
        tc_cn = Dropdown(
            options=get_pr_columns(),
            value=config.autoselect(
                values['dataset'][dsc_value]['pcolumns']['crop_names'],
                get_pr_columns(), False),
            description='Crop names:',
            disabled=False,
            layout=Layout(width='180px')
        )
        tc_cc = Dropdown(
            options=get_pr_columns(),
            value=config.autoselect(
                values['dataset'][dsc_value]['pcolumns']['crop_codes'],
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

        tb_s2 = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['dataset'][dsc_value]['tables']['s2'],
                get_tb_list(), False),
            description='S2 signatures:',
            disabled=False
        )
        tb_bs = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['dataset'][dsc_value]['tables']['bs'],
                get_tb_list(), False),
            description='Backscattering:',
            disabled=False
        )
        tb_6c = Dropdown(
            options=get_tb_list(),
            value=config.autoselect(
                values['dataset'][dsc_value]['tables']['c6'],
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
                db_queries.getTableCentroid(tb_pr.value)['center'][0])
            map_cent_lat.value = round(center_json['coordinates'][1], 2)
            map_cent_lon.value = round(center_json['coordinates'][0], 2)
            map_zoom.value = 10

        @wb_save.on_click
        def wb_save_on_click(b):
            progress.clear_output()
            dscode = ds_code.value
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'tables', 'dias_catalog'], str(tb_dc.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'tables', 'parcels'], str(tb_pr.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'pcolumns', 'parcels_id'], str(tc_id.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'pcolumns', 'crop_names'], str(tc_cn.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'pcolumns', 'crop_codes'], str(tc_cc.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'tables', 's2'], str(tb_s2.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'tables', 'bs'], str(tb_bs.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'tables', 'c6'], str(tb_6c.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'db'], str(ds_db.value))
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'description'], str(ds_desc.value))
            config.set_value(
                ['dataset', f'{dscode}_{str(ds_year.value)}', 'center'],
                f"{map_cent_lat.value},{map_cent_lon.value}")
            config.set_value(['dataset', f'{dscode}_{str(ds_year.value)}',
                              'zoom'], str(map_zoom.value))
            config.set_value(['set', 'dataset'],
                             f'{dscode}_{str(ds_year.value)}')
            config.set_value(['set', 'ds_year'], str(ds_year.value))
            values = config.read()
            ds_c = values['set']['dataset']
            dsc.options = [d for d in values['dataset']]
            dsc.value = ds_c
            outlog("The configurations are saved.")

        db_box = HBox([VBox([Label('Tables:'),
                             tb_pr, tb_dc, tb_s2, tb_bs, tb_6c]),
                       VBox([Label('Columns:'),
                             HBox([tc_id, tc_cn, tc_cc])])])

        return VBox([info_config, ds_box, db_box,
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

    @bt_del.on_click
    def bt_del_on_click(b):
        progress.clear_output()
        if len(dsc.options) > 1:
            config.delete(['dataset', dsc.value])
            outlog(f"Dataset configuration '{dsc.value}' is deleted.")
            values = config.read()
            dsc.options = [d for d in values['dataset']]
        else:
            outlog("Can not remove last configuration.")

    wbox = VBox([Label("Datasets configurations."), dsc_box,
                 dsc_new_box, progress])

    return wbox
