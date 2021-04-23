#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import glob
import rasterio
import rasterio.warp
import rasterio.features
import numpy as np
import pandas as pd
from os.path import join, normpath


def available_options(ci_path, pid, ndvi=True, individual=True):
    """
    Get available band combination options.
    Args:
        ci_path: Images path
        pid: Parcel id
    """

    ci_path = normpath(join(ci_path, 'chip_images'))
    csv_lists = glob.glob(normpath(join(ci_path, 'images_list.*.csv')))
    bands_list = [i.split('.')[-2] for i in csv_lists]

    available = []
    options = {}
    options['True color'] = ['B02', 'B03', 'B04']
    options['False color 1'] = ['B04', 'B11', 'B08']
    options['False color 2'] = ['B03', 'B04', 'B08']
    if ndvi:
        options['NDVI'] = ['B04', 'B08']

    for key in options:
        if all(b in bands_list for b in options[key]):
            available.append((f"{key} ({(', ').join(options[key])})",
                              options[key]))

    if individual:
        available.extend([(f'Band {b}', [b]) for b in bands_list])

    return available


def create_df(path, pid, bands):
    """
    Create dataframe with the available downloaded images.
    Args:
        path: the path to the images (str)
        pid: the parcel id (int)
        bands: selected the band or bands (str)
    Returns:
        Dataframe (df)
    """
    csv_list = normpath(join(path, f'images_list.{bands[0]}.csv'))
    df = pd.read_csv(csv_list, index_col=0)
    df['date'] = df['dates'].str[0:8]
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

    # Filter df to remove dates with missing bands.
    if len(bands) > 1:
        for b in bands:
            csv_list_b = normpath(join(path, f'images_list.{b}.csv'))
            df_b = pd.read_csv(csv_list_b, index_col=0)
            df_b['date'] = df_b['dates'].str[0:8]
            df_b['date'] = pd.to_datetime(df_b['date'], format='%Y%m%d')
            df = df[df['date'].isin(df_b['date'])]

    df['imgs'] = df['chips'].str.split('/').str[-1]
    df['imgs'] = df['imgs'].str.split('.').str[0]
    # source = df['chips'][0].split('/')[1]
    df = df.drop(['dates', 'chips'], axis=1)
    df = df.sort_values(by='date')

    return df


def merge_bands(imgs_path, dst_file, bands, percent=(5, 95)):
    from skimage import exposure
    import numpy as np
    import rasterio
    """
    Mix any bands
    Args:
        imgs_path: The images path.
        dst_file: Destination file with .tif extension.
        bands: List of bands must be three.
    Returns:
        None
    Example:
        merge_bands(images/image_, "TrueColor.tif",
                                ['B02', 'B03', 'B04'])

    """
    trsfrm = False

    bafs = {}  # Band files
    bads = {}  # rasterio opened files
    bash = {}  # Image pixel size
    for b in bands:
        bafs[b] = f"{imgs_path}.{b}.tif"
        bads[b] = rasterio.open(bafs[b], format='GTiff')
        bash[b] = (bads[b].width, bads[b].height)
        if next(iter(bash)) != bash[b]:
            trsfrm = True

    if trsfrm is True:
        from rasterio.enums import Resampling
        maxw = max([bash[w][0] for w in bash])
        maxh = max([bash[h][1] for h in bash])
        blist = [bads[bands[bands.index(b)]].read(
            out_shape=(bads[bands[bands.index(b)]].count, maxw, maxh),
            resampling=Resampling.bilinear)[0, :, :] for b in bands]
    else:
        blist = [bads[bands[bands.index(b)]].read(1) for b in bands]

    rescale = []
    for i in blist:
        rimg = np.true_divide(i, [255], out=None)
        rimg *= 255 / rimg.max()
        rimg = rimg.astype(np.uint16)
        p5, p95 = np.percentile(rimg, percent)
        rimg = exposure.rescale_intensity(rimg, in_range=(p5, p95))
        rescale.append(rimg)

    img_tc = np.array(rescale).transpose(1, 0, 2)

    # Update profile
    img_tc = img_tc.astype(np.uint16)
    profile = bads[bands[0]].profile
    profile.update(
        dtype=rasterio.uint16,
        count=len(bands),
        compress='lzw',
        driver='PNG',
        transform=bads[bands[0]].transform)

    with rasterio.open(dst_file, 'w', **profile) as dst:
        for b in bands:
            rindex = (len(bands) - 1) - bands.index(b)
            img = img_tc[:, rindex]
            dst.write(img, bands.index(b) + 1)

    for b in bands:
        bads[b].close()


def calc_ndvi(imgs_path, dst_file, bands, percent=(5, 95)):
    import numpy as np
    import rasterio
    from skimage import exposure

    b4f = f"{imgs_path}.B04.tif"
    b8f = f"{imgs_path}.B08.tif"

    b4 = rasterio.open(b4f, format='GTiff')
    b8 = rasterio.open(b8f, format='GTiff')

    b4_read = b4.read()
    b8_read = b8.read()
    b4_read = np.true_divide(b4_read, [255], out=None)
    b4_read *= 255 / b4_read.max()
    b4_read = b4_read.astype(np.uint16)
    b4_p5, b4_p95 = np.percentile(b4_read, percent)
    b4_read = exposure.rescale_intensity(b4_read, in_range=(b4_p5, b4_p95))

    b8_read = np.true_divide(b8_read, [255], out=None)
    b8_read *= 255 / b8_read.max()
    b8_read = b8_read.astype(np.uint16)
    b8_p5, b8_p95 = np.percentile(b8_read, percent)
    b8_read = exposure.rescale_intensity(b8_read, in_range=(b8_p5, b8_p95))

    # Update profile
    profile = b4.profile
    profile.update(
        dtype=rasterio.uint16,
        count=1,
        compress='lzw',
        driver='PNG',
        transform=b4.transform)

    # Calculate NDVI
    vis = b4_read[:, :].astype(float)
    nir = b8_read[:, :].astype(float)

    ndvi = np.divide((nir - vis), (nir + vis))
    ndvi[np.isnan(ndvi)] = 0

    b4.close()
    b8.close()

    return ndvi


def bounds(geotiff):

    """
    Args:
        geotiff: A tiff type image with georeferencing information.
    Returns:
        img_bounds: The bounds of the geotiff.
    Example:
        (13, -130), (32, -100) # SW and NE corners of the image
    """
    with rasterio.open(geotiff) as dataset:
        # Read the dataset's valid data mask as a ndarray.
        mask = dataset.dataset_mask().astype(np.uint16)

        # Extract feature shapes and values from the array.
        for geom, val in rasterio.features.shapes(
                mask, transform=dataset.transform):

            # Transform shapes from the dataset's own coordinate
            # reference system to CRS84 (EPSG:4326).
            geom = rasterio.warp.transform_geom(
                dataset.crs, 'EPSG:4326', geom, precision=6)

            # Print GeoJSON shapes to stdout.
            img_bounds = ((geom['coordinates'][0][1][1],
                           geom['coordinates'][0][1][0]),
                          (geom['coordinates'][0][3][1],
                           geom['coordinates'][0][3][0]))

    return img_bounds
