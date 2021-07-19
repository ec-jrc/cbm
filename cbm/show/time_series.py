#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from os.path import join, normpath, isfile
from datetime import timedelta

from cbm.utils import config
from cbm.get import parcel_info, time_series


def ndvi(aoi, pid):

    path = normpath(join(config.get_value(['paths', 'temp']), aoi, str(pid)))
    file_info = normpath(join(path, 'info.json'))
    if not isfile(file_info):
        parcel_info.by_pid(aoi, pid)
    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())

    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]

    file_ts = normpath(join(path, 'time_series_s2.csv'))
    if not isfile(file_ts):
        time_series.by_pid(aoi, pid, 's2')
    df = pd.read_csv(file_ts, index_col=0)

    df['date'] = pd.to_datetime(df['date_part'], unit='s')
    start_date = df.iloc[0]['date'].date()
    end_date = df.iloc[-1]['date'].date()
    # print(f"From '{start_date}' to '{end_date}'.")

    pd.set_option('max_colwidth', 200)
    pd.set_option('display.max_columns', 20)

    # Plot settings are confirm IJRS graphics instructions
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 14

    df.set_index(['date'], inplace=True)

    dfB4 = df[df.band.isin(['B4', 'B04'])].copy()
    dfB8 = df[df.band.isin(['B8', 'B08'])].copy()
    datesFmt = mdates.DateFormatter('%-d %b %Y')

    # Plot Cloud free NDVI.
    dfNDVI = (dfB8['mean'] - dfB4['mean']) / (dfB8['mean'] + dfB4['mean'])

    dfSC = df[df.band == 'SC'].copy()
    cloudfree = ((dfSC['mean'] >= 4) & (dfSC['mean'] < 6))

    fig = plt.figure(figsize=(16.0, 10.0))
    axb = fig.add_subplot(1, 1, 1)

    axb.set_title(f"Parcel {pid} (crop: {crop_name}, area: {area:.2f} sqm)")

    axb.set_xlabel("Date")
    axb.xaxis.set_major_formatter(datesFmt)

    axb.set_ylabel(r'NDVI')
    axb.plot(dfNDVI.index, dfNDVI, linestyle=' ', marker='s',
             markersize=10, color='DarkBlue',
             fillstyle='none', label='NDVI')
    try:
        axb.plot(dfNDVI[cloudfree].index, dfNDVI[cloudfree],
                 linestyle=' ', marker='P',
                 markersize=10, color='Red',
                 fillstyle='none', label='Cloud free NDVI')
    except Exception as err:
        message = f"Could not mark cloud free images: {err}"

    axb.set_xlim(start_date, end_date + timedelta(1))
    axb.set_ylim(0, 1.0)

    axb.legend(frameon=False)  # loc=2)

    if 'message' in locals():
        print(message)

    return plt.show()


def s2(aoi, pid, bands):
    if type(bands) is str:
        bands = [bands]
    path = normpath(join(config.get_value(['paths', 'temp']), aoi, str(pid)))
    file_info = normpath(join(path, 'info.json'))
    if not isfile(file_info):
        parcel_info.by_pid(aoi, pid)
    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())

    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]

    file_ts = normpath(join(path, 'time_series_s2.csv'))
    if not isfile(file_ts):
        time_series.by_pid(aoi, pid, 'st')
    df = pd.read_csv(file_ts, index_col=0)

    df['date'] = pd.to_datetime(df['date_part'], unit='s')
    start_date = df.iloc[0]['date'].date()
    end_date = df.iloc[-1]['date'].date()
    # print(f"From '{start_date}' to '{end_date}'.")

    pd.set_option('max_colwidth', 200)
    pd.set_option('display.max_columns', 20)

    # Plot settings are confirm IJRS graphics instructions
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 14

    df.set_index(['date'], inplace=True)

    dfb = {}
    for b in bands:
        if b[1] == '0':
            bz = [b, f'{b[0]}{b[-1]}']
        elif b in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9']:
            bz = [b, f'{b[0]}0{b[-1]}']
        dfb[b] = df[df.band.isin(bz)].copy()

    dfSC = df[df.band == 'SC'].copy()
    cloudfree = ((dfSC['mean'] >= 4) & (dfSC['mean'] < 6))

    datesFmt = mdates.DateFormatter('%-d %b %Y')

    # Plot Band
    fig = plt.figure(figsize=(16.0, 10.0))
    axb = fig.add_subplot(1, 1, 1)

    axb.set_title(f"Parcel {pid} (crop: {crop_name}, area: {area:.2f} ha)")
    axb.set_xlabel("Date")
    axb.xaxis.set_major_formatter(datesFmt)

    axb.set_ylabel(r'DN')

    colors = {"B01": "Grey",
              "B02": "Blue",
              "B03": "Green",
              "B04": "Red",
              "B05": "Grey",
              "B06": "Grey",
              "B07": "Grey",
              "B08": "magenta",
              "B8A": "Grey",
              "B09": "Grey",
              "B10": "Grey",
              "B11": "Grey",
              "B12": "Grey",
              "SCL": "yellow",
              "B1": "Grey",
              "B2": "Blue",
              "B3": "Green",
              "B4": "Red",
              "B5": "Grey",
              "B6": "Grey",
              "B7": "Grey",
              "B8": "magenta",
              "B9": "Grey"
              }

    seriesB = {}
    for b in bands:
        axb.plot(dfb[b].index, dfb[b]['mean'], linestyle=' ', marker='o',
                 markersize=8, color=colors[b],
                 fillstyle='none', label=b)

        seriesB[b] = pd.Series(dfb[b]['mean'], index=dfb[b].index)
        try:
            axb.plot(seriesB[b][cloudfree].index, seriesB[b][cloudfree],
                     linestyle=' ', marker='x',
                     markersize=8, color=colors[b],
                     fillstyle='none', label=f'{b} Cloud free')
        except Exception as err:
            message = f"Could not mark cloud free images: {err}"

    axb.set_xlim(start_date, end_date + timedelta(1))
    axb.set_ylim(0, 10000)

    axb.legend(frameon=False)

    if 'message' in locals():
        print(message)

    return plt.show()


