#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import json
import glob
import rasterio
import matplotlib.pyplot as plt
from copy import copy
from os.path import join, normpath, isfile
from descartes import PolygonPatch
from rasterio.plot import show
from mpl_toolkits.axes_grid1 import ImageGrid

from cbm.utils import config, spatial_utils
from cbm.get import background as get_bg
from cbm.get import parcel_info


def overlay_parcel(img, geom):
    """Create parcel polygon overlay"""
    patche = [PolygonPatch(feature, edgecolor="yellow",
                           facecolor="none", linewidth=2
                           ) for feature in geom['geom']]
    return patche


def by_location(aoi, year, lon, lat, chipsize=512, extend=512, tms=['google'],
                ptype=None, columns=4, debug=False):
    """Show the background image with parcels polygon overlay by selected
    parcel id. This function will get an image from the center of the polygon.

    Examples:
        from cbm.view import background
        background.by_location(aoi, year, lon, lat, 512, 512, 'Google',
                                True, True)

    Arguments:
        aoi, the area of interest (str)
        year, the year of parcels table
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        columns, the number of columns of the grid
        debug, print or not procedure information (Boolean).
    """
    if type(tms) is str:
        tms = [tms]
    if len(tms) < columns:
        columns = len(tms)

    try:
        parcel = parcel_info.by_location(aoi, year, lon, lat, ptype,
                                         True, False, debug)
        if type(parcel['pid']) is list:
            pid = parcel['pid'][0]
        else:
            pid = parcel['pid']

        workdir = normpath(join(config.get_value(['paths', 'temp']),
                                aoi, str(year), str(pid)))
        parcel_id = True
    except Exception as err:
        workdir = normpath(join(config.get_value(['paths', 'temp']), aoi,
                                str(year), f'_{lon}_{lat}'.replace('.', '_')))
        parcel_id = False
        if debug:
            print("No parcel information found.", err)

    bg_path = normpath(join(workdir, 'backgrounds'))

    same_args = check_args(bg_path, chipsize, extend, debug)

    if debug:
        print('path: ', bg_path)
        print('same args: ', same_args)
        print('aoi-year-lon-lat-chipsize-extend-tms-ptype-columns-debug')
        print(aoi, year, lon, lat, chipsize,
              extend, tms, ptype, columns, debug)

    for t in tms:
        if not isfile(normpath(join(bg_path, f'{t.lower()}.tif'))) or not same_args:
            if parcel_id:
                get_bg.by_pid(aoi, year, pid, chipsize,
                              extend, t, ptype, True, debug)
            else:
                get_bg.by_location(aoi, year, lon, lat, chipsize,
                                   extend, t, ptype, True, debug)

    if parcel_id:
        with open(normpath(join(workdir, 'info.json')), 'r') as f:
            parcel = json.load(f)

        with rasterio.open(normpath(join(bg_path,
                                         f'{tms[0].lower()}.tif'))) as img:
            img_epsg = img.crs.to_epsg()
            geom = spatial_utils.transform_geometry(parcel, img_epsg)
            patches = overlay_parcel(img, geom)

    rows = int(len(tms) // columns + (len(tms) % columns > 0))
    fig = plt.figure(figsize=(30, 10 * rows))
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(rows, columns),  # creates grid of axes
                     axes_pad=0.4,  # pad between axes in inch.
                     )

    def overlay_title(img, date):
        date_text = ax.text(
            img.bounds.left + ((img.bounds.right - img.bounds.left) / 9),
            img.bounds.bottom + ((img.bounds.top - img.bounds.bottom) / 1.15),
            date, color='yellow', weight='bold', size=32 - columns * 2,
            bbox=dict(boxstyle="round", ec='yellow', fc='black', alpha=0.2))
        return date_text

    for ax, t in zip(grid, tms):
        with rasterio.open(normpath(join(bg_path, f'{t.lower()}.tif'))) as img:
            if parcel_id:
                for patch in patches:
                    ax.add_patch(copy(patch))
            overlay_title(img, t)
            show(img, ax=ax)
