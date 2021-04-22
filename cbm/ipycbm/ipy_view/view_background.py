import json
import os.path
import matplotlib.pyplot as plt
from ipywidgets import Output, VBox, SelectionSlider
from mpl_toolkits.axes_grid1 import ImageGrid

import rasterio
from rasterio.plot import show
from descartes import PolygonPatch
from copy import copy
# import matplotlib.ticker as ticker
# import numpy as np

from cbm.utils import config, spatial_utils
from cbm.get import background as bg


def slider(aoi, pid, chipsize=512, extend=512, tms=['Google']):

    workdir = config.get_value(['paths', 'temp'])
    path = f'{workdir}/{aoi}/{pid}/'
    bg_path = f'{path}/backgrounds/'

    for t in tms:
        if not os.path.isfile(f'{bg_path}{t.lower()}.tif'):
            bg.by_pid(aoi, pid, chipsize, extend, t, True)

    with open(f'{path}info.json', "r") as f:
        json_data = json.load(f)

    def overlay_parcel(img, geom):
        patche = [PolygonPatch(feature, edgecolor="yellow",
                               facecolor="none", linewidth=2
                               ) for feature in geom['geom']]
        return patche

    with rasterio.open(f'{bg_path}{tms[0].lower()}.tif') as img:
        img_epsg = img.crs.to_epsg()
        geom = spatial_utils.transform_geometry(json_data, img_epsg)
        patches = overlay_parcel(img, geom)

    selection = SelectionSlider(
        options=tms,
        value=tms[0],
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True
    )
    output = Output()

    fig, ax = plt.subplots(figsize=(10, 10))
    with output:
        with rasterio.open(f'{bg_path}{selection.value.lower()}.tif') as img:
            for patch in patches:
                ax.add_patch(copy(patch))
            show(img, ax=ax)
        plt.show()

    def on_value_change(change):
        with output:
            output.clear_output()
            fig, ax = plt.subplots(figsize=(10, 10))
            with rasterio.open(f'{bg_path}{selection.value.lower()}.tif') as im:
                for patch in patches:
                    ax.add_patch(copy(patch))
                show(im, ax=ax)
            plt.show()

    selection.observe(on_value_change, names='value')
    return VBox([selection, output])


def maps(aoi, pid, chipsize=512, extend=512, tms='Google'):

    workdir = config.get_value(['paths', 'temp'])
    path = f'{workdir}/{aoi}/{pid}/backgrounds/'

    for t in tms:
        if not os.path.isfile(f'{path}{t.lower()}.png'):
            bg.by_pid(aoi, pid, chipsize, extend, t, True)

    columns = 5
    rows = int(len(tms) // columns + (len(tms) % columns > 0))
    fig = plt.figure(figsize=(25, 5 * rows))
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(rows, columns),  # creates grid of axes
                     axes_pad=0.1,  # pad between axes in inch.
                     )

    for ax, im in zip(grid, tms):
        # Iterating over the grid returns the Axes.
        ax.axis('off')
        ax.imshow(plt.imread(f'{path}{im.lower()}.png', 3))
        ax.set_title(im)

    plt.show()
