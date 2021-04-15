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


from IPython.display import display
from cbm.ipycbm.utils import settings
from cbm.utils import config

display(settings.clean_temp(True))
config.update_keys()


def get(*args):
    from cbm.ipycbm.ipy_get import get_main
    return get_main.get_widget_box(*args)


def view(*args):
    from cbm.ipycbm.ipy_view import view_main
    return view_main.view_widget_box(*args)


def extract(*args):
    from cbm.ipycbm.ipy_ext import ext_main
    return ext_main.ext_widget_box(*args)


def foi(*args):
    from cbm.ipycbm.ipy_foi import foi_main
    return foi_main.foi_widget_box(*args)


def qa(*args):
    from cbm.ipycbm.ipy_qa import qa_main
    return qa_main.qa_widget_box(*args)


def config(*args):
    from cbm.ipycbm.utils import settings
    return settings.main(*args)


def bg_grid(*args):
    from cbm.show import background
    return background.by_pid(*args)


def bg_slider(*args):
    from cbm.ipycbm.ipy_view import view_background
    return view_background.slider(*args)


def card2db(*args):
    from cbm.ipycbm.ipy_ext import ext_card2db
    return ext_card2db.dias_cat(*args)
