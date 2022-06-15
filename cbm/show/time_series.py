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
from random import uniform
from itertools import groupby
from os.path import join, normpath, isfile
from datetime import timedelta

from cbm.utils import config
from cbm.get import parcel_info, time_series


def all_equal(iterable):
    "Returns True if all the elements are equal to each other"
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def ndvi(aoi, year, pids, ptype=None, scl='3_8_9_10_11', std=True,
         max_line_plots=10, errorbar=True, view=True, debug=False):

    if type(pids) is not list:
        pids = [pids]
    if max_line_plots > 20:
        max_line_plots = 20
        print("Can not plot more then 20 lines.")
    if len(pids) > 50:
        del pids[50:]
        print("Currently supporting max 50 shading plots.",
              "Will plot first 50 parcels")

    crop_names = []
    for pid in pids:
        path = normpath(join(config.get_value(['paths', 'temp']),
                             aoi, str(year), str(pid)))
        file_info = normpath(join(path, 'info.json'))
        if not isfile(file_info):
            if not parcel_info.by_pid(aoi, year, pid, ptype, True, False, debug):
                return "[Err]: No parcel found, please check the parameters"
        with open(file_info, 'r') as f:
            info_data = json.loads(f.read())
        crop_names.append(info_data['cropname'][0])
    parcel_peers = all_equal(crop_names)

    plt.rcParams['figure.facecolor'] = 'white'
    fig = plt.figure(figsize=(16.0, 10.0))
    axn = fig.add_subplot(1, 1, 1)

    pcount = 1

    for pid in pids:
        path = normpath(join(config.get_value(['paths', 'temp']),
                             aoi, str(year), str(pid)))
        file_info = normpath(join(path, 'info.json'))
        with open(file_info, 'r') as f:
            info_data = json.loads(f.read())

        crop_name = info_data['cropname'][0]
        area = info_data['area'][0]

        if len(pids) == 1:
            plot_title = f"NDVI profile, parcel: '{pid}', crop type: {crop_names[0]}, year: {year}, area: {area:.1f}sqm."
            cloudfreelabel = "Cloud free"
        elif parcel_peers:
            plot_title = f"NDVI profiles for crop type: {crop_names[0]} of the year: {year}."
            cloudfreelabel = f"Parcel: {pid}"
        else:
            plot_title = f"NDVI profiles, year: {year}"
            cloudfreelabel = f"Parcel: {pid}, {crop_name}"

        file_ts = normpath(join(path, 'time_series_s2.csv'))
        if not isfile(file_ts):
            time_series.by_pid(aoi, str(year), str(pid),
                               's2', ptype, '', debug)
        df = pd.read_csv(file_ts, index_col=0)

        df['date'] = pd.to_datetime(df['date_part'], unit='s')
        start_date = df.iloc[0]['date'].date()
        end_date = df.iloc[-1]['date'].date()
        if debug:
            print('Time series file:', file_ts)
            print(f"From '{start_date}' to '{end_date}'.")

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

        axn.set_xlabel("Date")
        axn.xaxis.set_major_formatter(datesFmt)

        if len(pids) == 1:
            axn.set_ylabel(r'NDVI')
            axn.plot(dfNDVI.index, dfNDVI, linestyle=' ', marker='s',
                     markersize=10, color='lightgray',
                     fillstyle='none', label='All observations')

        if 'hist' in df.columns:
            df['cf'] = pd.Series(dtype='str')
            scls = scl.split('_')
            for index, row in df.iterrows():
                if any(x in scls for x in [*json.loads(row['hist'].replace("\'", "\""))]):
                    df.at[index, 'cf'] = 'False'
                else:
                    df.at[index, 'cf'] = 'True'
            cloudfree = (df['cf'] == 'True')
            cloudfree = cloudfree[~cloudfree.index.duplicated()]
        else:
            dfSC = df[df.band == 'SC'].copy()
            cloudfree = ((dfSC['mean'] >= 4) & (dfSC['mean'] < 6))
        if std or errorbar:
            dfstd = ((dfB8['p75'] - dfB4['p25']) / 50000)
            cloufreestd = dfstd[dfstd.index.isin(dfNDVI[cloudfree].index)]
        try:
            if pcount <= max_line_plots:
                axn.plot(dfNDVI[cloudfree].index, dfNDVI[cloudfree],
                         linestyle='--', marker='P', markersize=10,
                         fillstyle='none', label=cloudfreelabel)
                if errorbar:
                    axn.errorbar(dfNDVI[cloudfree].index, dfNDVI[cloudfree],
                                 cloufreestd, fmt=' ', color='Gray',
                                 linewidth=2, capsize=4, alpha=0.4)
            if std:
                if max_line_plots == 1 and pcount == 1:
                    peers_lable = 'Parcel peers'
                else:
                    peers_lable = None
                axn.fill_between(dfNDVI[cloudfree].index,
                                 dfNDVI[cloudfree] - cloufreestd,
                                 dfNDVI[cloudfree] + cloufreestd,
                                 color='b', alpha=(2 * ((len(pids) + 2) / (3 * len(pids)))) / 10, label=peers_lable)
        except Exception as err:
            message = f"Could not mark cloud free images: {err}"

        axn.set_xlim(start_date, end_date + timedelta(1))
        axn.set_ylim(0, 1.0)

        axn.legend(frameon=False)
        pcount += 1
    if 'message' in locals():
        print(message)
    axn.set_title(plot_title)

    if not view:
        plt.close(fig)
        return fig
    return plt.show(fig)


