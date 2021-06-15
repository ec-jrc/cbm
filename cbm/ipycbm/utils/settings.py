#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
from os.path import join, normpath
from ipywidgets import (Text, VBox, HBox, Label, Dropdown,
                        Button, Checkbox, Layout, Output, BoundedIntText,
                        RadioButtons, Box, Tab)

from cbm.utils import config, data_options
from cbm.ipycbm.utils import settings_ds


def main():

    tab_box = Tab(children=[data_source(), general()])

    tab_box.set_title(0, 'DataSource')
    tab_box.set_title(1, 'General')

    return tab_box


def data_source():

    source = config.get_value(['set', 'data_source'])

    sources = RadioButtons(
        options=[
            ("RESTful API for CbM.", 'api'),
            ("Direct access to database and object storage.", 'direct')
        ],
        value=source,
        layout={'width': 'max-content'},
        disabled=True
    )

    sources_box = Box([
        Label(value="Data sources:"),
        sources]
    )

    info_api = Label("RESTful API Settings.")
    info_direct = Label("Direct access settings")

    view_options = VBox([info_direct])

    if source == 'api':
        view_options.children = [info_api, settings_ds.api()]
    elif source == 'direct':
        view_options.children = [info_direct, settings_ds.direct()]

    def on_source_change(change):
        view_options.children = []
        if sources.value == 'api':
            view_options.children = [info_api, settings_ds.api()]
        elif sources.value == 'direct':
            view_options.children = [info_direct, settings_ds.direct()]
        config.set_value(['set', 'data_source'], sources.value)

    sources.observe(on_source_change, 'value')

    wbox_sources = VBox([sources_box, view_options],
                        layout=Layout(border='1px solid black'))

    return wbox_sources


def general():
    """General settings.
    Args:
        None
    Returns:
        update_widget : A widget for general settings.
    Raises:
        Error:
    Example:

    """

    # User settings
    user_info = Label("General settings.")

    values = config.read()

    user_name = Text(
        value=values['set']['user'],
        placeholder='user name',
        description='User:',
        disabled=False
    )
    user_email = Text(
        value=values['set']['email'],
        placeholder='email@.com',
        description='email:',
        disabled=False
    )
    user_institution = Text(
        value=values['set']['institution'],
        placeholder='EU-',
        description='Institution:',
        disabled=False
    )
    ms_list = data_options.eu_ms()
    ms = Dropdown(
        options=[(ms_list[m], m) for m in ms_list] + [('', '')],
        value=values['set']['member_state'],
        description='Member state:',
        disabled=False,
    )
    wbox_user = VBox([user_info, user_name, user_email,
                      user_institution, ms],
                     layout=Layout(border='1px solid black'))

    # System settings
    sys_info = Label(
        "System settings.")
    paths_info = Label(
        "Select the personal data folder.")

    jupyterlab = Checkbox(
        value=eval(values['set']['jupyterlab']),
        description='Workin in Jupyter Lab (Uncheck for Voila and classical jupyter environment)',
        disabled=False,
        indent=False
    )

    def on_jupyterlab_change(change):
        config.set_value(['set', 'jupyterlab'], str(jupyterlab.value))
    jupyterlab.observe(on_jupyterlab_change, 'value')

    path_data = Text(
        value=values['paths']['data'],
        description='Data path:'
    )

    path_temp = Text(
        value=values['paths']['temp'],
        description='Temp path:',
        disabled=True
    )

    files_info = Label(
        "Select where to store the parcel IDs list file from:")

    plimit_info = Label(
        "Warning: No more than 25 parcels are tested, unexpected results may occur.")
    plimit = BoundedIntText(
        value=int(values['set']['plimit']),
        max=100_000_000,
        min=1,
        step=1,
        description='Max parcels that can be downloaded:',
        disabled=False
    )

    wbox_sys = VBox([sys_info, jupyterlab, plimit_info, plimit,
                     paths_info, path_data, path_temp,
                     files_info],
                    layout=Layout(border='1px solid black'))

    btn_save = Button(
        description='Save',
        icon='save'
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    @btn_save.on_click
    def btn_save_on_click(b):
        progress.clear_output()
        config.set_value(['set', 'user'], str(user_name.value))
        config.set_value(['set', 'email'], str(user_email.value))
        config.set_value(['set', 'institution'], str(user_institution.value))
        config.set_value(['set', 'member_state'], str(user_email.value))
        config.set_value(['set', 'plimit'], str(plimit.value))
        config.set_value(['paths', 'data'], str(path_data.value))
        config.set_value(['paths', 'temp'], str(path_temp.value))
        outlog("The new settings are saved.")

    wbox = VBox([clean_temp(), wbox_user, wbox_sys,
                 HBox([btn_save]),
                 progress])

    return wbox


def clean_temp(hide=False):
    import shutil
    progress = Output()

    def outlog(*text):
        progress.clear_output()
        with progress:
            print(*text)

    temppath = config.get_value(['paths', 'temp'])
    directory = os.listdir(normpath(join(config.path_work, temppath)))

    if len(directory) > 0:
        outlog(f"Your temp folder '{temppath}' has old files:",
               f" '{directory}', do you want to delete them? ")

    bt_clean = Button(
        value=False,
        description='Empty temp folder',
        disabled=False,
        button_style='danger',
        tooltip='Delete all data from the temporary folder.',
        icon='trash'
    )

    clean_box = HBox([bt_clean, progress])

    @bt_clean.on_click
    def bt_clean_on_click(b):
        for i in directory:
            try:
                shutil.rmtree(join(temppath, i))
            except Exception:
                os.remove(join(temppath, i))
        outlog(f"The '{temppath}' folder is now empty.")

    if hide is False:
        return clean_box
    elif hide is True and len(directory) > 0:
        return clean_box
    else:
        return HBox([])
