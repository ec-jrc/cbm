#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Version   : 1.0 - 2020-04-05

"""Simple image processing routines for client side chip handling"""


import rasterio
import numpy as np
from matplotlib import cm

def normalizedDifference(band0, band1, output):
    # Calculates the normalized difference between 2 input bands
    # band0, band1  - rasterio readable object
    # output        - rasterio writable object
    with rasterio.open(band0) as b0:
        band_0 = b0.read(1)
        kwargs = b0.meta
    with rasterio.open(band1) as b1:
        band_1 = b1.read(1)
    # Allow division by zero
    np.seterr(divide='ignore', invalid='ignore')
    # Calculate NDVI
    nd = (band_0.astype(float) - band_1.astype(float)) / (band_0 + band_1)
    # Set spatial characteristics of the output object to mirror the input
    kwargs.update(
        dtype=rasterio.float32,
        count = 1)
    # Create the file
    with rasterio.open(output, 'w', **kwargs) as dst:
            dst.write_band(1, nd.astype(rasterio.float32))
    return True

def scaled_palette(band, min, max, matplot_cmap):
    # Scales band to a np.uint8 image, clipping between min and max and
    # assigns a matplotlib cmap of colormap
    # Check:
    # https://matplotlib.org/3.1.1/gallery/color/colormap_reference.html
    
    cmap = cm.get_cmap(matplot_cmap, 256)

    cmap = (255.0*cmap(range(256))).astype(np.uint8)

    lut = {}
    for i in range(256):
        lut[i] = tuple(cmap[i].astype(np.uint8))

    with rasterio.Env():

        with rasterio.open(band) as src:
            image = src.read(1)
            meta = src.meta

            image = np.clip(255 * (image - min) /(max - min), 0, 255).astype(np.uint8)
            meta['dtype'] = rasterio.uint8
            print(meta)
            with rasterio.open(band.replace('.tif', '_scaled.tif'), 'w', **meta) as dst:
                dst.write(image, indexes=1)
                dst.write_colormap(1, lut)