#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import json
import glob
import random
import itertools
from scripts import users, db, db_queries


def generator(user=None, selected_aoi=None, selected_year=None):
    user_aois = users.get_list(only_names=False, aois=True)[user]
    with open('config/datasets.json', 'r') as f:
        all_datasets = json.load(f)
    with open('config/main.json') as f:
        configs = json.load(f)

    dslist = list(dict.fromkeys([x for x in dict.keys(all_datasets)]))
    all_aois = list(dict.fromkeys([x.split('_')[0]
                                   for x in dict.keys(all_datasets)]))
    server = configs["server"]
    url = configs["server"]["host"]

    helpers = {
        "documentation": "https://jrc-cbm.readthedocs.io",
        "git_repository": "https://github.com/ec-jrc/cbm",
        "information_page": f"{url}/query/info",
        "downloadable material": f"{url}/files",
        "swagger": f"{url}/apidocs"
    }

    info_page = {"server": server, "helpers": helpers, "aois": {}}

    def aoi_data(aoi, years, year):
        schema = all_datasets[
            f'{aoi}_{year}']['tables']['parcels'].split('.')[0]
        dbtables = db.tables(all_datasets[f'{aoi}_{year}']['db'], schema)

        def validPt(dbt):
            p = dbt.split('_')[-1]
            if p.isnumeric() or p == 'rast':
                return False
            elif dbt.startswith(aoi) or dbt.startswith("parcels"):
                if len(p) == 1 or len(p) == 3:
                    return True
            else:
                return False

        ptypes = list(dict.fromkeys(
            [dbt.split('_')[-1] for dbt in dbtables if validPt(dbt)]))

        if len(ptypes) > 0:
            pt = random.choice(ptypes)
            ptype = f"_{pt}"
            ptype_param = f"&ptype={pt}"
        else:
            ptype, ptype_param = '', ''

        # Get available tms
        tfiles = [f.split('/')[1].split('.')[0] for f in glob.glob('tms/*')]
        available_tms = ['google', 'bing', 'osm', 'esri']
        for f in tfiles:
            if "".join(itertools.takewhile(str.isalpha, f)) == aoi:
                available_tms.append(f)

        # Set requests parameters
        dataset = all_datasets[f"{aoi}_{year}"]
        pidcolumn = all_datasets[f"{aoi}_{year}"]["pcolumns"]["parcel_id"]
        pids_df = db_queries.pids(dataset, 100, ptype, False)
        pids = random.sample(pids_df['pids'].values.tolist(), 5)
        pid = random.choice(pids)
        # tms = random.choice(available_tms)

        request_examples = {
            "parcelByID": f"{url}/query/parcelByID?aoi={aoi}&year={year}&pid={pid}{ptype_param}&withGeometry=True",
            "parcelTimeSeries_s2": f"{url}/query/parcelTimeSeries?aoi={aoi}&year={year}&pid={pid}{ptype_param}&tstype=s2&scl=True",
            "parcelTimeSeries_bs": f"{url}/query/parcelTimeSeries?aoi={aoi}&year={year}&pid={pid}{ptype_param}&tstype=bs",
            "parcelTimeSeries_c6": f"{url}/query/parcelTimeSeries?aoi={aoi}&year={year}&pid={pid}{ptype_param}&tstype=c6",
            "backgroundByParcelID": f"{url}/query/backgroundByParcelID?aoi={aoi}&year={year}&pid={pid}{ptype_param}&chipsize=256&extend=512&iformat=png",
            "weatherTimeSeries": f"{url}/query/weatherTimeSeries?aoi={aoi}&year={year}&pid={pid}{ptype_param}",
            "parcelPeers": f"{url}/query/parcelPeers?aoi={aoi}&year={year}&pid={pid}{ptype_param}"
        }

        def ts_data():
            ts_data = []
            ts_data_types = ["s2", "bs", "c6"]
            for tst in ts_data_types:
                if all_datasets[f'{aoi}_{year}']['tables'][tst] != '':
                    ts_data.append(tst)
                else:
                    del request_examples[f"parcelTimeSeries_{tst}"]
            return ts_data

        info_page["aois"][aoi] = {
            "years": years,
            "datasets": ptypes,
            "time_series": ts_data(),
            "tms": available_tms,
            "id_table_column": pidcolumn,
            f"id_examples_{year}{ptype}": pids,
            "request_examples": request_examples
        }

    def get_ds(for_aoi):
        try:
            years = [y.split('_')[1]
                     for y in dslist if y.split('_')[0] == for_aoi]
            year = random.choice(years)
            aoi_data(for_aoi, years, year)
        except Exception as err:
            print(for_aoi, err)

    if 'admin' in user_aois:
        if selected_aoi:
            if selected_aoi.lower() in all_aois:
                get_ds(selected_aoi.lower())
        else:
            for aoi in all_aois:
                get_ds(aoi)

    else:
        if selected_aoi.lower():
            if selected_aoi.lower() in user_aois:
                if selected_aoi.lower() in all_aois:
                    get_ds(selected_aoi.lower())
        else:
            for aoi in user_aois:
                if aoi in all_aois:
                    get_ds(aoi)

    return info_page