def s2(aoi, year, pid, ptype=None, bands=['B02', 'B03', 'B04', 'B08'],
       scl='3_8_9_10_11', view=True, debug=False):
    if type(bands) is str:
        bands = [bands]
    path = normpath(join(config.get_value(['paths', 'temp']),
                         aoi, str(year), str(pid)))

    file_info = normpath(join(path, 'info.json'))
    if not isfile(file_info):
        if not parcel_info.by_pid(aoi, year, pid, ptype, True, False, debug):
            return "[Err]: No parcel found, please check the parameters"
    with open(file_info, 'r') as f:
        parcel = json.loads(f.read())

    crop_name = parcel['cropname'][0]
    area = parcel['area'][0]

    file_ts = normpath(join(path, 'time_series_s2.csv'))
    if not isfile(file_ts):
        time_series.by_pid(aoi, str(year), str(pid), 's2', ptype, '', debug)
    df = pd.read_csv(file_ts, index_col=0)

    df['date'] = pd.to_datetime(df['date_part'], unit='s')
    start_date = df.iloc[0]['date'].date()
    end_date = df.iloc[-1]['date'].date()
    if debug:
        print('Time series file:', file_ts)
        print(f"From '{start_date}' to '{end_date}'.")

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

    if 'hist' in df.columns:
        df['cf'] = pd.Series(dtype='str')
        scls = scl.split('_')
        for index, row in df.iterrows():
            if any(x in scls for x in [*json.loads(row['hist'].replace("\'",
                                                                       "\""))]):
                df.at[index, 'cf'] = 'False'
            else:
                df.at[index, 'cf'] = 'True'
        cloudfree = (df['cf'] == 'True')
        cloudfree = cloudfree[~cloudfree.index.duplicated()]
    else:
        dfSC = df[df.band == 'SC'].copy()
        cloudfree = ((dfSC['mean'] >= 4) & (dfSC['mean'] < 6))

    datesFmt = mdates.DateFormatter('%-d %b %Y')

    # Plot Band
    plt.rcParams['figure.facecolor'] = 'white'
    fig = plt.figure(figsize=(16.0, 10.0))
    axb = fig.add_subplot(1, 1, 1)

    axb.set_title(f"Parcel {pid} (crop: {crop_name}, area: {area:.1f} sqm)")
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
              "B08": "darkviolet",
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
              "B8": "darkviolet",
              "B9": "Grey"
              }

    seriesB = {}
    for b in bands:
        axb.plot(dfb[b].index, dfb[b]['mean'], linestyle=' ', marker='o',
                 markersize=8, color=colors[b],
                 fillstyle='none', label=b, alpha=0.5)

        seriesB[b] = pd.Series(dfb[b]['mean'], index=dfb[b].index)
        axb.plot(seriesB[b][cloudfree].index, seriesB[b][cloudfree],
                 linestyle='--', marker='x',
                 markersize=8, color=colors[b],
                 fillstyle='none', label=f'{b} Cloud free')

    axb.set_xlim(start_date, end_date + timedelta(1))
    axb.set_ylim(0, 10000)
    axb.legend(frameon=False)

    if not view:
        plt.close(fig)
        return fig
    return plt.show(fig)


