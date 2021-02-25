#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (HBox, VBox, Dropdown, Button, Output, Checkbox)

from cbm.utils import config, data_options


def time_series(path):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import timedelta
    import pandas as pd
    import json
    import glob

    confvalues = config.read()
    inst = confvalues['set']['institution']
    file_info = f"{path}info.json"

    with open(file_info, 'r') as f:
        info_data = json.loads(f.read())
    pid = info_data['ogc_fid'][0]
    crop_name = info_data['cropname'][0]
    area = info_data['area'][0]

    def plot_ts_s2(cloud):
        file_ts = f"{path}time_series_s2.csv"
        df = pd.read_csv(file_ts, index_col=0)

        df['date'] = pd.to_datetime(df['date_part'], unit='s')
        start_date = df.iloc[0]['date'].date()
        end_date = df.iloc[-1]['date'].date()
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

        dfB4 = df[df.band == 'B4'].copy()
        dfB8 = df[df.band == 'B8'].copy()
        datesFmt = mdates.DateFormatter('%-d %b %Y')
        if cloud is False:
            # Plot NDVI
            fig = plt.figure(figsize=(16.0, 10.0))
            axb = fig.add_subplot(1, 1, 1)

            axb.set_title(
                f"Parcel {pid} (crop: {crop_name}, area: {area:.2f} ha)")
            axb.set_xlabel("Date")
            axb.xaxis.set_major_formatter(datesFmt)

            axb.set_ylabel(r'DN')
            axb.plot(dfB4.index, dfB4['mean'], linestyle=' ', marker='s',
                     markersize=10, color='DarkBlue',
                     fillstyle='none', label='B4')
            axb.plot(dfB8.index, dfB8['mean'], linestyle=' ', marker='o',
                     markersize=10, color='Red',
                     fillstyle='none', label='B8')

            axb.set_xlim(start_date, end_date + timedelta(1))
            axb.set_ylim(0, 10000)

            axb.legend(frameon=False)  # loc=2)

            return plt.show()

        else:
            # Plot Cloud free NDVI.
            dfSC = df[df.band == 'SC'].copy()
            dfNDVI = (dfB8['mean'] - dfB4['mean']) / \
                (dfB8['mean'] + dfB4['mean'])

            cloudfree = ((dfSC['mean'] >= 4) & (dfSC['mean'] < 6))

            fig = plt.figure(figsize=(16.0, 10.0))
            axb = fig.add_subplot(1, 1, 1)

            axb.set_title(
                f"{inst}\nParcel {pid} (crop: {crop_name}, area: {area:.2f} sqm)")

            axb.set_xlabel("Date")
            axb.xaxis.set_major_formatter(datesFmt)

            axb.set_ylabel(r'NDVI')
            axb.plot(dfNDVI.index, dfNDVI, linestyle=' ', marker='s',
                     markersize=10, color='DarkBlue',
                     fillstyle='none', label='NDVI')
            axb.plot(dfNDVI[cloudfree].index, dfNDVI[cloudfree],
                     linestyle=' ', marker='P',
                     markersize=10, color='Red',
                     fillstyle='none', label='Cloud free NDVI')

            axb.set_xlim(start_date, end_date + timedelta(1))
            axb.set_ylim(0, 1.0)

            axb.legend(frameon=False)  # loc=2)

            return plt.show()

    def plot_ts_bs():
        import numpy as np
        file_ts = f"{path}time_series_bs.csv"
        df = pd.read_csv(file_ts, index_col=0)

        df['date'] = pd.to_datetime(df['date_part'], unit='s')
        start_date = df.iloc[0]['date'].date()
        end_date = df.iloc[-1]['date'].date()
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
            f"{inst}\nParcel {pid} (crop: {crop_name}, area: {area:.2f} sqm)")
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

    def plot_ts_c6():
        file_ts = f"{path}time_series_c6.csv"
        df = pd.read_csv(file_ts, index_col=0)

        df['date'] = pd.to_datetime(df['date_part'], unit='s')
        start_date = df.iloc[0]['date'].date()
        end_date = df.iloc[-1]['date'].date()
        print(f"From '{start_date}' to '{end_date}'.")

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
            f"{inst}\nParcel {pid} (crop: {crop_name}, area: {area:.2f} sqm)")
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

    ts_cloud = Checkbox(
        value=True,
        description='Cloud free',
        disabled=False,
        indent=False
    )

    ts_files = glob.glob(f"{path}*time_series*.csv")
    ts_file_types = [b.split('_')[-1].split('.')[0] for b in ts_files]
    ts_types = [t for t in data_options.pts_tstype() if t[1] in ts_file_types]

    ts_type = Dropdown(
        options=ts_types,
        description='Select type:',
        disabled=False,
    )

    btn_ts = Button(
        value=False,
        description='Plot TS',
        disabled=False,
        button_style='info',
        tooltip='Refresh output',
        icon=''
    )

    ts_out = Output()

    @btn_ts.on_click
    def btn_ts_on_click(b):
        btn_ts.description = 'Refresh'
        btn_ts.icon = 'refresh'
        with ts_out:
            ts_out.clear_output()
            if ts_type.value == 's2':
                plot_ts_s2(ts_cloud.value)
            elif ts_type.value == 'bs':
                plot_ts_bs()
            elif ts_type.value == 'c6':
                plot_ts_c6()

    def on_ts_type_change(change):
        if ts_type.value == 's2':
            wbox_ts.children = [btn_ts, ts_type, ts_cloud]
        else:
            wbox_ts.children = [btn_ts, ts_type]

    ts_type.observe(on_ts_type_change, 'value')

    wbox_ts = HBox([btn_ts, ts_type, ts_cloud])

    wbox = VBox([wbox_ts, ts_out])

    return wbox
