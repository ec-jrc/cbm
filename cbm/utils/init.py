#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import sys
from os.path import join, normcase, exists, normpath
from cbm.utils import config, update
from pkg_resources import get_distribution, DistributionNotFound


def main():
    global __version__
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

    paths = config.get_value(['paths'])
    for p in paths:
        try:
            if not exists(normpath(join(config.path_work, paths[p]))):
                os.makedirs(normpath(join(config.path_work, paths[p])))
                print(f"The folder {p} is created successfully.")
        except OSError as err:
            print(f"The folder {p} can not be created: ", err)

    config.create()
    update.check()
