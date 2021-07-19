#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import glob
from os.path import normpath, join
from ipywidgets import (Text, Label, HBox, VBox, Layout, Tab, Dropdown,
                        Output, Button, FileUpload, Checkbox, DatePicker)

from cbm.utils import config
from cbm.datas import db
from cbm.extract import db_tables

from cbm.extract import (pgS2Extract, pgS1bsExtract)


def upload_shp(path_data, config_path=False):
    # Upload
    l_up = Label("a. Upload .shp to the server.")
    accept_files = ".shp, .cpg, .dbf, .prj, .shx, .sbn, .sbx, .xml"
    data_path = config.get_value(['paths', 'temp'])
    shp_dist_folder = Text(
        value=normpath(join(path_data, 'vector')),
        placeholder='tmp/',
        description='Folder:',
        disabled=config_path
    )
    shp_select = FileUpload(
        description='Select files:',
        icon='plus',
        accept=accept_files,
        multiple=True  # True to accept multiple files upload else False
    )
    shp_clear = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Clear selections.',
        icon='broom',
        layout=Layout(width='40px')
    )
    shp_upload = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Upload foi reference data (.shp).',
        icon='fa-upload',
        layout=Layout(width='40px')
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    @shp_clear.on_click
    def shp_clear_on_click(b):
        shp_select.value.clear()
        shp_select._counter = 0

    @shp_upload.on_click
    def shp_upload_on_click(b):
        progress.clear_output()
        os.makedirs(shp_dist_folder.value, exist_ok=True)
        for key in shp_select.value:
            content = shp_select.value[key]['content']
            with open(normpath(join(shp_dist_folder.value, key)), 'wb') as f:
                f.write(content)
        outlog("All files are uploaded.")
        shp_select.value.clear()
        shp_select._counter = 0

    shp_box = HBox([shp_dist_folder, shp_select, shp_clear, shp_upload])

    # Import the .shp to the database
    l_imp = Label("""b. Import uploaded .shp to the database. Add a short name,
        max 15 characters for the parcels table e.g.:escat2020.""")
    imp_select = Dropdown(
        options=[s for s in glob.glob(normpath(join(shp_dist_folder.value,
                                                    '*'))) if '.shp' in s],
        description='Select .shp:',
        disabled=False
    )
    imp_refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh'
    )
    imp_proc = Button(
        description='Import .shp file',
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Run',
        icon='fa-database',
    )
    imp_truncate = Checkbox(
        value=False,
        description='Remove old entries',
        disabled=False
    )

    try:
        with open(normpath(join(data_path, 'tb_prefix')), 'r') as f:
            name_from_prfix = f.read()
    except Exception:
        name_from_prfix = None
    imp_tb_name = Text(
        value=name_from_prfix,
        placeholder='ms2010',
        description='Table name:',
        tooltip='A short name max 10 char.',
        disabled=False
    )

    def on_imp_tb_name(change):
        with open(normpath(join(data_path, 'tb_prefix')), 'w+') as f:
            f.write(imp_tb_name.value)
    imp_tb_name.observe(on_imp_tb_name, 'value')

    @imp_proc.on_click
    def imp_proc_on_click(b):
        if imp_tb_name is not None:
            import subprocess
            progress.clear_output()
    #         tb_name = imp_select.value.split('/')[-1].split('.')[0]
            tb_name = imp_tb_name.value.replace(' ', '').lower()[:15]

            outlog("Importing .shp to database...")
            command = ['ogr2ogr', '-f', 'PostgreSQL',
                       'PG:' + db.conn_str(), '-nln',
                       tb_name, '-nlt', 'PROMOTE_TO_MULTI', '-nlt', 'GEOMETRY',
                       imp_select.value]
            if imp_truncate.value is True:
                command.extend(['--config', 'OGR_TRUNCATE', 'YES'])
            if subprocess.call(command) == 0:
                progress.clear_output()
                outlog(f"Completed. Total number of rows in table '{tb_name}':",
                       db.exact_count(tb_name))
            else:
                outlog("Could not import shp file.")
        else:
            outlog(
                "Please add a name for the parcels table (MAX 15 char e.g.: escat2020).")

    @imp_refresh.on_click
    def imp_refresh_on_click(b):
        imp_select.options = [
            s for s in glob.glob(f'{shp_dist_folder.value}/*'
                                 ) if '.shp' in s]

    imp_box = HBox(
        [imp_tb_name, imp_select, imp_refresh, imp_proc, imp_truncate])

    return VBox([l_up, shp_box, l_imp, imp_box, progress])


