#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
"""__init__.py: Description of what this module does."""

__title__ = "CbM"
__author__ = ["Guido Lemoine", "Konstantinos Anastasakis"]
__copyright__ = "Copyright 2021, European Commission Joint Research Centre"
__credits__ = ["GTCAP Team"]
__license__ = "3-Clause BSD"
__version__ = "01/2021"
__maintainer__ = ["Guido Lemoine", "Konstantinos Anastasakis"]
__email__ = ""
__status__ = "Development"

import os
import sys
from os.path import dirname, abspath, join
from cbm.utils import config

if sys.version_info < (3, 6):
    print("Not supoted python version, cbm needs python version > 3.6")
    sys.exit()

paths = config.get_value(['paths'])
paths['config'] = 'config'

for p in paths:
    try:
        if not os.path.exists(join(config.folder_repo, paths[p])):
            os.makedirs(join(config.folder_repo, paths[p]))
            print(f"Directory {p} created successfully")
    except OSError as error:
        print(f"Directory {p} can not be created")

config.create()