def s1(aoi, year, pids, tstype='bs', ptype=None, std=True,
       max_line_plots=10, errorbar=True, view=True, debug=False):
    if type(pids) is not list:
        pids = [pids]
    if max_line_plots > 20:
        max_line_plots = 20
        print("Can not plot more then 20 lines.")
    if len(pids) > 50:
        del pids[50:]
        print("Currently supporting max 50 shading plots.",
              "Will plot first 50 parcels")

    crop_names = []
    for pid in pids:
        path = normpath(join(config.get_value(['paths', 'temp']),
                             aoi, str(year), str(pid)))
        file_info = normpath(join(path, 'info.json'))
        if not isfile(file_info):
            if not parcel_info.by_pid(aoi, year, pid, ptype, True, False, debug):
                return "[Err]: No parcel found, please check the parameters"
        with open(file_info, 'r') as f:
            info_data = json.loads(f.read())
        crop_names.append(info_data['cropname'][0])
    parcel_peers = all_equal(crop_names)

    if tstype == 'bs':
        profile_type = 'Backscattering coefficient'
    else:
        profile_type = '6 day coherence'

    plt.rcParams['figure.facecolor'] = 'white'
    fig = plt.figure(figsize=(16.0, 10.0))
    ax = fig.add_subplot(1, 1, 1)

    pcount = 1
    for pid in pids:
        path = normpath(join(config.get_value(['paths', 'temp']),
                             aoi, str(year), str(pid)))
        file_info = normpath(join(path, 'info.json'))
        with open(file_info, 'r') as f:
            info_data = json.loads(f.read())

        crop_name = info_data['cropname'][0]
        area = info_data['area'][0]

        if len(pids) == 1:
            plot_title = f"S1 {profile_type}, parcel: '{pid}', crop type: {crop_names[0]}, year: {year}, area: {area:.1f}sqm."
            plabel = '{} Moving average'
        elif parcel_peers:
            plot_title = f"Moving average of S1 {profile_type}, crop type: {crop_names[0]}, year: {year}."
            plabel = f'{pid} {{}}'
        else:
            plot_title = f"NDVI profiles, year: {year}"
            plabel = f"Parcel: {pid}, {{}} {crop_name}"

        file_ts = normpath(join(path, f'time_series_{tstype}.csv'))
        if not isfile(file_ts):
            time_series.by_pid(aoi, year, pid, tstype, ptype, '', debug)
        df = pd.read_csv(file_ts, index_col=0)

        df['date'] = pd.to_datetime(df['date_part'], unit='s')
        start_date = df.iloc[0]['date'].date()
        end_date = df.iloc[-1]['date'].date()
        if debug and pcount == 1:
            print(f"From '{start_date}' to '{end_date}'.")

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

        def moving_average(a, n=3):
            ret = np.cumsum(a, dtype=float)
            ret[n:] = ret[n:] - ret[:-n]
            return ret[n - 1:] / n

        # Plot Backscattering coefficient
        df = df[df['mean'] >= 0]  # to remove negative values

        dfVV = df[df.band == f'VV{tstype[0]}'].copy()
        dfVH = df[df.band == f'VH{tstype[0]}'].copy()

        if tstype == 'bs':
            dfVH['mean'] = dfVH['mean'].map(lambda s: 10.0 * np.log10(s))
            dfVH['p25'] = dfVH['p25'].map(lambda s: 10.0 * np.log10(s))
            dfVH['p75'] = dfVH['p75'].map(lambda s: 10.0 * np.log10(s))
            dfVV['mean'] = dfVV['mean'].map(lambda s: 10.0 * np.log10(s))
            dfVV['p25'] = dfVV['p25'].map(lambda s: 10.0 * np.log10(s))
            dfVV['p75'] = dfVV['p75'].map(lambda s: 10.0 * np.log10(s))
            ax.set_ylim(-25, -1)
            ylabel = 'Sentinel-1 Backscattering coefficient, $\gamma\degree$ (dB)'
        else:
            ax.set_ylim(0, 1)
            ylabel = 'Sentinel-1 6 day coherence'

        ax.set_xlabel("Date")
        ax.xaxis.set_major_formatter(datesFmt)
        ax.set_ylabel(ylabel)
        ax.set_xlim(start_date + timedelta(5), end_date - timedelta(5))

        if len(pids) == 1:
            ax.plot(dfVH.index, dfVH['mean'], linestyle=' ', marker='.',
                    markersize=5, color='DarkBlue', label='VH mean', alpha=0.5)
            ax.plot(dfVV.index, dfVV['mean'], linestyle=' ', marker='.',
                    markersize=5, color='Red', label='VV mean', alpha=0.5)

        if pcount <= max_line_plots:
            if pcount == 1:
                colorVH = 'DarkBlue'
                colorVV = 'Red'
            else:
                colorVH = (uniform(0.0, 0.7), uniform(
                    0.0, 0.9), uniform(0.7, 1.0))
                colorVV = (uniform(0.7, 1.0), uniform(
                    0.0, 0.9), uniform(0.0, 0.7))
            dfVHmean = moving_average(np.concatenate(
                ([-10], dfVH['mean'].to_numpy(), [-10])))
            dfVVmean = moving_average(np.concatenate(
                ([-10], dfVV['mean'].to_numpy(), [-10])))
            ax.plot(dfVV.index, dfVHmean, linestyle='-',
                    color=colorVH, label=plabel.format('VH'))
            ax.plot(dfVV.index, dfVVmean, linestyle='-',
                    color=colorVV, label=plabel.format('VV'))

        if std:
            dfVH25 = moving_average(np.concatenate(
                ([-10], dfVH['p25'].to_numpy(), [-10])))
            dfVH75 = moving_average(np.concatenate(
                ([-10], dfVH['p75'].to_numpy(), [-10])))
            dfVV25 = moving_average(np.concatenate(
                ([-10], dfVV['p25'].to_numpy(), [-10])))
            dfVV75 = moving_average(np.concatenate(
                ([-10], dfVV['p75'].to_numpy(), [-10])))
            ax.fill_between(dfVV.index, dfVV25, dfVV75, color='r',
                            alpha=(2 * ((len(pids) + 2) / (3 * len(pids)))) / 10)
            ax.fill_between(dfVV.index, dfVH25, dfVH75, color='b',
                            alpha=(2 * ((len(pids) + 2) / (3 * len(pids)))) / 10)

        pcount += 1
        ax.legend(frameon=False)
    ax.set_title(plot_title)
    ax.legend(frameon=False)

    if not view:
        plt.close(fig)
        return fig
    return plt.show(fig)