#            ax.xaxis.set_major_locator(ticker.MultipleLocator(200))

    if len(tms) > columns and columns * rows > len(tms):
        for ax in grid[-((columns * rows - len(tms))):]:
            ax.remove()

    plt.show()


def by_pid(aoi, year, pid, chipsize=512, extend=512, tms=['google'],
           ptype=None, columns=4, debug=False):
    """Show the background image with parcels polygon overlay by selected
    parcel id. This function will get an image from the center of the polygon.

    Examples:
        from cbm.view import background
        background.by_location(aoi, year, lon, lat, 512, 512, 'Google',
                                True, True)

    Arguments:
        aoi, the area of interest (str)
        year, the year of parcels table
        pid, the parcel id (str).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        columns, the number of columns of the grid
        debug, print or not procedure information (Boolean).
    """
    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            aoi, str(year), str(pid)))
    file_info = normpath(join(workdir, 'info.json'))
    if not isfile(file_info):
        if not parcel_info.by_pid(aoi, str(year), str(pid), ptype, True):
            return "No parcel found, please check the parcel ID"

    if type(tms) is str:
        tms = [tms]
    if len(tms) < columns:
        columns = len(tms)

    bg_path = normpath(join(workdir, 'backgrounds'))
    same_args = check_args(bg_path, chipsize, extend, debug)

    if debug:
        print('path: ', bg_path)
        print('same args: ', same_args)
        print('aoi, year, pid, chipsize, extend, tms, columns, debug')
        print(aoi, year, pid, chipsize, extend, tms, columns, debug)

    for t in tms:
        if not isfile(normpath(join(bg_path, f'{t.lower()}.tif'))) or not same_args:
            get_bg.by_pid(aoi, year, pid, chipsize,
                          extend, t, ptype, True, debug)

    with open(file_info, 'r') as f:
        parcel = json.load(f)

    with rasterio.open(normpath(join(bg_path, f'{tms[0].lower()}.tif'))) as img:
        img_epsg = img.crs.to_epsg()
        geom = spatial_utils.transform_geometry(parcel, img_epsg)
        patches = overlay_parcel(img, geom)

    rows = int(len(tms) // columns + (len(tms) % columns > 0))
    fig = plt.figure(figsize=(30, 10 * rows))
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(rows, columns),  # creates grid of axes
                     axes_pad=0.4)  # pad between axes in inch.

    def overlay_title(img, date):
        date_text = ax.text(
            img.bounds.left + ((img.bounds.right - img.bounds.left) / 9),
            img.bounds.bottom + ((img.bounds.top - img.bounds.bottom) / 1.15),
            date, color='yellow', weight='bold', size=32 - columns * 2,
            bbox=dict(boxstyle="round", ec='yellow', fc='black', alpha=0.2))
        return date_text

    for ax, t in zip(grid, tms):
        with rasterio.open(normpath(join(bg_path, f'{t.lower()}.tif'))) as img:
            for patch in patches:
                ax.add_patch(copy(patch))
            overlay_title(img, t)
            show(img, ax=ax)
#            ax.xaxis.set_major_locator(ticker.MultipleLocator(200))

    if len(tms) > columns and columns * rows > len(tms):
        for ax in grid[-((columns * rows - len(tms))):]:
            ax.remove()

    plt.show()


def check_args(path, chipsize, extend, debug=False):
    """
    Summary :
        Check if the chipsize and extend are the same with the last requst.

    Arguments:
        path, the path for the backroud images of the selected parcel
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).

    Returns:
        True or False.
    """
    if os.path.isdir(path):
        last_par = glob.glob(f"{path}/chipsize_extend_*")
        if last_par != []:
            last_chipsize = int(last_par[0].split('_')[-2])
            last_extend = float(last_par[0].split('_')[-1])
            if debug:
                print('last_chipsize:', last_chipsize,
                      ', last_extend:', last_extend)
            if last_chipsize != chipsize or last_extend != extend:
                os.rename(rf'{last_par[0]}',
                          rf'{path}/chipsize_extend_{chipsize}_{extend}')
                return False
            else:
                return True
        else:
            with open(f"{path}/chipsize_extend_{chipsize}_{extend}", "w") as f:
                f.write('')
            return False
    else:
        return False
