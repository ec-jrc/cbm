#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import json
import rasterio
import matplotlib.pyplot as plt
from copy import copy
from os.path import join, normpath, isfile
from descartes import PolygonPatch
from rasterio.plot import show
from mpl_toolkits.axes_grid1 import ImageGrid

from cbm.utils import config, spatial_utils
from cbm.get import background as bg


def overlay_parcel(img, geom):
    """Create parcel polygon overlay"""
    patche = [PolygonPatch(feature, edgecolor="yellow",
                           facecolor="none", linewidth=2
                           ) for feature in geom['geom']]
    return patche


def by_location(aoi, lon, lat, chipsize=512, extend=512, tms=['Google'],
                columns=4, quit=True):
    """Show the background image with parcels polygon overlay by selected
    parcel id. This function will get an image from the center of the polygon.

    Examples:
        from cbm.view import background
        background.by_location(aoi, lon, lat, 512, 512, 'Google',
                                True, True)

    Arguments:
        aoi, the area of interest and year e.g.: es2020, cat2020 (str)
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        quiet, print or not procedure information (Boolean).
    """
    show_parcel = True

    if type(tms) is str:
        tms = [tms]

    try:
        from cbm.sources import api
        json_data = json.loads(api.ploc(aoi, lon, lat, True))
        if type(json_data['ogc_fid']) is list:
            pid = json_data['ogc_fid'][0]
        else:
            pid = json_data['ogc_fid']

        workdir = normpath(join(config.get_value(['paths', 'temp']),
                                aoi, str(pid)))
    except Exception:
        workdir = normpath(join(config.get_value(['paths', 'temp']),
                                aoi, f'_{lon}_{lat}'))
        show_parcel = False
        if not quit:
            print("No parcel information found.")

    if len(tms) < columns:
        columns = len(tms)

    bg_path = normpath(join(workdir, 'backgrounds'))

    for t in tms:
        if not isfile(normpath(join(bg_path, f'{t.lower()}.tif'))):
            bg.by_location(aoi, lon, lat, chipsize, extend, t, True)

    if show_parcel:
        with open(normpath(join(workdir, 'info.json')), 'r') as f:
            json_data = json.load(f)

        with rasterio.open(normpath(join(bg_path, f'{tms[0].lower()}.tif'))) as img:
            img_epsg = img.crs.to_epsg()
            geom = spatial_utils.transform_geometry(json_data, img_epsg)
            patches = overlay_parcel(img, geom)

    rows = int(len(tms) // columns + (len(tms) % columns > 0))
    fig = plt.figure(figsize=(30, 10 * rows))
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(rows, columns),  # creates grid of axes
                     axes_pad=0.4,  # pad between axes in inch.
                     )

    for ax, t in zip(grid, tms):
        with rasterio.open(normpath(join(bg_path, f'{t.lower()}.tif'))) as img:
            if show_parcel:
                for patch in patches:
                    ax.add_patch(copy(patch))
            show(img, ax=ax)
            ax.set_title(t, fontsize=20)

    if len(tms) > columns:
        for ax in grid[-((columns * rows - len(tms))):]:
            ax.remove()

    plt.show()


def by_pid(aoi, pid, chipsize=512, extend=512, tms=['Google'],
           columns=4, quit=True):
    """Show the background image with parcels polygon overlay by selected
    parcel id. This function will get an image from the center of the polygon.

    Examples:
        from cbm.view import background
        background.by_location(aoi, lon, lat, 512, 512, 'Google',
                                True, True)

    Arguments:
        aoi, the area of interest and year e.g.: es2020, cat2020 (str)
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        quiet, print or not procedure information (Boolean).
    """

    if type(tms) is str:
        tms = [tms]
    if len(tms) < columns:
        columns = len(tms)

    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            aoi, str(pid)))
    bg_path = normpath(join(workdir, 'backgrounds'))

    for t in tms:
        if not isfile(normpath(join(bg_path, f'{t.lower()}.tif'))):
            bg.by_pid(aoi, pid, chipsize, extend, t, True)

    with open(normpath(join(workdir, 'info.json')), 'r') as f:
        json_data = json.load(f)

    with rasterio.open(normpath(join(bg_path, f'{tms[0].lower()}.tif'))) as img:
        img_epsg = img.crs.to_epsg()
        geom = spatial_utils.transform_geometry(json_data, img_epsg)
        patches = overlay_parcel(img, geom)

    rows = int(len(tms) // columns + (len(tms) % columns > 0))
    fig = plt.figure(figsize=(30, 10 * rows))
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(rows, columns),  # creates grid of axes
                     axes_pad=0.4,  # pad between axes in inch.
                     )

    for ax, t in zip(grid, tms):
        with rasterio.open(normpath(join(bg_path, f'{t.lower()}.tif'))) as img:
            for patch in patches:
                ax.add_patch(copy(patch))
#             ax.xaxis.set_major_locator(ticker.MultipleLocator(200))
#             ax.xaxis.set_minor_locator(ticker.MultipleLocator(200))
            show(img, ax=ax)
            ax.set_title(t, fontsize=20)

    if len(tms) > columns:
        for ax in grid[-((columns * rows - len(tms))):]:
            ax.remove()

    plt.show()
