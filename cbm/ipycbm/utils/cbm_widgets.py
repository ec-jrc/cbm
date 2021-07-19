#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import glob
from ipywidgets import (Text, Label, HBox, VBox, Layout, Dropdown,
                        ToggleButtons, Output, HTML, Button,
                        FileUpload, IntText, RadioButtons)


def get_files_dropdown(path, ftype='', description='', select_multi=False):

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    select = FileUpload(
        description='Select file:',
        icon='plus',
        accept=ftype,
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
        options=[os.path.basename(s) for s in glob.glob(
            f'{path}/*') if s.endswith(ftype)],
        description=description,
        disabled=False,
    )
    refresh = Button(
        layout=Layout(width='35px'),
        icon='fa-refresh'
    )

    @refresh.on_click
    def refresh_on_click(b):
        flist.options = [os.path.basename(s) for s in glob.glob(
            f'{path}/*') if s.endswith(ftype)]

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
        flist.options = [os.path.basename(s) for s in glob.glob(
            f'{path}/*') if s.endswith(ftype)]
        outlog("The file is uploaded.")

    return VBox([HBox([select, clear, upload, dist_folder]),
                 HBox([flist, refresh]), progress])
