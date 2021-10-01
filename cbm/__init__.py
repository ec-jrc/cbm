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

import sys

import os
from os.path import join, normcase, normpath
from cbm.utils import update
from pkg_resources import get_distribution, DistributionNotFound

from cbm import show, get, extract, foi, card2db

if sys.version_info < (3, 6):
    print("Not supoted python version, cbm needs python version > 3.6")
    sys.exit()

try:
    _dist = get_distribution('cbm')
    # Normalize case for Windows systems
    dist_loc = normcase(_dist.location)
    here = normcase(__file__)
    if not here.startswith(normpath(join(dist_loc, 'cbm'))):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = _dist.version

os.makedirs("temp", exist_ok=True)
update.check()


def init():
    from cbm.utils import init
    init.main()


def set_api_account(url, username, password):
    from cbm.utils import config
    config.set_value(['api', 'url'], url)
    config.set_value(['api', 'user'], username)
    config.set_value(['api', 'pass'], password)
    print("The 'api' key in config/main.json file is updated:")
    print(config.get_value(['api']))
