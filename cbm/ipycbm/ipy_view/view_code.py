#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import glob


def code(path):
    from ipywidgets import HTML
    file_info = f"{path}info.json"
    file_ts = glob.glob(f"{path}time_series_*.csv")
    folder_ci = f"{path}/chip_images"

    code = f"""
        <H2>Get and display data for the selected parcel.</H2>
        <b>Example to read the json file with parcel informatin:</b><br>
        <code>import json</code><br>
        <code>with open('{file_info}', 'r') as f:</code><br>
        <code> &nbsp; &nbsp; json_data = json.loads(f.read())</code><br>
        <code>print(json_data)</code><br>
        <br>
        <b>Example code on how to run database queries</b><br>
        from cbm.datas import database<br>
        # Return the exact count of rown of the given table<br>
        query = "SELECT count(*) AS exact_count FROM abigtable_names;"<br>
        database.execute_query(query)<br>
    """

    if file_ts:
        code = f"""{code}
<H3>Basic example code to plot the time series:</H3><br>
<code>import pandas as pd<br>
df = pd.read_csv('{file_ts[0]}', index_col=0)<br>
df.plot.scatter(x='date_part', y='max')</code><br>

<b>To view and edit a more advanced code to plot the time series, copy the <br>
contents of the file 'ipycbm/ipy_view/view_time_series' to a new cell and <br>
the below code to another cell and run the cells:</b><br>
path = '{path}'<br>
time_series(path)<br>
        <br>
        """

    if folder_ci:
        code = f"""{code}
<H3>Basic example code to view the images:</H3><br>
<code>import glob<br>
import numpy as np<br>
from osgeo import gdal<br>
import matplotlib.pyplot as plt<br>
folder_ci = f'{path}/chip_images'<br>
image_list = glob.glob(f'{folder_ci}/*.tif')<br>
fig = plt.figure(figsize=(8, 8))<br>
columns = 4<br>
rows = 5<br>
image = 0<br>
for i in range(1, columns * rows + 1):<br>
 &nbsp; &nbsp; ds = gdal.Open(image_list[image])<br>
 &nbsp; &nbsp; img = np.array(ds.GetRasterBand(1).ReadAsArray())<br>
 &nbsp; &nbsp; fig.add_subplot(rows, columns, i)<br>
 &nbsp; &nbsp; plt.imshow(img)<br>
 &nbsp; &nbsp; image = image + 1<br>
 &nbsp; &nbsp; if image == len(image_list):<br>
 &nbsp; &nbsp;  &nbsp; &nbsp; break<br>
plt.show()</code><br>

<b>To view and edit a more advanced code to view the images, copy the <br>
contents of the file 'ipycbm/ipy_view/view_grid' to a new cell and the <br>
below code to another cell and run the cells:</b><br>
path = '{path}'<br>
imgs_grid(path)<br>
        """

    code_widget = HTML(
        value=code,
        placeholder="Documantation",
        description="")
    return code_widget
