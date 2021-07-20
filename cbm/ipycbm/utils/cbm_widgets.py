#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import glob
from ipywidgets import (Label, HBox, VBox, Layout, Dropdown,
                        Output, Button, FileUpload)


def get_files_dropdown(path, ftypes='', description='',
                       select_multi=False, only_shp=False):

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    select = FileUpload(
        description='Select file:',
        icon='plus',
        accept=ftypes,
        multiple=select_multi
    )
    clear = Button(
        value=False,
        button_style='warning',
        tooltip='Clear selection.',
        icon='broom',
        layout=Layout(width='40px')
    )
    upload = Button(
        value=False,
        button_style='info',
        tooltip='Upload file.',
        icon='fa-upload',
        layout=Layout(width='40px')
    )
    dist_folder = Label(f"Destination path: '{path}'")

    flist = Dropdown(
        options=filter_files(path, ftypes, only_shp),
        description=description,
        disabled=False,
    )
    refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh'
    )

    @refresh.on_click
    def refresh_on_click(b):
        flist.options = filter_files(path, ftypes, only_shp)

    @clear.on_click
    def clear_on_click(b):
        select.value.clear()
        select._counter = 0

    @upload.on_click
    def upload_on_click(b):
        progress.clear_output()
        os.makedirs(path, exist_ok=True)
        for key in select.value:
            content = select.value[key]['content']
            with open(f'{path}/{key}', 'wb') as f:
                f.write(content)
        flist.options = filter_files(path, ftypes, only_shp)
        outlog("The file is uploaded.")

    return VBox([HBox([select, clear, upload, dist_folder]),
                 HBox([flist, refresh]), progress])


def filter_files(path, ftypes, only_shp=False):
    if type(ftypes) is str:
        ftypes = ftypes.split(', ')
    if only_shp:
        ftypes = ['shp']
    flist = []
    for s in glob.glob(f'{path}/*'):
        for f in ftypes:
            if s.endswith(f):
                flist.append(s)
    return flist