def weather(aoi, year, pid, tstype='tp', ptype=None, view=True, debug=False):
    path = normpath(join(config.get_value(['paths', 'temp']),
                         aoi, str(year), str(pid)))

    file_info = normpath(join(path, 'info.json'))
    if not isfile(file_info):
        if not parcel_info.by_pid(aoi, year, pid, ptype, True, False, debug):
            return "[Err]: No parcel found, please check the parameters"
    with open(file_info, 'r') as f:
        parcel = json.loads(f.read())

    crop_name = parcel['cropname'][0]
    area = parcel['area'][0]

    file_ts = normpath(join(path, 'time_series_weather.csv'))
    if not isfile(file_ts):
        time_series.weather(aoi, year, pid, ptype, debug)
    df = pd.read_csv(file_ts, index_col=0)

    df['date'] = pd.to_datetime(df['meteo_date'])
    start_date = df.iloc[0]['date'].date()
    end_date = df.iloc[-1]['date'].date()
    if debug:
        print('Time series file:', file_ts)
        print(f"From '{start_date}' to '{end_date}'.")

    pd.set_option('max_colwidth', 10)
    pd.set_option('display.max_columns', 20)

    # Plot settings are confirm IJRS graphics instructions
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 14

    df.set_index(['date'], inplace=True)
    datesFmt = mdates.DateFormatter('%-d %b %Y')

    # Plot temperature and precipitation
    plt.rcParams['figure.facecolor'] = 'white'
    fig = plt.figure(figsize=(16.0, 10.0))
    axw = fig.add_subplot(1, 1, 1)
    axw.set_title(f"Parcel {pid} (crop: {crop_name}, area: {area:.1f} sqm)")
    axw.set_xlabel("Date")
    axw.xaxis.set_major_formatter(datesFmt)
    if 't' in tstype[:3]:
        axw.set_ylabel(r'Daily mean temperature', color='r')
        axw.plot(df.index, df['tmean'], linestyle=' ', marker='o',
                 markersize=3, color='red',
                 fillstyle='none', label='Temperature', alpha=0.8)
        axw.fill_between(df.index, df['tmin'], df['tmax'],
                         color='b', alpha=0.08)
        axw.legend(loc='upper left')

    if 'p' in tstype[:3]:
        axp = axw.twinx()
        axp.set_ylabel('Daily precipitation', color='b')
        axp.plot(df.index, df['prec'], linestyle=' ', marker='o',
                 markersize=3, color='blue',
                 fillstyle='none', label='Precipitation', alpha=0.8)
        axp.legend(loc='upper right')

    axw.set_xlim(start_date - timedelta(1), end_date + timedelta(1))

    if not view:
        plt.close(fig)
        return fig
    return plt.show(fig)
