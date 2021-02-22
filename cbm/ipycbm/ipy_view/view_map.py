#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import glob
import json
import os.path
import pandas as pd
from IPython.display import display
from ipywidgets import (HBox, VBox, Dropdown, Play, Layout, Label,
                        Checkbox, IntSlider, jslink, HTML, Output)
from ipyleaflet import (Map, ImageOverlay, Popup, basemap_to_tiles,
                        Polygon, WidgetControl, basemaps)

from cbm.utils import config, spatial
from cbm.ipycbm.ipy_view import view_images


def widget_box(path):
    map_view_box = Output()
    file_info = glob.glob(f"{path}*_information.json")[0]

    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())

    pid = info_data['ogc_fid'][0]
    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]

    ci_path = f"{path}{pid}_chip_images/"
    csv_lists = glob.glob(f"{ci_path}{pid}_images_list.*.csv")
    bands_list = [i.split('.')[-2] for i in csv_lists]

    ci_band = Dropdown(
        options=view_images.available_options(path, pid, False, False),
        disabled=False,
        layout=Layout(width='140px')
    )
    ci_cloud = Checkbox(
        value=False,
        description='Cloud free',
        disabled=True,
        indent=False,
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
        multycent = []
        geom = spatial.transform_geometry(info_data)
        poly = geom['coordinates'][0][0]
    #     poly = spatial.swap_xy(geom['coordinates'][0])[0]
        multipoly.append(poly)
        cent = spatial.centroid(poly)
        multycent.append(cent)

        cent = spatial.centroid(multycent)
        m = Map(center=cent, zoom=16, basemap=basemaps.OpenStreetMap.Mapnik)

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
                                    Coordinates: {cent}
                                    """
        poly_text.placeholder = "HTML"
        poly_text.description = ""

        # Popup with a given location on the map:
        poly_popup = Popup(
            child=poly_text,
            close_button=False,
            auto_close=False,
            close_on_escape_key=False
        )
        m.add_layer(poly_popup)

        # Popup associated to a layer
        polygon.popup = poly_popup

        # Layers control
        show_poly = Checkbox(
            value=True,
            description='Polygon',
            disabled=False,
            indent=False,
            layout=Layout(width='140px')
        )
        show_sat = Checkbox(
            value=False,
            description='High res basemap',
            disabled=False,
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
            csv_list = f"{ci_path}{pid}_images_list.{ci_band.value[0]}.csv"
            df = view_images.create_df(ci_path, pid, ci_band.value)

            geotiff = f"{ci_path}{df['imgs'][0]}.{ci_band.value[0]}.tif"
            bounds = spatial.bounds(geotiff)

            images = {}
            for i, row in df.iterrows():
                str_date = str(row['date'].date()).replace('-', '')
                workdir = os.getcwd().split('/')[-1]
                img_tc = f"{ci_path}{('').join(ci_band.value)}_{str_date}.png"

                # Create false color image if it does not exist
                # Merge bands (images path, export image path, bands list)
                if not os.path.isfile(img_tc):
                    imgs_path = f"{ci_path}{row['imgs']}"
                    view_images.merge_bands(imgs_path, img_tc,
                                             ci_band.value)
                values = config.read()

                # Set the current environment
                if eval(values['set']['jupyterlab']) is True:
                    image_path = f'files/{workdir}/{img_tc}'
                else:
                    image_path = img_tc
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
                disabled=False,
                continuous_update=False,
                orientation='horizontal',
                readout=True,
                readout_format='d'
            )
            show_chip = Checkbox(
                value=True,
                description='Chip image',
                disabled=False,
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
                disabled=False
            )

            def slider_changed(b):
                if show_chip.value is True:
                    try:
                        m.substitute_layer(
                            images[b['old'] - 1], images[b['new'] - 1])
                    except Exception:
                        pass
                    slider.description = str(df['date'][slider.value - 1].date())

            slider.observe(slider_changed)
            jslink((play, 'value'), (slider, 'value'))
            time_box = HBox([slider, play])
            time_control = WidgetControl(widget=time_box, position='bottomleft')
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
