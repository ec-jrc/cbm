#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" rawS1ChipBatchExtract.py -- A routine to extract a small subset from
        imagery in S3 object storage.
        Essential part of DIAS functionality for CAP Checks by Monitoring
    Author: Guido Lemoine, European Commission, Joint Research Centre
    License: see git repository
    Version 1.0 - 2020-04-14

    Revisions in 1.0:
    - Derived from rawChipBatchExtract.py
    - Revised to return raw data time series of S1
    - Change cache list check for both polarizations
    - Revised by Konstantinos Anastasakis 2022-12

"""

import os
import glob
import time
import sys
import json
import logging

from scripts.chip_extract import creodiasCARDchips, chiptools


logging.basicConfig(
    filename=os.path.basename(sys.argv[0]).replace('.py', '.log'), filemode='w',
    format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def parallelExtract(unique_dir):
    start = time.time()
    logging.debug(start)
    # Read in params from chipslist.json
    try:
        with open(f"{unique_dir}/params.json") as source:
            params = json.load(source)
    except Exception():
        logging.debug("Errr")

    logging.debug(params)
    lon = params.get('lon')
    lat = params.get('lat')
    chipsize = params.get('chipsize')
    dates = params.get('dates')
    plevel = params.get('plevel')

    chiplist = creodiasCARDchips.getS1Chips(float(lon), float(
        lat), dates[0], dates[1], int(chipsize), plevel)
    chiplist = creodiasCARDchips.rinseAndDryS1(chiplist)

    logging.debug("INITIAL CHIPS")
    logging.debug(chiplist)
    if os.path.exists(unique_dir):
        # Check which chips are already in the unique_dir
        # (simple form of caching)
        cachedList = glob.glob(f"{unique_dir}/*.tif")

        cachedList = [f.split('/')[-1].replace(
            '_VV.tif', '').replace('_VH.tif', '') for f in cachedList]
        logging.debug("CACHED")
        logging.debug(cachedList)
        for f in cachedList:
            if f in chiplist:
                chiplist.remove(f)
        logging.debug("FINAL CHIPS")
        logging.debug(chiplist)

        if len(chiplist) == 0:
            print(f"No new chips to be processed, {unique_dir}")
            logging.debug("No new chips to be processed")
            return 0
    else:
        logging.debug(f"Creating {unique_dir} on host")
        os.makedirs(unique_dir)

    logging.debug(f"Processing {len(chiplist)} chips")

    if len(chiplist) > 36:
        print("Request results in too many chips, please revise selection")
        logging.debug("Too many chips requested")
        return -1
    chiptools.runjobs(chiplist, lon, lat, unique_dir,
                      'rawS1ChipRipper.py', f'{chipsize} {plevel}')

    logging.debug(
        f"Total time required for {len(chiplist)} images: {time.time() - start} seconds")
    logging.debug(f"Generated {len(chiplist)} chips")
    chiptools.chipCollect(unique_dir)
    return len(chiplist)


def buildJSON(unique_dir):
    flist = glob.glob(f"{unique_dir}/*.tif")

    dict = {}

    for f in flist:
        if f.find('CARD_BS') != -1:
            dkey = f.split('_')[-8]
        elif f.find('CARD-COH6') != -1:
            dkey = f.split('_')[-7]

        bkey = f.replace('.tif', '').split('_')[-1]
        dict[f"{dkey}_{bkey}"] = f

    keys = sorted(dict.keys())
    logging.debug(keys)

    dates = []
    chips = []

    for i in range(len(keys)):
        dates.append(keys[i])
        chips.append(dict[keys[i]].replace('tmp', '/tmp'))

    logging.debug(chips)
    logging.debug(dates)
    with open(f"{unique_dir}/chipslist.json", "w") as out:
        out.write(json.dumps({'dates': dates, 'chips': chips}))

    return True
