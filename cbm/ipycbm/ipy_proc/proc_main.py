#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import Tab
from cbm.ipycbm.utils import help_docs
from cbm.ipycbm.ipy_proc import proc_settings, proc_panel

def proc_widget_box():

    tab_box = Tab(children=[proc_panel.proc(), help_docs.widget_box(),
                  proc_settings.widget_box()])

    tab_box.set_title(0, 'Process Data')
    tab_box.set_title(1, 'Help')
    tab_box.set_title(2, 'Settings')

    return tab_box
