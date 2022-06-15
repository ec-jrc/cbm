#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from IPython.display import display
from ipywidgets import HTML, VBox, Output
from cbm.show import parcel_info


def info(path):
    try:
        p = path.split('/')
        pinf = parcel_info.by_pid(p[-3], p[-2], p[-1], view=False)
    except Exception:
        pinf = VBox([])
    # file_info = f"{path}info.json"
    # file_ts = glob.glob(f"{path}time_series_*.csv")
    # folder_ci = f"{path}/chip_images"

    notes = f"""
        <H2>General information.</H2><br>
        This tool is part of JRC-CbM, see https://github.com/ec-jrc/cbm for more code examples.<br>
        All code examples are under the open source License 3-Clause BSD<br>
        For more information See the documentation at: https://jrc-cbm.readthedocs.io<br>
        <br>
        <br>
        <H4>information for the selected parcel.</H4><br>
    """

    out = Output()
    with out:
        display(pinf)

    notes_widget = HTML(
        value=notes,
        placeholder="Documantation",
        description="")
    return VBox([notes_widget, out])
