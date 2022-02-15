#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import shutil
from glob import glob
from IPython.display import display
from os.path import join, normpath, isdir
from ipywidgets import (Label, VBox, HBox, Layout, Dropdown,
                        ToggleButtons, Output, Box, RadioButtons, Button)

from cbm.utils import config
from cbm.ipycbm.ipy_view import (view_map, view_grid, view_time_series,
                                 view_code, view_notes)

from cbm.ipycbm.ipy_get import get_panel


def view():

    temppath = config.get_value(['paths', 'temp'])
    datapath = config.get_value(['paths', 'data'])

    paths = RadioButtons(
        options=[(f"Temporary folder: '{temppath}'.", temppath),
                 (f"Personal data folder: '{datapath}'.", datapath)],
        layout={'width': 'max-content'},
        value=temppath
    )

    paths_box = Box([Label(value="Select folder:"), paths])

    select_aoi = Dropdown(
        options=[d.split('/')[-2] for d in glob(f"{paths.value}/*/")],
        value=None,
        description='Select tabe:',
        disabled=False,
    )

    select_year = Dropdown(
        options=[],
        value=None,
        description='Select year:',
        disabled=False,
    )

    button_refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh')

    select_option_box = HBox([select_aoi, button_refresh])

    selection_single = Dropdown(
        options=[],
        value=None,
        description='Select parcel:',
        disabled=False,
    )

    view_source = ToggleButtons(
        options=[('From local folder', 0), ('Download new data', 1)],
        value=0,
        description='',
        disabled=False,
        button_style='success',
        tooltips=[],
    )

    view_method = ToggleButtons(
        options=[],
        value=None,
        description='',
        disabled=False,
        button_style='info',
        tooltips=[],
    )

    rm_parcel = Button(
        value=False,
        disabled=False,
        button_style='danger',
        tooltip='Delete parcel data.',
        icon='trash',
        layout=Layout(width='35px')
    )
    source_box = VBox([])

    def on_source_change(obj):
        if view_source.value == 1:
            source_box.children = [get_panel.get()]
        else:
            source_box.children = []

    view_source.observe(on_source_change, 'value')

    code_info = Label()
    single_box = HBox([select_year, selection_single, rm_parcel])
    select_box = Box([single_box])

    selection = VBox([Label("Select a data source."),
                      view_source, source_box, paths_box,
                      Label("Select a parcel to display."),
                      select_option_box, select_box])

    view_box = Output(layout=Layout(border='1px solid black'))

    @button_refresh.on_click
    def button_refresh_on_click(b):
        view_box.clear_output()
        tables_first = [f for f in os.listdir(
            paths.value) if isdir(normpath(join(paths.value, f)))]
        select_aoi.options = [
            f for f in tables_first if not f.startswith('.')]
        if select_aoi.value is not None:
            years_list = [d.split('/')[-2]
                          for d in glob(f"{paths.value}/{select_aoi.value}/*/")]
            select_year.options = years_list
            if select_year.value is not None:
                parcels = normpath(
                    join(paths.value, select_aoi.value, select_year.value))
                parcels_list = [f for f in os.listdir(
                    parcels) if not f.startswith('.')]
                selection_single.options = parcels_list
        else:
            selection_single.options = []
            select_year.options = []
            selection_single.value = None

    @rm_parcel.on_click
    def rm_parcel_on_click(b):
        try:
            parcel_to_rm = normpath(join(paths.value, select_aoi.value,
                                         selection_single.value))
            try:
                shutil.rmtree(f'{parcel_to_rm}')
            except Exception:
                pass
            try:
                os.remove(f'{parcel_to_rm}')
            except Exception:
                pass
#             print(f"The parce: '{selection_single.value}' is deleted.")
            parcels = normpath(
                join(paths.value, select_aoi.value, select_year.value))
            parcels_list = [f for f in os.listdir(
                parcels) if not f.startswith('.')]
            selection_single.options = parcels_list
            view_box.clear_output()
        except Exception:
            pass

    def on_datapath_change(change):
        tables = [f for f in os.listdir(
            paths.value) if isdir(normpath(join(paths.value, f)))]
        tables = [f for f in tables if not f.startswith('.')]
        select_aoi.options = tables
    paths.observe(on_datapath_change, 'value')

    def on_aoi_change(change):
        if select_aoi.value is not None:
            years = normpath(
                join(paths.value, select_aoi.value))
            years_list = [f for f in os.listdir(
                years) if not f.startswith('.')]
            select_year.options = years_list
        else:
            select_year.options = []
            select_year.value = None
            view_method.options = []
    select_aoi.observe(on_aoi_change, 'value')

    def on_year_change(change):
        if select_aoi.value is not None:
            parcels = normpath(
                join(paths.value, select_aoi.value, select_year.value))
            parcels_list = [f for f in os.listdir(
                parcels) if not f.startswith('.')]
            selection_single.options = parcels_list
        else:
            selection_single.options = []
            selection_single.value = None
            view_method.options = []
    select_year.observe(on_year_change, 'value')

    def on_selection_change(obj):
        code_info.value = "Select how to view the dataset."
        options_list = [('Get example code', 1)]
        if obj['new'] is not None:
            parceldata = normpath(
                join(paths.value, select_aoi.value,
                     select_year.value, selection_single.value))
            data_list = [f for f in os.listdir(
                parceldata) if not f.startswith('.')]
            if any("time_series" in s for s in data_list):
                options_list.append(('Plot time series', 2))
            if any("chip_images" in s for s in data_list):
                options_list.append(('View images', 3))
            options_list.append(("Show on map", 4))
            view_method.options = options_list
            view_method.value = None

    selection_single.observe(on_selection_change, 'value')

    def method_options(obj):
        view_box.clear_output()
        data_path = normpath(join(paths.value, select_aoi.value,
                                  select_year.value, selection_single.value))
        with view_box:
            if obj['new'] == 1:
                display(view_code.code(data_path))
            elif obj['new'] == 2:
                display(view_time_series.time_series_widget(
                    select_aoi.value, select_year.value,
                    selection_single.value))
            elif obj['new'] == 3:
                display(view_grid.imgs_grid(data_path))
            elif obj['new'] == 4:
                display(view_map.widget_box(data_path))

    selection_single.observe(method_options, 'value')
    view_method.observe(method_options, 'value')

    notes_info = Label("Add a note for the parcel")
    notes_bt = Button(
        value=False,
        description='Add note',
        disabled=False,
        button_style='info',
        tooltip='Add a note.',
        icon='sticky-note'
    )
    notes_box = VBox([])

    @notes_bt.on_click
    def notes_bt_on_click(b):
        if notes_box.children == ():
            notes_box.children = [view_notes.notes(
                normpath(join(paths.value, select_aoi.value)),
                select_aoi.value, select_year.value,
                selection_single.value)]
        else:
            notes_box.children = []

    wbox = VBox([selection, code_info, view_method, view_box,
                 HBox([notes_info, notes_bt]), notes_box])

    return wbox
