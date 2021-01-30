#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (Text, VBox, Label, Password, 
                        Button, Checkbox, Layout)

from src.utils import config
from src.ipycbm.utils import update, settings

def widget_box():

    wbox = VBox([settings.widget_box()])
    
    return wbox
