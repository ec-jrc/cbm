#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
from os.path import dirname, abspath
from IPython.display import display

from src.utils import config
from src.ipycbm.utils import update

def error(err):
    if config.get_value(['api', 'pass']) == '':
        print("Please provide a password for you selected data source.")
    elif 'line 1 column 1 (char 0)' in str(err):
        print("Cloud not conect to the selected data source.",
              "Please check your user name and password.")


def startup():
    import sys
    if sys.version_info < (3, 6):
        print("Not supoted python version, ipycbm needs python version > 3.6")
        return

    config.update_keys()

    paths = config.get_value(['paths'])
    for p in paths:
        os.makedirs(paths[p], exist_ok=True)

    update.check()
    display(config.clean_temp(True))
