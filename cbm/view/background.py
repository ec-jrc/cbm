#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import re
import json
import rasterio
import requests
import matplotlib.pyplot as plt
from rasterio.plot import show
from descartes import PolygonPatch

from cbm.get import background
from cbm.sources import api
from cbm.view import spatial_utils

def by_location(aoi, year, lon, lat, chipsize=512, extend=512, tms='Google', prefix='', folder='temp', quiet=True):
    """Download the background image with parcels polygon overlay by selected location.

    Examples:
        from cbm.view import background
        background.by_location(aoi, year, lon, lat, 512, 512, 'Google', 'temp/test.tif', True)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        lon, lat, longitude and latitude in decimal degrees (float).
        chipsize, size of the chip in pixels (int).
        extend, size of the chip in meters  (float).
        tms, tile map server Google or Bing (str).
        prefix, the name of the output file (str).
        folder, the folder to be stored (str).
        quiet, print or not procedure information (Boolean).

    """
    json_data = json.loads(api.ploc(aoi, year, lon, lat, True))
    with open(f'{folder}/{prefix}info.json', "w") as f:
        json.dump(json_data, f)

    background.main(lon, lat, chipsize, extend, tms, f'{folder}{tms}.tif')

    with rasterio.open(f'{folder}/{prefix}{tms}.tif') as img:
        def overlay_parcel(img, json_data):
            img_epsg = img.crs.to_epsg()
            geo_json = spatial_utils.transform_geometry(
                json_data, img_epsg)
            patche = [PolygonPatch(feature, edgecolor="yellow",
                                   facecolor="none", linewidth=2
                                   ) for feature in [geo_json]]
            return patche

        ax = plt.gca()
        for p in overlay_parcel(img, json_data):
            ax.add_patch(p)

        show(img, ax=ax)

        if prefix:
            plt.savefig(f'{folder}/{prefix}{tms}.png', dpi=None, facecolor='w', edgecolor='w',
                    orientation='portrait', format=None,
                    transparent=False, bbox_inches=None, pad_inches=0.1,
                    metadata=None)
        else:
            plt.show()


if __name__ == "__main__":
    import sys
    main(sys.argv)