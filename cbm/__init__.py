#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
"""__init__.py: Description of what this module does."""

__title__ = "CbM"
__author__ = ["Guido Lemoine", "Konstantinos Anastasakis"]
__copyright__ = "Copyright 2021, European Commission Joint Research Centre"
__credits__ = ["GTCAP Team"]
__license__ = "3-Clause BSD"
__maintainer__ = ["Guido Lemoine", "Konstantinos Anastasakis"]
__email__ = ""
__status__ = "Development"

import os
import os.path
from cbm.utils import config, update
from pkg_resources import get_distribution, DistributionNotFound

import sys
if sys.version_info < (3, 6):
    print("Not supoted python version, cbm needs python version > 3.6")
    sys.exit()

try:
    _dist = get_distribution('cbm')
    # Normalize case for Windows systems
    dist_loc = os.path.normcase(_dist.location)
    here = os.path.normcase(__file__)
    if not here.startswith(os.path.join(dist_loc, 'cbm')):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = _dist.version

paths = config.get_value(['paths'])
for p in paths:
    try:
        if not os.path.exists(os.path.join(config.path_work, paths[p])):
            os.makedirs(os.path.join(config.path_work, paths[p]))
            print(f"Directory {p} created successfully")
    except OSError as err:
        print(f"Directory {p} can not be created: ", err)

config.create()
update.check()