def s1_bs(aoi, pid):
    path = normpath(join(config.get_value(['paths', 'temp']), aoi, str(pid)))
    file_info = normpath(join(path, 'info.json'))
    if not isfile(file_info):
        parcel_info.by_pid(aoi, pid)
    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())

    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]

    file_ts = normpath(join(path, 'time_series_bs.csv'))
    if not isfile(file_ts):
        time_series.by_pid(aoi, pid, 'bs')
    df = pd.read_csv(file_ts, index_col=0)

    df['date'] = pd.to_datetime(df['date_part'], unit='s')
    start_date = df.iloc[0]['date'].date()
    end_date = df.iloc[-1]['date'].date()
    # print(f"From '{start_date}' to '{end_date}'.")

    pd.set_option('max_colwidth', 200)
    pd.set_option('display.max_columns', 20)

    # Plot settings are confirm IJRS graphics instructions
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 14

    df.set_index(['date'], inplace=True)
    datesFmt = mdates.DateFormatter('%-d %b %Y')

    # Plot Backscattering coefficient
    datesFmt = mdates.DateFormatter('%-d %b %Y')
    df = df[df['mean'] >= 0]  # to remove negative values

    dfVV = df[df.band == 'VV'].copy()
    dfVH = df[df.band == 'VH'].copy()
    fig = plt.figure(figsize=(16.0, 10.0))
    axb = fig.add_subplot(1, 1, 1)

    dfVV['mean'] = dfVV['mean'].map(lambda s: 10.0 * np.log10(s))
    dfVH['mean'] = dfVH['mean'].map(lambda s: 10.0 * np.log10(s))

    axb.set_title(
        f"Parcel {pid} (crop: {crop_name}, area: {area:.2f} sqm)")
    axb.set_xlabel("Date")
    axb.xaxis.set_major_formatter(datesFmt)

    axb.set_ylabel(r'Backscattering coefficient, $\gamma\degree$ (dB)')
    axb.plot(dfVH.index, dfVH['mean'], linestyle=' ', marker='s',
             markersize=10, color='DarkBlue', fillstyle='none', label='VH')
    axb.plot(dfVV.index, dfVV['mean'], linestyle=' ', marker='o',
             markersize=10, color='Red', fillstyle='none', label='VV')

    axb.set_xlim(start_date, end_date + timedelta(1))
    axb.set_ylim(-25, 0)

    axb.legend(frameon=False)  # loc=2)

    return plt.show()


def s1_c6(aoi, pid):
    path = normpath(join(config.get_value(['paths', 'temp']), aoi, str(pid)))
    file_info = normpath(join(path, 'info.json'))
    if not isfile(file_info):
        parcel_info.by_pid(aoi, pid)
    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())

    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]

    file_ts = normpath(join(path, 'time_series_c6.csv'))
    if not isfile(file_ts):
        time_series.by_pid(aoi, pid, 'c6')
    df = pd.read_csv(file_ts, index_col=0)

    df['date'] = pd.to_datetime(df['date_part'], unit='s')
    start_date = df.iloc[0]['date'].date()
    end_date = df.iloc[-1]['date'].date()
    # print(f"From '{start_date}' to '{end_date}'.")

    pd.set_option('max_colwidth', 200)
    pd.set_option('display.max_columns', 20)
    datesFmt = mdates.DateFormatter('%-d %b %Y')

    # Plot settings are confirm IJRS graphics instructions
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 14

    df.set_index(['date'], inplace=True)

    # Plot Coherence

    dfVV = df[df.band == 'VV'].copy()
    dfVH = df[df.band == 'VH'].copy()
    fig = plt.figure(figsize=(16.0, 10.0))
    axb = fig.add_subplot(1, 1, 1)

    axb.set_title(
        f"Parcel {pid} (crop: {crop_name}, area: {area:.2f} sqm)")
    axb.set_xlabel("Date")
    axb.xaxis.set_major_formatter(datesFmt)

    axb.set_ylabel(r'Coherence')
    axb.plot(dfVH.index, dfVH['mean'], linestyle=' ', marker='s',
             markersize=10, color='DarkBlue', fillstyle='none', label='VH')
    axb.plot(dfVV.index, dfVV['mean'], linestyle=' ', marker='o',
             markersize=10, color='Red', fillstyle='none', label='VV')

    axb.set_xlim(start_date, end_date + timedelta(1))
    axb.set_ylim(0, 1)

    axb.legend(frameon=False)  # loc=2)

    return plt.show()
