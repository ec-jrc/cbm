#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import json
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from skimage import exposure
from rasterio.plot import show
from descartes import PolygonPatch
from cbm.get import parcel_info, chip_images
from os.path import join, normpath, isfile, exists

from cbm.utils import data_options, spatial_utils, raster_utils, config


def grid(aoi, year, pid, start_date=None, end_date=None, imgtype=['B04', 'B08'],
         chipsize=400, columns=4, show_parcel=True, cmap='RdYlGn_r',
         percentile=[2, 98], ptype='g', debug=False):

    if type(imgtype) is str:
        bands = [imgtype]  # bands
    else:
        bands = imgtype

    if bands[0].lower() == 'ndvi':
        bands = ['B04', 'B08']
    elif bands[0].lower().replace(' ', '_') == 'true_color':
        bands = ['B04', 'B03', 'B02']

    if start_date is None and end_date is None:
        start_date, end_date = f'{year}-01-01', f'{year}-12-31'

    path = normpath(join(config.get_value(['paths', 'temp']),  # workdir
                         aoi, str(year), str(pid)))
    file_info = normpath(join(path, 'info.json'))
    if not isfile(file_info):
        parcel_info.by_pid(aoi, str(year), str(pid), ptype, True)
    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())

    ci_path = normpath(join(path, 'chip_images'))

    for b in bands:
        csv_list_b = normpath(join(ci_path, f'images_list.{b}.csv'))
        if debug:
            print(csv_list_b)
        if not exists(csv_list_b):
            chip_images.by_pid(aoi, year, pid, start_date, end_date,
                               b, 512, ptype, debug)

    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]

    # available_options = raster_utils.available_options(path, pid)

    print(f"Crop name: {crop_name},  Area: {area:.2f} sqm")

    def multi_bands_imgs(bands, fname):
        df = raster_utils.create_df(ci_path, pid, bands)
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
                if show_parcel:
                    ax.add_patch(overlay_parcel(img, info_data))

                plt.axis('off')  # Turn of axis.
                pA, pB = np.percentile(
                    img.read(1), tuple(percentile))

                # Strech image to A - B percentile.
                stack = [exposure.rescale_intensity(
                    img.read()[i, :, :], in_range=(
                        pA, pB)) for i in range(len(bands))]
                rgb_enhanced = np.dstack(stack)

                show(np.uint16(rgb_enhanced.transpose(2, 0, 1) / 300),
                     ax=ax, transform=img.transform)
        return plt.show()

    def ndvi_imgs(bands, fname):
        df = raster_utils.create_df(ci_path, pid, bands)
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
            if show_parcel:
                ax.add_patch(overlay_parcel(b4, info_data))

            plt.axis('off')  # Turn of axis.
            pA, pB = np.percentile(
                ndvi, tuple(percentile))

            show(ndvi, ax=ax, transform=b4.transform,
                 cmap=cmap, vmin=pA, vmax=pB)

            b4.close()
        return plt.show()

    def single_band(band):
        df = raster_utils.create_df(ci_path, pid, bands)
        rows = round((df.shape[0] / columns) + 0.5)
        fig = plt.figure(figsize=(16, 4 * rows))
        for i, row in df.iterrows():
            img_gtif = normpath(
                join(ci_path, f"{row['imgs']}.{bands[0]}.tif"))
            with rasterio.open(img_gtif, format='GTiff') as img:
                fig.add_subplot(rows, columns, i + 1)
                overlay_date(img, row['date'].date())
                plt.axis('off')
                ax = plt.gca()
                if show_parcel:
                    ax.add_patch(overlay_parcel(img, info_data))

                img_read = img.read(1)

                pA, pB = np.percentile(
                    img_read, tuple(percentile))
                show(img.read(1), ax=ax, transform=img.transform,
                     cmap=data_options.cmaps(bands[0]),
                     vmin=pA, vmax=pB)

        return plt.show()

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

    if len(bands) == 1 and bands[0][0].lower() == 'b':
        return single_band(bands[0])
    elif bands == ['B04', 'B08']:
        return ndvi_imgs(bands, 'NDVI')
    elif bands == ['B04', 'B03', 'B02']:
        return multi_bands_imgs(bands, ('').join(bands))  # True color
    else:
        return f"""Not recognized images type {bands}.
        (use: [B0x, B...], True color or NDVI)"""
