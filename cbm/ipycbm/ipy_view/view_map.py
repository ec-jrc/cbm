#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import json
import os.path
from os.path import join, normpath, isfile
from IPython.display import display
from ipywidgets import (HBox, VBox, Dropdown, Play, Layout, Label,
                        Checkbox, IntSlider, jslink, HTML, Output)
from ipyleaflet import (Map, ImageOverlay, Popup, basemap_to_tiles,
                        Polygon, WidgetControl, basemaps)

from cbm.utils import config, spatial_utils, raster_utils


def widget_box(path):
    map_view_box = Output()
    file_info = normpath(join(path, 'info.json'))

    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())

    pid = info_data['pid'][0]
    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]

    ci_path = normpath(join(path, 'chip_images'))

    ci_band = Dropdown(
        options=raster_utils.available_options(path, pid, False, False),
        disabled=False,
        layout=Layout(width='140px')
    )

    def ci_band_changed(b):
        #         m.substitute_layer()
        map_view_box.clear_output()
#         m.clear_layers()
#         m.clear_controls()
        with map_view_box:
            display(show_m())
    ci_band.observe(ci_band_changed)

    parcel_info = Label(
        f"Crop ID: {pid} Crop type: {crop_name},  Area: {area:.2f} sqm")

    display(HBox([parcel_info, ci_band]))

#     if os.path.exists(ci_path):

    def show_m():

        multipoly = []
        geom = spatial_utils.transform_geometry(info_data)
        poly = geom['geom'][0]['coordinates'][0]
    #     poly = spatial_utils.swap_xy(geom['coordinates'][0])[0]
        multipoly.append(poly)
        centroid = tuple([round(info_data['clat'][0], 4),
                          round(info_data['clon'][0], 4)])

        m = Map(center=centroid, zoom=15,
                basemap=basemaps.OpenStreetMap.Mapnik)

        polygon = Polygon(
            locations=multipoly,
            name='Parcel polygon',
            color="yellow",
            fill_color=None
        )

        m.add_layer(polygon)
        basemap2 = basemap_to_tiles(basemaps.Esri.WorldImagery)

        poly_text = HTML()
        poly_text.value = f"""Parcel ID: {pid}<br>
                                    Crop name: {crop_name}<br>
                                    Area: {area:.2f} sqm<br>
                                    Coordinates: {centroid}
                                    """
        poly_text.placeholder = "HTML"
        poly_text.description = ""

        # Popup with a given location on the map:
        poly_popup = Popup(
            location=centroid,
            child=poly_text,
            close_button=False,
            auto_close=False,
            close_on_escape_key=False
        )
        m.add_layer(poly_popup)

        polygon.popup = poly_popup  # Popup associated to a layer

        # Layers control
        show_poly = Checkbox(
            value=True,
            description='Polygon',
            indent=False,
            layout=Layout(width='140px')
        )
        show_sat = Checkbox(
            value=False,
            description='High res basemap',
            indent=False,
            layout=Layout(width='140px')
        )

        def polygon_changed(b):
            try:
                if show_poly.value is True:
                    m.add_layer(polygon)
                else:
                    m.remove_layer(polygon)
            except Exception:
                pass
        show_poly.observe(polygon_changed)

        def show_sat_changed(b):
            try:
                if show_sat.value is True:
                    m.add_layer(basemap2)
                else:
                    m.remove_layer(basemap2)
            except Exception:
                pass
        show_sat.observe(show_sat_changed)

        try:
            df = raster_utils.create_df(ci_path, pid, ci_band.value)

            geotiff = normpath(join(ci_path,
                                    f"{df['imgs'][0]}.{ci_band.value[0]}.tif"))
            bounds = raster_utils.bounds(geotiff)

            images = {}
            for i, row in df.iterrows():
                str_date = str(row['date'].date()).replace('-', '')
                img_tc = normpath(
                    join(ci_path, f"{('').join(ci_band.value)}_{str_date}.png"))

                # Create false color image if it does not exist
                # Merge bands (images path, export image path, bands list)
                if not isfile(img_tc):
                    imgs_path = normpath(join(ci_path, row['imgs']))
                    raster_utils.merge_bands(imgs_path, img_tc,
                                             ci_band.value)

                if bool(config.get_value(['set', 'jupyterlab'])) is True:
                    jlab_path = os.getcwd().replace(os.path.expanduser("~"), '')
                    image_path = normpath(join(f'files{jlab_path}', img_tc))
                else:
                    image_path = img_tc

                # print('image_path: ', image_path)
                images[i] = ImageOverlay(
                    url=image_path,
                    name=str_date,
                    bounds=(bounds)
                )

            # Time slider
            slider = IntSlider(
                value=1,
                min=1,
                max=len(images),
                step=1,
                description=str(df['date'][0].date()),
                continuous_update=False,
                orientation='horizontal',
                readout=True,
                readout_format='d'
            )
            show_chip = Checkbox(
                value=True,
                description='Chip image',
                indent=False,
                layout=Layout(width='140px')
            )

            def on_ci_band_change(change):
                pass
            ci_band.observe(on_ci_band_change, 'value')

            def show_chip_changed(b):
                try:
                    if show_chip.value is True:
                        m.add_layer(images[slider.value - 1])
                    else:
                        m.remove_layer(images[slider.value - 1])
                except Exception:
                    pass
            show_chip.observe(show_chip_changed)

            # Slider control
            play = Play(
                value=1,
                min=1,
                max=len(images),
                step=1,
                interval=1000,
                description="Press play",
            )

            def slider_changed(b):
                if show_chip.value is True:
                    try:
                        m.substitute_layer(
                            images[b['old'] - 1], images[b['new'] - 1])
                    except Exception:
                        pass
                    slider.description = str(
                        df['date'][slider.value - 1].date())

            slider.observe(slider_changed)
            jslink((play, 'value'), (slider, 'value'))
            time_box = HBox([slider, play])
            time_control = WidgetControl(
                widget=time_box, position='bottomleft')
            m.add_control(time_control)
            m.add_layer(images[0])

            map_options = VBox([show_poly, show_chip, show_sat])
        except Exception as err:
            map_options = VBox([show_poly, show_sat])
            print(err)

        layers_control = WidgetControl(
            widget=map_options, position='topright', max_width=150)
        m.add_control(layers_control)
        return m

    with map_view_box:
        display(show_m())

    return map_view_box
