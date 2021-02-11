#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (Text, VBox, Label, Password, RadioButtons,
                        Button, Checkbox, Layout, Box)

from cbm.utils import config
from cbm.ipycbm.utils import update, settings


def widget_box():

    source = config.get_value(['set', 'data_source'])

    sources = RadioButtons(
        options=[
            ("DIAS API.", 'dias_api'),
            ("Direct access to database and object storage.", 'direct')
        ],
        layout={'width': 'max-content'}
    )

    sources_box = Box([
        Label(value="Available sources:"),
        sources]
    )

    info_api = Label("DIAS API Settings.")
    info_direct = Label("Direct access settings")

    view_options = VBox([info_direct])

    if source == 'direct':
        view_options.children = [info_direct]
    else:
        view_options.children = [info_api, dias_api()]

    def on_source_change(change):
        view_options.children = []
        if sources.value == 'dias_api':
            view_options.children = [info_api, dias_api()]
        elif sources.value == 'direct':
            view_options.children = [info_direct]
        config.update(['preferences', 'data_source'], str(sources.value))

    sources.observe(on_source_change, 'value')

    wbox_sources = VBox([sources_box, view_options],
                        layout=Layout(border='1px solid black'))

    info_general = Label(value="General settings:")

    wbox = VBox([wbox_sources, info_general, settings.widget_box()])

    return wbox


def dias_api(mode=None):
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

    @wb_save.on_click
    def wb_save_on_click(b):
        config.update(['api', 'url'], str(wt_url.value))
        config.update(['api', 'user'], str(wt_user.value))
        if wt_pass.value != '':
            config.update(['api', 'pass'], str(wt_pass.value))
        print("API information is updated")

    wbox = VBox([wt_url, wt_user, wt_pass, wb_save])

    return wbox

