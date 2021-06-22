#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import datetime
from IPython.display import display
from ipywidgets import (Text, Label, HBox, VBox, Layout, Dropdown,
                        Output, Button, DatePicker, RadioButtons)

from cbm.utils import config, data_options


def main():
    source = config.get_value(['s3', 'dias'])
    dias = Dropdown(
        options=data_options.dias_providers(),
        value='EOSC',
        description='DIAS Provider:',
    )

    dias_box = VBox()
    
    def dias_set(d):
        if d in ['CREODIAS', 'EOSC']:
            from cbm.ipycbm.ipy_ext.dias import creodias
            dias_box.children = [creodias.main()]
        elif d in ['SOBLOO']:
            from cbm.ipycbm.ipy_ext.dias import sobloo
            dias_box.children = [sobloo.main()]
        elif d in ['MUNDI']:
            dias_box.children = [Label('This provider is not supported yet')]
        elif d in ['ONDA']:
            dias_box.children = [Label('This provider is not supported yet')]
        elif d in ['WEKEO']:
            dias_box.children = [Label('This provider is not supported yet')]
    dias_set(source)

    def on_dias_change(change):
        dias_box.children = []
        dias_set(dias.value)

    dias.observe(on_dias_change, names='value')

    return VBox([dias, dias_box])