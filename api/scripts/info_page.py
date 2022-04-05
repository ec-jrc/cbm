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


def generator(user=None):
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

    def aois(aoi, years, year):
        dbtables = db.tables(all_datasets[f'{aoi}_{year}']['db'], aoi)

        ptypes = list(dict.fromkeys(
            [x.split('_')[-1] for x in dbtables if len(x.split('_')[-1]) == 1]))

        if len(ptypes) > 0:
            pt = random.choice(ptypes)
            ptype = f"_{pt}"
            ptype_param = f"&ptype={pt}"
        else:
            ptype, ptype_param = '', ''

        tfiles = [f.split('/')[1].split('.')[0] for f in glob.glob('tms/*')]
        available_tms = ['google', 'bing', 'osm', 'ags']
        for f in tfiles:
            if "".join(itertools.takewhile(str.isalpha, f)) == aoi:
                available_tms.append(f)

        dataset = all_datasets[f"{aoi}_{year}"]
        pidcolumn = all_datasets[f"{aoi}_{year}"]["pcolumns"]["parcel_id"]
        pids_df = db_queries.pids(dataset, 100, ptype, False)
        pids = random.sample(pids_df['pids'].values.tolist(), 5)
        pid = random.choice(pids)
        # tms = random.choice(available_tms)

        data_request_examples = {
            "parcelByID": f"{url}/query/parcelByID?aoi={aoi}&year={year}&pid={pid}{ptype_param}&withGeometry=True",
            "parcelTimeSeries_s2": f"{url}/query/parcelTimeSeries?aoi={aoi}&year={year}&pid={pid}{ptype_param}&tstype=s2&scl=True",
            "parcelTimeSeries_bs": f"{url}/query/parcelTimeSeries?aoi={aoi}&year={year}&pid={pid}{ptype_param}&tstype=bs",
            "parcelTimeSeries_c6": f"{url}/query/parcelTimeSeries?aoi={aoi}&year={year}&pid={pid}{ptype_param}&tstype=c6",
            "backgroundByParcelID": f"{url}/query/backgroundByParcelID?aoi={aoi}&year={year}&pid={pid}{ptype_param}&chipsize=256&extend=512&iformat=png&withGeometry=True",
            "weatherTimeSeries": f"{url}/query/weatherTimeSeries?aoi={aoi}&year={year}&pid={pid}{ptype_param}",
            "parcelPeers": f"{url}/query/parcelPeers?aoi={aoi}&year={year}&pid={pid}{ptype_param}"
        }
        info_page["aois"][aoi] = {
            "dataset_types": ptypes,
            "years": years,
            "ts_data": ["s2", "bs", "c6"],
            "id_table_column": pidcolumn,
            f"id_examples_{year}{ptype}": pids,
            "available_tms": available_tms,
            "data_request_examples": data_request_examples
        }

    if 'admin' in user_aois:
        for aoi in all_aois:
            try:
                years = [y.split('_')[1]
                         for y in dslist if y.split('_')[0] == aoi]
                year = random.choice(years)
                aois(aoi, years, year)
            except Exception as err:
                print(aoi, err)
    else:
        for aoi in user_aois:
            if aoi in all_aois:
                try:
                    years = [y.split('_')[1]
                             for y in dslist if y.split('_')[0] == aoi]
                    year = random.choice(years)
                    aois(aoi, years, year)
                except Exception as err:
                    print(aoi, err)

    return info_page