def create_tables():
    """Create essential cbm tables
    """
    data_path = config.get_value(['paths', 'temp'])
    l_tb = Label("""Add a short name as prefix for the tables,
        max 15 characters e.g.:escat2020.""")
    try:
        with open(normpath(join(data_path, 'tb_prefix')), 'r') as f:
            prefix = f.read()
    except Exception:
        prefix = ''

    tb_prefix = Text(
        value=prefix,
        placeholder='xx2010',
        description='Table prefix:',
        disabled=False
    )

    checkboxes = {}
    tbs = db_tables.tables_dict()
    for key in tbs:
        checkboxes[key] = Checkbox(
            value=True,
            description=tbs[key]['name'],
            disabled=False,
            indent=False,
            layout=Layout(width='150px')
        )
    checkboxes["aois"].value = False
    check_box = HBox([checkboxes[t] for t in checkboxes])

    bt_create_tb = Button(
        description='Create tables',
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Creat tables',
        icon='fa-table'
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    def on_tb_prefix(change):
        with open(normpath(join(data_path, 'tb_prefix')), 'w+') as f:
            f.write(tb_prefix.value.replace(' ', '').lower()[:15])
    tb_prefix.observe(on_tb_prefix, 'value')

    @bt_create_tb.on_click
    def bt_create_tb_on_click(b):
        progress.clear_output()
        tb_prefix_clean = tb_prefix.value.replace(' ', '').lower()[:15]
        if tb_prefix.value != '':
            for key in tbs:
                if checkboxes[key].value is True:
                    if db.tb_exist(
                            f"{tb_prefix_clean}_{tbs[key]['table']}") is False:
                        sql = tbs[key]['sql'].replace(
                            '\n', '').replace('  ', '')
                        db.execute_sql(sql.format(tb_prefix_clean))
                        outlog(
                            f"The table {tb_prefix_clean}_{tbs[key]['table']} is created..")
                    else:
                        outlog(
                            f"The table {tb_prefix_clean}_{tbs[key]['table']} already exist.")
        else:
            outlog("Please add tables prefix.")

    wbox = VBox([l_tb, tb_prefix, check_box, bt_create_tb, progress])

    return wbox


def extraction():
    start = DatePicker(
        description='Start date:',
        disabled=False
    )
    end = DatePicker(
        description='End date:',
        disabled=False
    )
    dates = HBox([start, end])
    bt_sig_s2 = Button(
        description='Sentinel 2',
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Run Sentinel 2 extraction',
        icon='fa-play'
    )
    bt_sig_bs = Button(
        description='S1 Backscattering',
        value=False,
        disabled=True,
        button_style='info',
        tooltip='Run S1 Backscattering extraction',
        icon='fa-play'
    )
    bt_sig_c6 = Button(
        description='S1 6-day coherence',
        value=False,
        disabled=True,
        button_style='info',
        tooltip='Run S1 6-day coherence extraction',
        icon='fa-play'
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    bt_sg_box = VBox([bt_sig_s2, bt_sig_bs, bt_sig_c6])

    tab_box = Tab(children=[bt_sg_box, Text()])

    tab_box.set_title(0, 'Procedures')
    tab_box.set_title(1, 'VM Workers config')

    @bt_sig_s2.on_click
    def bt_sig_s2_on_click(b):
        progress.clear_output()
        with progress:
            try:
                delta = end.value - start.value
                for d in range(delta.days):
                    pgS2Extract.main(start.value, end.value)
            except Exception as err:
                outlog(err)

    @bt_sig_bs.on_click
    def bt_sig_bs_on_click(b):
        progress.clear_output()
        with progress:
            try:
                delta = end.value - start.value
                for d in range(delta.days):
                    pgS1bsExtract.extractS1bs(start.value, end.value)
            except Exception as err:
                outlog(err)

    @bt_sig_c6.on_click
    def bt_sig_c6_on_click(b):
        progress.clear_output()
        with progress:
            outlog(
                "6-day coherence extraction not yet available please check for updates.")

    return VBox([dates, bt_sg_box, progress])
