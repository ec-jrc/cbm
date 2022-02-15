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
    users_list = users.get_list(only_names=False, aois=True)
    with open('config/datasets.json', 'r') as f:
        datasets = json.load(f)
    with open('config/main.json') as f:
        configs = json.load(f)

    all_aois = list(dict.fromkeys([x.split('_')[0]
                                   for x in dict.keys(datasets)]))
    server = configs["server"]
    url = configs["server"]["host"]

    helpers = {
        "information_page": f"{url}/query/info",
        "downloadable material": f"{url}/files",
        "swagger": f"{url}/apidocs"
    }

    info_page = {"server": server, "helpers": helpers, "aois": {}}

    def aois(aoi):
        dbtables = db.tables('main', aoi)  # Needs fix to get the db
        tables = [x for x in dbtables if x.startswith('parcels_')]
        ptables = [x for x in tables if not x.endswith('rast')]
        years = list(dict.fromkeys([x.split('_')[1] for x in ptables]))
        year = random.choice(years)

        types = [x.split('_')[2]
                 for x in ptables if len(x.split('_')) == 3]
        ptypes = list(dict.fromkeys(types))

        if len(ptypes) > 0:
            pt = random.choice(ptypes)
            ptype = f"_{pt}"
            ptype_param = f"&ptype={pt}"
        else:
            ptype, ptype_param = '', ''

        tfiles = [f.split('/')[1].split('.')[0] for f in glob.glob('tms/*')]
        available_tms = ['google', 'bing', 'osm']
        for f in tfiles:
            if "".join(itertools.takewhile(str.isalpha, f)) == aoi:
                available_tms.append(f)

        dataset = datasets[f"{aoi}_{year}"]
        pidcolumn = datasets[f"{aoi}_{year}"]["pcolumns"]["parcel_id"]
        pids_df = db_queries.pids(dataset, 5, ptype, False)
        pids = pids_df['pids'].values.tolist()
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
            "id_examples": pids,
            "available_tms": available_tms,
            "data_request_examples": data_request_examples
        }

    if 'admin' in users_list[user]:
        for aoi in all_aois:
            try:
                aois(aoi)
            except Exception as err:
                print(aoi, err)
    else:
        for aoi in users_list[user]:
            if aoi in all_aois:
                try:
                    aois(aoi)
                except Exception as err:
                    print(aoi, err)

    return info_page
