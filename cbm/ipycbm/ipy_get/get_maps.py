#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from cbm.utils import config

def base_map(area, source):
    from ipyleaflet import Map, Marker

    center, zoom = centroid(area, source)

    m = Map(center=center, zoom=zoom)

    base_map.map_marker = Marker(location=m.center)
    m += base_map.map_marker

    return m


def polygon_map(area, source):
    from ipyleaflet import Map, DrawControl

    center, zoom = centroid(area, source)

    m = Map(center=center, zoom=zoom)

    draw_control = DrawControl()
    draw_control.polygon = {
        "shapeOptions": {
            "fillColor": "#6be5c3",
            "color": "#6be5c3",
            "fillOpacity": 1.0
        },
        "drawError": {
            "color": "#dd253b",
            "message": "Oups!"
        },
        "allowIntersection": False
    }

    polygon_map.feature_collection = {
        'type': 'FeatureCollection',
        'features': []
    }

    def handle_draw(self, action, geo_json):
        """Do something with the GeoJSON when it's drawn on the map"""
        polygon_map.feature_collection['features'].append(geo_json)

    draw_control.on_draw(handle_draw)

    m.add_control(draw_control)

    return m


def polygon(area, source):
    # from ipywidgets import Textarea, Button, HBox, VBox
    from ipywidgets import Button, VBox
    # polygon = Textarea(
    #     value='',
    #     placeholder='List of polygon coordinates, or polygon in json format',
    #     description='Polygon:',
    #     disabled=False
    # )

    bt_show = Button(
        description='Show poly on map',
        disabled=True,
        button_style='info',
        tooltip='Show polygon on map below',
        icon=''
    )

    @bt_show.on_click
    def bt_show_on_click(b):
        pass

    # json_poly = HBox([polygon, bt_show])

    bt_get_ids = Button(
        description="Get parcels ids",
        disabled=False,
        button_style='info',
        tooltip='Get the ids of the parcels that are in the polygon',
        icon=''
    )

    @bt_get_ids.on_click
    def bt_get_ids_on_click(b):
        # from cbm.ipycbm.ipy_get import get_requests
        try:
            print(polygon_map.feature_collection['features'][0]['geometry'])
#             polyids = get_requests()
#             pids = [i[0] for i in polyids]
#             pids.pop(0)
        except Exception:
            print("No parcel ids found")

    wbox = VBox([polygon_map(area, source)])

    return wbox


def centroid(area, source):
    """Get the centroid for the selected area.
    """
    values = config.read()
    if source == 1:
        center = values['dataset'][area]['center'].split(",")
        zoom = values['dataset'][area]['zoom']
    else:
        if 'nld' in area:
            center, zoom = [52.13, 5.29], 10
        elif 'nrw' in area:
            center, zoom = [51.36, 7.32], 10
        elif 'es' in area:
            center, zoom = [41.85, 0.86], 10
        else:
            center, zoom = [45, 15], 4

    return [center, zoom]
