#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import shutil
from IPython.display import display
from ipywidgets import (Label, VBox, HBox, Layout, Dropdown, SelectMultiple,
                        ToggleButtons, Output, Box, RadioButtons, Button)

from cbm.utils import config
from cbm.ipycbm.ipy_view import view_notes


def view():
    info = Label("Select a parcel to display.")

    temppath = config.get_value(['paths', 'temp'])
    datapath = config.get_value(['paths', 'data'])

    method = ToggleButtons(
        options=[('From local storage', 0),
                 ('Remote to memory', 1)],
        value=0,
        description='',
        disabled=True,
        button_style='info',
        tooltips=['View data that are stored on the local drive.',
                  'View data from memory.']
    )

    paths = RadioButtons(
        options=[(f"Temporary folder: '{temppath}'.", temppath),
                 (f"Personal data folder: '{datapath}'.", datapath)],
        layout={'width': 'max-content'},
        value=temppath
    )

    paths_box = Box([Label(value="Select folder:"), paths])

    tables_first = [f for f in os.listdir(
        paths.value) if os.path.isdir(os.path.join(paths.value, f))]

    select_table = Dropdown(
        options=[f for f in tables_first if not f.startswith('.')],
        value=None,
        description='Select tabe:',
        disabled=False,
    )

    select_option = RadioButtons(
        options=[(f"Single parcel selection.", 1),
                 (f"Multiple parcels selection.", 2)],
        disabled=True,
        layout={'width': 'max-content'}
    )

    button_refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh')

    select_option_box = HBox([select_table, button_refresh, Label(
        value="Selection method:"), select_option])

    selection_single = Dropdown(
        options=[],
        value=None,
        description='Select parcel:',
        disabled=False,
    )

    selection_multi = SelectMultiple(
        options=[],
        value=[],
        description='Select parcels:',
        disabled=False,
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

    code_info = Label()
    single_box = HBox([selection_single, rm_parcel])
    select_box = Box([single_box])

    method_0 = VBox([info, paths_box, select_option_box, select_box])
    method_1 = VBox([])
    view_box = Output(layout=Layout(border='1px solid black'))
    method_out = Output()
    with method_out:
        display(method_0)

    def method_options(obj):
        with method_out:
            method_out.clear_output()
            if obj['new'] == 0:
                display(method_0)
            elif obj['new'] == 1:
                display(method_1)

    method.observe(method_options, 'value')

    @button_refresh.on_click
    def button_refresh_on_click(b):
        view_box.clear_output()
        tables_first = [f for f in os.listdir(
            paths.value) if os.path.isdir(os.path.join(paths.value, f))]
        select_table.options = [
            f for f in tables_first if not f.startswith('.')]
        if select_table.value is not None:
            parcels = f"{paths.value}{select_table.value}"
            parcels_list = [f for f in os.listdir(
                parcels) if not f.startswith('.')]
            selection_single.options = parcels_list
            selection_multi.options = parcels_list
        else:
            selection_single.options = []
            selection_single.value = None
            selection_multi.options = []
            selection_multi.value = []

    @rm_parcel.on_click
    def rm_parcel_on_click(b):
        try:
            parcel_to_rm = f"{paths.value}{select_table.value}/{selection_single.value}"
            try:
                shutil.rmtree(f'{parcel_to_rm}')
            except Exception:
                pass
            try:
                os.remove(f'{parcel_to_rm}')
            except Exception:
                pass
#             print(f"The parce: '{selection_single.value}' is deleted.")
            parcels = f"{paths.value}{select_table.value}"
            parcels_list = [f for f in os.listdir(
                parcels) if not f.startswith('.')]
            selection_single.options = parcels_list
            view_box.clear_output()
        except Exception:
            pass

    def on_select_option_change(change):
        if select_option.value == 1:
            select_box.children = [single_box]
        else:
            select_box.children = [selection_multi]

    select_option.observe(on_select_option_change, 'value')

    def on_datapath_change(change):
        tables = [f for f in os.listdir(
            paths.value) if os.path.isdir(os.path.join(paths.value, f))]
        tables = [f for f in tables if not f.startswith('.')]
        select_table.options = tables

    paths.observe(on_datapath_change, 'value')

    def on_table_change(change):
        if select_table.value is not None:
            parcels = f"{paths.value}{select_table.value}"
            parcels_list = [f for f in os.listdir(
                parcels) if not f.startswith('.')]
            selection_single.options = parcels_list
            selection_multi.options = parcels_list
        else:
            selection_single.options = []
            selection_single.value = None
            selection_multi.options = []
            selection_multi.value = []
            view_method.options = []

    select_table.observe(on_table_change, 'value')

    def on_selection_change(obj):
        code_info.value = "Select how to view the dataset."
        options_list = [('Get example code', 1)]
        if obj['new'] is not None:
            parceldata = f"{paths.value}{select_table.value}/{selection_single.value}"
            data_list = [f for f in os.listdir(
                parceldata) if not f.startswith('.')]
            if any("time_series" in s for s in data_list):
                options_list.append(('Plot time series', 2))
            if any("chip_images" in s for s in data_list):
                options_list.append(('View images', 3))
            options_list.append(("Show on map", 4))
            if select_option.value == 2:
                options_list.append(('Comparison', 5))
            view_method.options = options_list
            view_method.value = None

    selection_single.observe(on_selection_change, 'value')
    selection_multi.observe(on_selection_change, 'value')

    def method_options(obj):
        view_box.clear_output()
        with view_box:
            if selection_single.value is None:
                with view_box:
                    print("Please select a parcel")

            elif select_option.value == 1:
                data_path = f'{paths.value}{select_table.value}/{selection_single.value}/'
                if obj['new'] == 1:
                    from cbm.ipycbm.ipy_view import view_code
                    display(view_code.code(data_path))
                elif obj['new'] == 2:
                    from cbm.ipycbm.ipy_view import view_time_series
                    display(view_time_series.time_series(data_path))
                elif obj['new'] == 3:
                    from cbm.ipycbm.ipy_view import view_grid
                    display(view_grid.imgs_grid(data_path))
                elif obj['new'] == 4:
                    from cbm.ipycbm.ipy_view import view_map
                    display(view_map.widget_box(data_path))

            elif select_option.value == 2 and len(selection_multi.value) > 0:
                data_path = f'{paths.value}{select_table.value}/'
                data_paths = [
                    f'{data_path}{s}/' for s in selection_multi.value]
                if obj['new'] == 1:
                    from cbm.ipycbm.ipy_view import view_code
                    display(view_code.code(data_paths[0]))
                    pass
                elif obj['new'] == 2:
                    from cbm.ipycbm.ipy_view import view_time_series
                    # display(view_time_series.time_series(data_list[0]))
                    pass
                elif obj['new'] == 3:
                    from cbm.ipycbm.ipy_view import view_grid
                    # display(view_chip_images.imgs_grid(data_path))
                    pass
                elif obj['new'] == 4:
                    from cbm.ipycbm.ipy_view import view_maps
                    display(view_maps.with_polygons(data_paths))

    selection_single.observe(method_options, 'value')
    selection_multi.observe(method_options, 'value')
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
                f"{paths.value}{select_table.value}/",
                select_table.value,
                selection_single.value)]
        else:
            notes_box.children = []

    wbox = VBox([method_out, code_info, view_method, view_box,
                 HBox([notes_info, notes_bt]), notes_box])

    return wbox
