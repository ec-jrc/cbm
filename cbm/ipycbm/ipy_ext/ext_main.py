#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import Tab
from cbm.ipycbm.utils import help_docs
from cbm.ipycbm.ipy_ext import ext_settings, ext_panel

def ext_widget_box():

    tab_box = Tab(children=[ext_panel.extract(), help_docs.widget_box(),
                  ext_settings.widget_box()])

    tab_box.set_title(0, 'Process Data')
    tab_box.set_title(1, 'Help')
    tab_box.set_title(2, 'Settings')

    return tab_box
