#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import Tab
from cbm.ipycbm.utils import settings, help_docs
from cbm.ipycbm.ipy_get import get_panel


def get_widget_box():

    try:
        tab_box = Tab(children=[get_panel.get(), help_docs.widget_box(),
                                settings.main()])

        tab_box.set_title(0, 'Get Data')
        tab_box.set_title(1, 'Help')
        tab_box.set_title(2, 'Settings')

    except Exception as err:
        tab_box = Tab(children=[help_docs.widget_box(),
                                settings.main()])

        tab_box.set_title(0, 'Help')
        tab_box.set_title(1, 'Settings')
        print("Could not show 'Get panel'.", err)

    return tab_box
