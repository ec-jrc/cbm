#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


def pts_tstype():
    options = [
        ("NDVI", 'ndvi'),
        ("Sentinel-2 Level 2A", 's2'),
        ("S1 Backscattering Coefficients", 'bs'),
        ("S1 6-day Coherence (20m)", 'c6')
    ]
    return options


def pts_bands():
    options = {
        'bs': [('All Bands', ''),
               ('VV polarization', 'VV'),
               ('VH polarization', 'VH')],
        'c6': [('All Bands', ''),
               ('VV polarization', 'VV'),
               ('VH polarization', 'VH')],
        's2': [('All Bands', ''),
               ('Band 4 (RED, 10m)', 'B4'),
               ('Band 8 (NIR, 10m)', 'B8'),
               ('Scene Classification (SC 20m)', 'SC')]
    }
    return options


def pci_bands():
    """
    Sentinel-2 bands
    Band 1 – Coastal aerosol	442.7	21	442.2	21	60
    Band 2 – Blue	492.4	66	492.1	66	10
    Band 3 – Green	559.8	36	559.0	36	10
    Band 4 – Red	664.6	31	664.9	31	10
    Band 5 – Vegetation red edge	704.1	15	703.8	16	20
    Band 6 – Vegetation red edge	740.5	15	739.1	15	20
    Band 7 – Vegetation red edge	782.8	20	779.7	20	20
    Band 8 – NIR	832.8	106	832.9	106	10
    Band 8A – Narrow NIR	864.7	21	864.0	22	20
    Band 9 – Water vapour	945.1	20	943.2	21	60
    Band 10 – SWIR – Cirrus	1373.5	31	1376.9	30	60
    Band 11 – SWIR	1613.7	91	1610.4	94	20
    Band 12 – SWIR	2202.4	175	2185.7	185	20
    """
    options = {
        "Sentinel 1": ['VV', 'HH'],
        "Sentinel 2": [('Band 2 (10m)', 'B02'), ('Band 3 (10m)', 'B03'),
                       ('Band 4 (10m)', 'B04'), ('Band 8 (10m)', 'B08'),
                       ('Band 5 (20m)', 'B05'), ('Band 6 (20m)', 'B06'),
                       ('Band 7 (20m)', 'B07'), ('Band 8A (20m)', 'B8A'),
                       ('Band 11 (20m)', 'B11'), ('Band 12 (20m)', 'B12'),
                       ('Band SCL (20m)', 'SCL')]
    }
    return options


def cmaps(band):
    """
    Color maps:
    'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
    'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
    'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn'
    """
    colors = {"B01": "Greys",
              "B02": "Blues",
              "B03": "Greens",
              "B04": "Reds",
              "B05": "OrRd",
              "B06": "OrRd",
              "B07": "OrRd",
              "B08": "PuRd",
              "B8A": "RdPu",
              "B09": "BuGn",
              "B10": "Greys",
              "B11": "Greys",
              "B12": "Greys",
              "SCL": "gist_rainbow_r"
              }
    return colors[band]


def color_maps():
    colors = ['Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r',
              'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r',
              'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r',
              'Greys', 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r',
              'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r',
              'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn',
              'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r',
              'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r',
              'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r',
              'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3',
              'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn',
              'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd',
              'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary',
              'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r',
              'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm',
              'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r',
              'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray',
              'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar',
              'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern',
              'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot',
              'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot',
              'hot_r', 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r',
              'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean',
              'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism',
              'prism_r', 'rainbow', 'rainbow_r', 'seismic', 'seismic_r',
              'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r',
              'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r',
              'terrain', 'terrain_r', 'turbo', 'turbo_r', 'twilight',
              'twilight_r', 'twilight_shifted', 'twilight_shifted_r',
              'viridis', 'viridis_r', 'winter', 'winter_r'
              ]

    return colors

def eu_ms():
    ms = {
        "be": "Belgium",
        "bg": "Bulgaria",
        "cz": "Czechia",
        "dk": "Denmark",
        "de": "Germany",
        "ee": "Estonia",
        "ie": "Ireland",
        "el": "Greece",
        "es": "Spain",
        "fr": "France",
        "hr": "Croatia",
        "it": "Italy",
        "cy": "Cyprus",
        "lv": "Latvia",
        "lt": "Lithuania",
        "lu": "Luxembourg",
        "hu": "Hungary",
        "mt": "Malta",
        "nl": "Netherlands",
        "at": "Austria",
        "pl": "Poland",
        "pt": "Portugal",
        "ro": "Romania",
        "si": "Slovenia",
        "sk": "Slovakia",
        "fi": "Finland",
        "se": "Sweden"
         }
    return ms


def ms_polygons():
    ms_poly = {
        'Denmark':'8.0 54.8,8.0 57.0,10.7 57.8,13.2 55.2,15.3 55.3,15.4 54.9,12.0 54.5,8.0 54.7,8.0 54.8',
        'Catalunya (ES)':'0.58 40.5,3.33 41.8,3.33 42.5,0.61 42.9,0.04 40.7,0.58 40.5',
        'NL & NRW': '3.0 51.27,6.49 50.27,9.66 51.22,9.135 52.618,7.28 52.47,7.213 53.515,4.774 53.56,3.0 51.27'
    }

    return ms_poly

def dias_providers():
    return ['EOSC', 'CREODIAS', 'MUNDI', 'SOBLOO', 'ONDA', 'WEKEO']
