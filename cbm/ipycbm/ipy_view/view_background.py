import os
import os.path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from ipywidgets import Output, VBox, SelectionSlider
from mpl_toolkits.axes_grid1 import ImageGrid

from cbm.utils import config
from cbm.get import background as bg


def slider(aoi, year, pid, chipsize=512, extend=512, tms=['Google']):

    workdir = config.get_value(['paths', 'temp'])
    path = f'{workdir}/{aoi}{year}/pid{pid}/background/'

    for t in tms:
        if not os.path.isfile(f'{path}{t.lower()}.png'):
            bg.by_pid(aoi, year, pid, chipsize, extend, t, True)

    selection = SelectionSlider(
        options=tms,
        value=tms[0],
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True
    )
    output = Output()

    with output:
        img = mpimg.imread(f'{path}{selection.value.lower()}.png')
        plt.imshow(img)
        plt.axis('off')
        plt.show()

    def on_value_change(change):
        with output:
            output.clear_output()
            img = mpimg.imread(f'{path}{selection.value.lower()}.png')
            plt.imshow(img)
            plt.axis('off')
            plt.show()

    selection.observe(on_value_change, names='value')
    return VBox([selection, output])


def grid(aoi, year, pid, chipsize=512, extend=512, tms='Google'):

    workdir = config.get_value(['paths', 'temp'])
    path = f'{workdir}/{aoi}{year}/pid{pid}/background/'

    for t in tms:
        if not os.path.isfile(f'{path}{t.lower()}.png'):
            bg.by_pid(aoi, year, pid, chipsize, extend, t, True)

    columns = 5
    rows = int(len(tms) // columns + (len(tms) % columns > 0))
    fig = plt.figure(figsize=(25, 5 * rows))
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(rows, columns),  # creates 2x2 grid of axes
                     axes_pad=0.1,  # pad between axes in inch.
                     )

    for ax, im in zip(grid, tms):
        # Iterating over the grid returns the Axes.
        ax.axis('off')
        ax.imshow(plt.imread(f'{path}{im.lower()}.png', 3))
        ax.set_title(im)

    plt.show()
