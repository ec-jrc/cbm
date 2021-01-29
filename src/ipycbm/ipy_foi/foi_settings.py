#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (Text, VBox, Label, Password, RadioButtons,
                        Button, Checkbox, Layout, Box)

from src.utils import config, update, settings


def widget_box():

    info_general = Label(value="General settings:")

    wbox = VBox([info_general,
                 settings.widget_box()])

    return wbox
