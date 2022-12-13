#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" rawChipBatchExtract.py -- A routine to extract a small subset from imagery
        in S3 object storage.
        Essential part of DIAS functionality for CAP Checks by Monitoring
    Author: Guido Lemoine, European Commission, Joint Research Centre
    License: see git repository
    Version 1.0 - 2020-03-22

    Revisions in 1.0:
    - Derived from rawChipExtractor.py
    - Revised to return raw data for known tiles
    - Revised by Konstantinos Anastasakis 2022-12

"""

import os
import glob
import time
import sys
import json
import logging

from scripts.chip_extract import chiptools

logging.basicConfig(
    filename=os.path.basename(sys.argv[0]).replace('.py', '.log'), filemode='w',
    format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def parallelExtract(unique_dir):
    start = time.time()
    logging.debug(start)
    # Read in params from json chipslist
    try:
        with open(f"{unique_dir}/params.json") as source:
            params = json.load(source)
    except Exception as err:
        print("[!Error]", err)
        logging.debug("error")

    logging.debug(params)
    lon = params.get('lon')
    lat = params.get('lat')
    chipsize = params.get('chipsize')
    tiles = params.get('tiles')
    bands = params.get('bands')
    chiplist = []
    for t in tiles:
        for b in bands:
            chiplist.append(f"{t}.{b}")

    # Make sure to skip duplicates that have lower version numbers
    # chiplist = creodiasCARDchips.getS2Chips(lon, lat, start_date, end_date, plevel)
    # chiplist = creodiasCARDchips.rinseAndDry(chiplist)
    logging.debug("INITIAL CHIPS")
    logging.debug(chiplist)
    if os.path.exists(unique_dir):
        # Check which chips are already in the unique_dir
        # (simple form of caching)
        cachedList = glob.glob(f"{unique_dir}/*.tif")

        cachedList = [f.split('/')[-1].replace('.tif', '') for f in cachedList]
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
                      'rawChipRipper2.py', chipsize)

    logging.debug(
        f"Total time required for {len(chiplist)} images: {time.time() - start} seconds")
    logging.debug(f"Generated {len(chiplist)} chips")
    chiptools.chipCollect(unique_dir)  # Collect the generate chips
    return len(chiplist)


def buildJSON(unique_dir):
    flist = glob.glob(f"{unique_dir}/*.tif")

    dict = {}

    for f in flist:
        dkey = f.split('_')[-5]
        bkey = f.split('.')[-2]
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
