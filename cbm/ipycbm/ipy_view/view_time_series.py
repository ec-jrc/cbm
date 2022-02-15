#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (HBox, VBox, Dropdown, Button, Output, Checkbox)
from os.path import join, normpath

from cbm.utils import config, data_options
from cbm.show import time_series
import json
import glob


def time_series_widget(aoi, year, pid):

    path = normpath(join(config.get_value(['paths', 'temp']),
                         aoi, str(year), str(pid)))
    # confvalues = config.read()
    # inst = confvalues['set']['institution']
    file_info = normpath(join(path, 'info.json'))

    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())
    pid = info_data['pid'][0]

    ts_cloud = Checkbox(
        value=True,
        description='Cloud free',
        disabled=False,
        indent=False
    )

    ts_files = glob.glob(normpath(join(path, '*time_series*.csv')))
    ts_file_types = [b.split('_')[-1].split('.')[0] for b in ts_files]
    if 's2' in ts_file_types:
        ts_file_types.append('ndvi')
    ts_types = [t for t in data_options.pts_tstype() if t[1] in ts_file_types]

    ts_type = Dropdown(
        options=ts_types,
        description='Select type:',
        disabled=False,
    )

    btn_ts = Button(
        value=False,
        description='Plot TS',
        disabled=False,
        button_style='info',
        tooltip='Refresh output',
        icon=''
    )

    ts_out = Output()

    @btn_ts.on_click
    def btn_ts_on_click(b):
        btn_ts.description = 'Refresh'
        btn_ts.icon = 'refresh'
        with ts_out:
            ts_out.clear_output()
            if ts_type.value == 's2':
                time_series.s2(aoi, str(year), str(pid), bands=['B4', 'B8'])
            elif ts_type.value == 'ndvi':
                time_series.ndvi(aoi, str(year), str(pid))
            elif ts_type.value == 'bs':
                time_series.s1(aoi, str(year), str(pid), 'bs')
            elif ts_type.value == 'c6':
                time_series.s1(aoi, str(year), str(pid), 'c6')

    def on_ts_type_change(change):
        if ts_type.value == 's2':
            wbox_ts.children = [btn_ts, ts_type]
        else:
            wbox_ts.children = [btn_ts, ts_type]

    ts_type.observe(on_ts_type_change, 'value')

    wbox_ts = HBox([btn_ts, ts_type, ts_cloud])

    wbox = VBox([wbox_ts, ts_out])

    return wbox
