#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import json
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
from os.path import join, normpath, isfile
from descartes import PolygonPatch
from ipywidgets import (HBox, VBox, Dropdown, Button, Output,
                        Checkbox, Layout, IntRangeSlider)

from cbm.utils import data_options, spatial_utils, raster_utils

from skimage import exposure


def imgs_grid(path):

    def show_imgs():
        print(f"Crop name: {crop_name},  Area: {area:.2f} sqm")

        def multi_bands_imgs(bands, fname):
            df = raster_utils.create_df(ci_path, pid, ci_band.value)
            rows = round((df.shape[0] / columns) + 0.5)
            fig = plt.figure(figsize=(16, 4 * rows))
            for i, row in df.iterrows():
                fig.add_subplot(rows, columns, i + 1)

                str_date = str(row['date'].date()).replace('-', '')
                img_png = normpath(join(ci_path, f'{fname}_{str_date}.png'))

                # Create color image if it does not exist
                # Merge bands (images path, export image path, bands list)
                if not isfile(img_png):
                    imgs_path = normpath(join(ci_path, row['imgs']))
                    raster_utils.merge_bands(imgs_path, img_png,
                                             bands)

                with rasterio.open(img_png, format='PNG') as img:
                    overlay_date(img, row['date'].date())  # Add date overlay.
                    ax = plt.gca()
                    if show_parcel.value:
                        ax.add_patch(overlay_parcel(img, info_data))

                    plt.axis('off')  # Turn of axis.
                    pA, pB = np.percentile(
                        img.read(1), tuple(ci_percent.value))

                    # Strech image to A - B percentile.
                    stack = [exposure.rescale_intensity(
                        img.read()[i, :, :], in_range=(
                            pA, pB)) for i in range(len(bands))]
                    rgb_enhanced = np.dstack(stack)

                    show(np.uint16(rgb_enhanced.transpose(2, 0, 1) / 300),
                         ax=ax, transform=img.transform)
            return plt.show()

        def ndvi_imgs(bands, fname):
            df = raster_utils.create_df(ci_path, pid, ci_band.value)
            rows = round((df.shape[0] / columns) + 0.5)
            fig = plt.figure(figsize=(16, 4 * rows))
            for i, row in df.iterrows():
                fig.add_subplot(rows, columns, i + 1)

                str_date = str(row['date'].date()).replace('-', '')
                img_png = normpath(join(ci_path, f'{fname}_{str_date}.png'))

                imgs_path = normpath(join(ci_path, row['imgs']))
                b4f = f"{imgs_path}.B04.tif"
                b4 = rasterio.open(b4f, format='GTiff')

                ndvi = raster_utils.calc_ndvi(imgs_path, img_png, bands)
                overlay_date(b4, row['date'].date())  # Add date overlay.
                ax = plt.gca()
                if show_parcel.value:
                    ax.add_patch(overlay_parcel(b4, info_data))

                plt.axis('off')  # Turn of axis.
                pA, pB = np.percentile(
                    ndvi, tuple(ci_percent.value))

                show(ndvi, ax=ax, transform=b4.transform,
                     cmap=ci_cmaps.value, vmin=pA, vmax=pB)

                b4.close()
            return plt.show()

        def single_band(band):
            df = raster_utils.create_df(ci_path, pid, ci_band.value)
            rows = round((df.shape[0] / columns) + 0.5)
            fig = plt.figure(figsize=(16, 4 * rows))
            for i, row in df.iterrows():
                img_gtif = normpath(
                    join(ci_path, f"{row['imgs']}.{ci_band.value[0]}.tif"))
                with rasterio.open(img_gtif, format='GTiff') as img:
                    fig.add_subplot(rows, columns, i + 1)
                    overlay_date(img, row['date'].date())
                    plt.axis('off')
                    ax = plt.gca()
                    if show_parcel.value:
                        ax.add_patch(overlay_parcel(img, info_data))

                    img_read = img.read(1)

                    pA, pB = np.percentile(
                        img_read, tuple(ci_percent.value))
                    show(img.read(1), ax=ax, transform=img.transform,
                         cmap=data_options.cmaps(ci_band.value[0]),
                         vmin=pA, vmax=pB)

            return plt.show()

        if len(ci_band.value) == 1:
            single_band(ci_band.value[0])
        elif ci_band.value == ['B04', 'B08']:
            ndvi_imgs(ci_band.value, 'NDVI')
        else:
            multi_bands_imgs(ci_band.value, ('').join(ci_band.value))

    def overlay_date(img, date):
        date_text = plt.text(
            img.bounds.left + ((img.bounds.right - img.bounds.left) / 6.5),
            img.bounds.top - ((img.bounds.top - img.bounds.bottom) / 6.5),
            date, color='yellow', weight='bold', size=12, bbox=dict(
                boxstyle="round", ec='yellow', fc='black', alpha=0.2))

        return date_text

    def overlay_parcel(img, geom):
        with open(file_info, 'r') as f:
            info_data = json.loads(f.read())
        img_epsg = img.crs.to_epsg()
        geo_json = spatial_utils.transform_geometry(info_data, img_epsg)
        patche = [PolygonPatch(feature, edgecolor="yellow",
                               facecolor="none", linewidth=2
                               ) for feature in [geo_json['geom'][0]]]
        return patche[0]

    # Images options.
    file_info = normpath(join(path, 'info.json'))
    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())
    # print(info_data)
    pid = info_data['pid'][0]
    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]
    ci_path = normpath(join(path, 'chip_images'))
    columns = 4

    available_options = raster_utils.available_options(path, pid)
    ci_band = Dropdown(
        options=available_options,
        description='Select band:',
        disabled=False,
    )

    ci_cmaps = Dropdown(
        options=data_options.color_maps(),
        value='RdYlGn_r',
        description='Color map:',
        disabled=False,
        layout=Layout(width='15%')
    )

    ci_percent = IntRangeSlider(
        value=[2, 98],
        min=0,
        max=100,
        step=1,
        description='%:',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='d',
    )

    show_parcel = Checkbox(
        value=True,
        description='Show parcel',
        disabled=False,
        indent=False,
        layout=Layout(width='100px')
    )

    ci_cloud = Checkbox(
        value=False,
        description='Cloud free',
        disabled=True,
        indent=False,
        layout=Layout(width='140px')
    )

    btn_ci = Button(
        value=False,
        description='Show images',
        disabled=False,
        button_style='info',
        tooltip='Refresh output',
        icon=''
    )

    ci_out = Output()

    @btn_ci.on_click
    def btn_ci_on_click(b):
        btn_ci.description = 'Refresh'
        btn_ci.icon = 'refresh'
        with ci_out:
            ci_out.clear_output()
            show_imgs()

    wbox_ci_cloud = HBox([])
    if len([val for key, val in available_options if 'SCL' in val]) > 0:
        wbox_ci_cloud = HBox([ci_cloud])

    wbox_ci = HBox([btn_ci, ci_band, show_parcel, ci_percent, wbox_ci_cloud])

    def ci_band_change(change):
        if len(ci_band.value) == 1:
            if ci_band.value[0] in ['B02', 'B03', 'B04', 'B08']:
                wbox_ci.children = [btn_ci, ci_band, show_parcel, ci_percent]
                show_parcel.value = True
            else:
                wbox_ci.children = [btn_ci, ci_band, ci_percent]
                show_parcel.value = False
        elif ci_band.value == ['B04', 'B08']:
            wbox_ci.children = [btn_ci, ci_band, show_parcel, ci_cmaps,
                                ci_percent, wbox_ci_cloud]
            show_parcel.value = True
        else:
            wbox_ci.children = [btn_ci, ci_band,
                                show_parcel, ci_percent, wbox_ci_cloud]
            show_parcel.value = True

    ci_band.observe(ci_band_change, 'value')

    wbox = VBox([wbox_ci, ci_out])

    return wbox
