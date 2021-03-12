#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from os.path import join, normpath
import pandas as pd
from ipywidgets import (Text, Textarea, HTML, BoundedIntText,
                        HBox, VBox, Dropdown, Button, Output, Checkbox, Layout)


def notes(path, ds=None, parcel=None):
    info = HTML(
        value="Add a note for the parcel",
        placeholder='Notes',
    )

    aoi = Text(
        value=ds,
        placeholder='MS or ragion',
        description='AOI:',
        disabled=False
    )
    try:
        y_ = int(ds[-4:])
    except Exception:
        y_ = 2000
    year = BoundedIntText(
        value=y_,
        min=1980,
        max=2100,
        step=1,
        description='Year:',
        disabled=False,
        layout=Layout(width='180px')

    )
    pid = Text(
        value=parcel,
        placeholder='12345',
        description='Parcel ID:',
        disabled=False
    )
    note = Textarea(
        value=None,
        placeholder='',
        description='Note:',
        disabled=False,
        layout=Layout(width='60%')
    )
    save = Button(
        value=False,
        disabled=False,
        button_style='info',
        tooltip='Save note to notes table.',
        icon='save',
        layout=Layout(width='35px')
    )
    new = HBox([aoi, year, pid])

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    @save.on_click
    def save_on_click(b):
        progress.clear_output()
        df = pd.DataFrame([[aoi.value, year.value, pid.value, note.value]])
        df.to_csv(normpath(join(path, 'notes.csv')), mode='a', header=False)
        outlog(f"The note is saved in {path}notes.csv")

    wbox = VBox([info, new, HBox([note, save]), progress])

    return wbox
