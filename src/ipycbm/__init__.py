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


from src.utils import check
check.startup()


def get(*args):
    from src.ipycbm.ipy_get import get_main
    return get_main.get_widget_box(*args)

def view(*args):
    from src.ipycbm.ipy_view import view_main
    return view_main.view_widget_box(*args)

def proc(*args):
    from src.ipycbm.ipy_proc import proc_main
    return proc_main.proc_widget_box(*args)

def foi(*args):
    from src.ipycbm.ipy_foi import foi_main
    return foi_main.foi_widget_box(*args)

def qa(*args):
    from src.ipycbm.ipy_qa import qa_main
    return qa_main.qa_widget_box(*args)