#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import Tab
from src.utils import help_docs
from src.ipycbm.ui_cbm import cbm_settings, cbm_panel

def cbm_widget_box():

    tab_box = Tab(children=[cbm_panel.cbm(), help_docs.widget_box(),
                  cbm_settings.widget_box()])

    tab_box.set_title(0, 'Checks by Monitoring')
    tab_box.set_title(1, 'Help')
    tab_box.set_title(2, 'Settings')

    return tab_box
