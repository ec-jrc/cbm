#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


# Get parcels data
import os
import json
import datetime
import pandas as pd
from os.path import join, normpath, dirname
from IPython.display import display
from ipywidgets import (Text, Textarea, Label, HBox, VBox, Dropdown,
                        ToggleButtons, ToggleButton, Layout, Output,
                        Button, DatePicker, RadioButtons, IntSlider,
                        Box, HTML, SelectMultiple)

from cbm.utils import config, data_options
from cbm.ipycbm.ipy_get import get_maps
from cbm.get import time_series, parcel_info


def get():
    """Get the parcel's dataset for the given location or ids"""
    debug = False
    info = Label("1. Select the aoi to get parcel data.")

    values = config.read()
    ppoly_out = Output()
    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    def outlog_poly(*text):
        with ppoly_out:
            print(*text)

    def aois_options():
        values = config.read()
        options = {}
        if values['set']['data_source'] == 'api':
            api_values = config.read('api_options.json')
            for aoi in api_values['aois']:
                options[(aoi.upper(), aoi)] = api_values['aois'][aoi]['years']
        elif values['set']['data_source'] == 'direct':
            values = config.read('api_options.json')
            for aoi in values['dataset']:
                options[(f"{aoi.upper()} ({aoi})", aoi)] = [aoi.split('_')[-1]]
        return options

    def aois_years():
        values = config.read()
        years = {}
        if values['set']['data_source'] == 'api':
            api_values = config.read('api_options.json')
            for aoi in api_values['aois']:
                years[aoi] = api_values['aois'][aoi]['years']
        elif values['set']['data_source'] == 'direct':
            values = config.read()
            for aoi in values['dataset']:
                years[aoi] = [aoi.split('_')[-1]]
        return years

    try:
        aois = Dropdown(
            options=tuple(aois_options()),
            value=values['set']['dataset'],
            description='AOI:',
        )
    except Exception:
        aois = Dropdown(
            options=tuple(aois_options()),
            description='AOI:',
        )

    def years_disabled():
        values = config.read()
        if values['set']['data_source'] == 'direct':
            return True
        else:
            return False

    year = Dropdown(
        options=next(iter(aois_options().values())),
        description='Year:',
        disabled=years_disabled(),
    )
    button_refresh = Button(layout=Layout(width='35px'),
                            icon='fa-refresh')

    @button_refresh.on_click
    def button_refresh_on_click(b):
        values = config.read()
        if values['set']['data_source'] == 'api':
            from cbm.datas import api
            available_options = json.loads(api.get_options())
            try:
                api_options = normpath(join(config.path_conf,
                                            'api_options.json'))
                os.makedirs(dirname(api_options), exist_ok=True)
                with open(api_options, "w") as f:
                    json.dump(available_options, f, indent=4)
                outlog(f"File saved at: {api_options}")
            except Exception as err:
                outlog(f"Could not create the file 'api_options.json': {err}")

            outlog(f"The API options are updated.")
        aois.options = tuple(aois_options())
        year.options = aois_years()[aois.value]
        year.disabled = years_disabled()

    def table_options_change(change):
        api_values = config.read('api_options.json')
        id_examples = api_values['aois'][change.new]['id_examples']
        try:
            id_examples_label.value = ', '.join(str(x) for x in id_examples)
            year.options = aois_years()[change.new]
            year.disabled = years_disabled()
            pid.value = str(id_examples[0])
        except Exception:
            id_examples_label.value = ', '.join(str(x) for x in id_examples)
            aois.options = tuple(aois_options())
            year.options = aois_years()[aois.value]
            year.disabled = years_disabled()
            pid.value = str(id_examples[0])
    aois.observe(table_options_change, 'value')

    info_method = Label("2. Select a method to download parcel data.")

    method = ToggleButtons(
        options=[('Parcel ID', 2),
                 ('Coordinates', 1),
                 ('Map marker', 3),
                 ('Polygon', 4)],
        value=None,
        description='',
        disabled=False,
        button_style='info',
        tooltips=['Enter lon lat', 'Enter parcel ID',
                  'Select a point on a map', 'Get parcels id in a polygon'],
    )

    plon = Text(value='5.664', placeholder='Add lon', description='Lon:')
    plat = Text(value='52.694', placeholder='Add lat', description='Lat:')
    wbox_lat_lot = VBox(children=[plat, plon])

    api_values = config.read('api_options.json')
    id_examples = api_values['aois'][aois.value]['id_examples']

    id_examples_label = Label(', '.join(str(x) for x in id_examples))
    info_pid = HBox([Label("Multiple parcel ids can be added, e.g.: "),
                     id_examples_label])

    pid = Textarea(
        value=str(id_examples[0]),
        placeholder='12345, 67890',
        description='Parcel(s) ID:',
    )

    wbox_pids = VBox(children=[info_pid, pid])

    bt_get_ids = Button(
        description="Find parcels",
        disabled=False,
        button_style='info',
        tooltip='Find parcels within the polygon.',
        icon=''
    )

    get_ids_box = HBox([bt_get_ids, Label(
        "Find the parcels that are in the polygon.")])

    @bt_get_ids.on_click
    def bt_get_ids_on_click(b):
        with ppoly_out:
            try:
                # get_requests = data_source()
                ppoly_out.clear_output()
                polygon = get_maps.polygon_map.feature_collection[
                    'features'][-1]['geometry']['coordinates'][0]
                polygon_str = '-'.join(['_'.join(map(str, c))
                                        for c in polygon])
                outlog_poly(f"Geting parcel ids within the polygon...")
                polyids = parcel_info.by_polygon(
                    aois.value, year.value, polygon_str, ptype.value,
                    False, True)
                outlog_poly(
                    f"'{len(polyids['ogc_fid'])}' parcels where found:")
                outlog_poly(polyids['ogc_fid'])
                file = normpath(join(config.get_value(['paths', 'temp']),
                                     'pids_from_polygon.txt'))
                with open(file, "w") as text_file:
                    text_file.write('\n'.join(map(str, polyids['ogc_fid'])))
            except Exception as err:
                outlog("No parcel ids found:", err)

    method_out = Output(layout=Layout(border='1px solid black'))

    def method_options(obj):
        with method_out:
            method_out.clear_output()
            if obj['new'] == 1:
                display(wbox_lat_lot)
            elif obj['new'] == 2:
                display(wbox_pids)
            elif obj['new'] == 3:
                display(get_maps.base_map(
                    aois.value, config.get_value(['set', 'data_source'])))
            elif obj['new'] == 4:
                display(VBox([get_maps.polygon(aois.value, config.get_value(
                        ['set', 'data_source'])),
                    get_ids_box, ppoly_out]))

    method.observe(method_options, 'value')

    info_type = Label("3. Select datasets to download.")

    ptype = Text(
        value=None,
        placeholder='(Optional) Parcel Type',
        description='pType:',
        disabled=False
    )

    table_options = HBox([aois, button_refresh, ptype, year])

    # ########### Time series options #########################################
    pts_bt = ToggleButton(
        value=False,
        description='Time series',
        button_style='success',  # success
        tooltip='Get parcel information',
        icon='toggle-off',
        layout=Layout(width='50%')
    )

    pts_bands = data_options.pts_bands()

    pts_tstype = SelectMultiple(
        options=[
            ("Sentinel-2 Level 2A", 's2'),
            ("S1 Backscattering Coefficients", 'bs'),
            ("S1 6-day Coherence (20m)", 'c6')
        ],
        value=['s2'],
        rows=3,
        description='TS type:',
        disabled=False,
    )

    pts_band = Dropdown(
        options=list(pts_bands['s2']),
        value='',
        description='Band:',
        disabled=False,
    )

    def pts_tstype_change(change):
        if len(pts_tstype.value) <= 1:
            pts_band.disabled = False
            try:
                pts_b = change.new[0]
                pts_band.options = pts_bands[pts_b]
            except Exception:
                pass
        else:
            pts_band.value = ''
            pts_band.disabled = True

    pts_tstype.observe(pts_tstype_change, 'value')

    pts_options = VBox(children=[pts_tstype, pts_band])

    # ########### Chip images options #########################################
    pci_bt = ToggleButton(
        value=False,
        description='Chip images',
        disabled=False,
        button_style='success',
        tooltip='Get parcel information',
        icon='toggle-off',
        layout=Layout(width='50%')
    )

    pci_start_date = DatePicker(
        value=datetime.date(2020, 6, 1),
        description='Start Date',
    )

    pci_end_date = DatePicker(
        value=datetime.date(2020, 6, 30),
        description='End Date',
    )

    pci_plevel = RadioButtons(
        options=['LEVEL2A', 'LEVEL1C'],
        value='LEVEL2A',
        description='Proces. level:',  # Processing level
        disabled=False,
        layout=Layout(width='50%')
    )

    pci_chipsize = IntSlider(
        value=640,
        min=100,
        max=5120,
        step=10,
        description='Chip size:',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='d'
    )

    pci_bands = data_options.pci_bands()

    pci_satellite = RadioButtons(
        options=list(pci_bands),
        value='Sentinel 2',
        disabled=True,
        layout=Layout(width='100px')
    )

    pci_band = SelectMultiple(
        options=list(pci_bands['Sentinel 2']),
        value=['B04'],
        rows=11,
        description='Band:',
        disabled=False
    )

    sats_plevel = HBox([pci_satellite, pci_plevel])

    def on_sat_change(change):
        sat = change.new
        pci_band.options = pci_bands[sat]

    pci_satellite.observe(on_sat_change, 'value')

    pci_options = VBox(children=[pci_start_date, pci_end_date,
                                 sats_plevel, pci_chipsize,
                                 pci_band])

    # ########### General options #############################################
    pts_wbox = VBox(children=[])
    pci_wbox = VBox(children=[])

    def pts_observe(button):
        if button['new']:
            pts_bt.icon = 'toggle-on'
            pts_wbox.children = [pts_options]
        else:
            pts_bt.icon = 'toggle-off'
            pts_wbox.children = []

    def pci_observe(button):
        if button['new']:
            pci_bt.icon = 'toggle-on'
            pci_wbox.children = [pci_options]
        else:
            pci_bt.icon = 'toggle-off'
            pci_wbox.children = []

    pts_bt.observe(pts_observe, names='value')
    pci_bt.observe(pci_observe, names='value')

    pts = VBox(children=[pts_bt, pts_wbox], layout=Layout(width='40%'))
    pci = VBox(children=[pci_bt, pci_wbox], layout=Layout(width='40%'))

    data_types = HBox(children=[pts, pci])

    info_get = Label("4. Download the selected data.")

    bt_get = Button(
        description='Download',
        button_style='warning',
        tooltip='Send the request',
        icon='download'
    )

    path_temp = config.get_value(['paths', 'temp'])
    path_data = config.get_value(['paths', 'data'])

    info_paths = HTML("".join([
        "<style>div.c {line-height: 1.1;}</style>",
        "<div class='c';>By default data will be stored in the temp folder ",
        f"({path_temp}), you will be asked to empty the temp folder each time ",
        "you start the notebook.<br>In your personal data folder ",
        f"({path_data}) you can permanently store the data.</div>"]))

    paths = RadioButtons(
        options=[(f"Temporary folder: '{path_temp}'.", path_temp),
                 (f"Personal data folder: '{path_data}'.", path_data)],
        layout={'width': 'max-content'},
        value=path_temp
    )

    paths_box = Box([Label(value="Select folder:"), paths])

    def file_len(fname):
        with open(fname) as f:
            for i, l in enumerate(f):
                pass
        return i + 1

    def get_data(parcel):
        get_requests = data_source()
        pid = str(parcel['pid'][0])
        source = config.get_value(['set', 'data_source'])
        if source == 'api':
            datapath = normpath(
                join(paths.value, aois.value, year.value, pid))
        elif source == 'direct':
            dataset = config.get_value(['set', 'dataset'])
            datapath = normpath(join(paths.value, dataset, pid))
        file_pinf = normpath(join(datapath, 'info.json'))
        os.makedirs(dirname(file_pinf), exist_ok=True)
        with open(file_pinf, "w") as f:
            json.dump(parcel, f)
        outlog(f"File saved at: {file_pinf}")

        if pts_bt.value is True:
            outlog(f"Getting time series for parcel: '{pid}',",
                   f"({pts_tstype.value} {pts_band.value}).")
            for pts in pts_tstype.value:
                ts = time_series.by_pid(aois.value, year.value, pid, pts,
                                        ptype.value, pts_band.value)
                band = ''
                if pts_band.value != '':
                    band = f"_{pts_band.value}"
                file_ts = normpath(join(datapath,
                                        f'time_series_{pts}{band}.csv'))
                if isinstance(ts, pd.DataFrame):
                    ts.to_csv(file_ts, index=True, header=True)
                elif isinstance(ts, dict):
                    os.makedirs(os.path.dirname(file_ts), exist_ok=True)
                    df = pd.DataFrame.from_dict(ts, orient='columns')
                    df.to_csv(file_ts, index=True, header=True)
            outlog("TS Files are saved.")
        if pci_bt.value is True:
            files_pci = normpath(join(datapath, 'chip_images'))
            outlog(f"Getting '{pci_band.value}' chip images for parcel: {pid}")
            with progress:
                get_requests.rcbl(parcel, pci_start_date.value,
                                  pci_end_date.value, pci_band.value,
                                  pci_chipsize.value, files_pci)
            filet = normpath(join(datapath, 'chip_images',
                                  f'images_list.{pci_band.value[0]}.csv'))
            if file_len(filet) > 1:
                outlog(f"Completed, all GeoTIFFs for bands '{pci_band.value}' are ",
                       f"downloaded in the folder: '{datapath}/chip_images'")
            else:
                outlog("No files where downloaded, please check your configurations")

    def get_from_location(lon, lat):
        outlog(f"Finding parcel information for coordinates: {lon}, {lat}")
        parcel = parcel_info.by_location(aois.value, year.value, lon, lat,
                                         ptype.value, True, False, debug)
        pid = str(parcel['pid'][0])
        outlog(f"The parcel '{pid}' was found at this location.")
        try:
            get_data(parcel)
        except Exception as err:
            print(err)

    def get_from_id(pids):
        outlog(f"Getting parcels information for: '{pids}'")
        for pid in pids:
            try:
                parcel = parcel_info.by_pid(aois.value, year.value, pid,
                                            ptype.value, True, False, debug)
                get_data(parcel)
            except Exception as err:
                print(err)

    @bt_get.on_click
    def bt_get_on_click(b):
        progress.clear_output()
        if method.value == 1:
            try:
                with progress:
                    lon, lat = plon.value, plat.value
                    get_from_location(lon, lat)
            except Exception as err:
                outlog("Could not get parcel information for location",
                       f"'{lon}', '{lat}': {err}")

        elif method.value == 2:
            try:
                with progress:
                    pids = pid.value.replace(" ", "").split(",")
                    get_from_id(pids)
            except Exception as err:
                outlog(f"Could not get parcel information: {err}")

        elif method.value == 3:
            try:
                marker = get_maps.base_map.map_marker
                lon = str(round(marker.location[1], 2))
                lat = str(round(marker.location[0], 2))
                get_from_location(lon, lat)
            except Exception as err:
                outlog(f"Could not get parcel information: {err}")
        elif method.value == 4:
            try:
                plimit = int(values['set']['plimit'])
                file = normpath(join(config.get_value(['paths', 'temp']),
                                     'pids_from_polygon.txt'))
                with open(file, "r") as text_file:
                    pids = text_file.read().split('\n')
                outlog("Geting data form the parcels:")
                outlog(pids)
                if len(pids) <= plimit:
                    get_from_id(pids)
                else:
                    outlog("You exceeded the maximum amount of selected parcels ",
                           f"({plimit}) to get data. Please select smaller area.")
            except Exception as err:
                outlog("No pids file found.", err)
        else:
            outlog(f"Please select method to get parcel information.")

    return VBox([info, table_options, info_method, method,
                 method_out, info_type, data_types, info_get, info_paths,
                 paths_box, bt_get, progress])


def data_source():
    source = config.get_value(['set', 'data_source'])
    if source == 'api':
        from cbm.datas import api
        return api
    elif source == 'direct':
        from cbm.datas import direct
        return direct


def error_check(err):
    from cbm.utils import check
    check.error(err)
