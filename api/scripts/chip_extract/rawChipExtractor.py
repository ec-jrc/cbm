#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" rawChipExtractor.py -- A routine to extract a small subset from imagery
        in S3 object storage.
        Essential part of DIAS functionality for CAP Checks by Monitoring
    Author: Guido Lemoine, European Commission, Joint Research Centre
    License: see git repository
    Version 1.1 - 2022-09-17

    Revisions in 1.0:
    - Derived from chipS2Extractor2.py
    - Revised to return raw data
    - Revised by Konstantinos Anastasakis 2022-09
"""

import os
import glob
import time
import json
import logging

from scripts.chip_extract import creodiasCARDchips, chiptools


logging.basicConfig(filename='logs/main.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


def parallelExtract(lon, lat, start_date, end_date, unique_dir,
                    band, chipsize, plevel):
    start = time.time()
    logging.debug(start)
    # Make sure to skip duplicates that have lower version numbers
    chiplist = creodiasCARDchips.getS2Chips(
        float(lon), float(lat), start_date, end_date, int(chipsize), plevel)
    chiplist = creodiasCARDchips.rinseAndDryS2(chiplist)

    logging.debug("INITIAL CHIPS")
    logging.debug(chiplist)
    if os.path.exists(unique_dir):
        # Check which chips are already in the unique_dir
        # (simple form of caching)
        cachedList = glob.glob(f"{unique_dir}/*.tif")
        cachedList = [f.split('/')[-1].replace(f'{band}.tif', 'SAFE') for f in cachedList]
        logging.debug("CACHED")
        logging.debug(cachedList)
        for f in cachedList:
            if f in chiplist:
                chiplist.remove(f)
        logging.debug("FINAL CHIPS")
        logging.debug(chiplist)

        if len(chiplist) == 0:
            logging.debug("No new chips to be processed")
            print(f"Chips already cached in {unique_dir}")
            return 0
    else:
        logging.debug(f"Creating {unique_dir} on host")
        os.makedirs(unique_dir)
    logging.debug(f"Processing {len(chiplist)} chips")
    if len(chiplist) > 24:
        logging.debug("Too many chips requested")
        print("Request results in too many chips, please revise selection")
        return -1

    chiptools.runjobs(chiplist, lon, lat, unique_dir, 'rawChipRipper.py', f'{band} {chipsize} {plevel}')
    logging.debug(f"Total time required for {len(chiplist)} images: {time.time() - start} seconds")
    logging.debug(f"Generated {len(chiplist)} chips")
    print(f"Total time required for {len(chiplist)} images: {time.time() - start} seconds")
    chiptools.chipCollect(unique_dir)  # Collect the generate chips
    return len(chiplist)


def buildJSON(unique_dir, start_date, end_date):
    flist = glob.glob(f"{unique_dir}/*.tif")

    dict = {}

    for f in flist:
        dict[f.split('_')[-5]] = f

    keys = sorted(dict.keys())
    logging.debug("Before calendar check: ")
    logging.debug(keys)
    keys = chiptools.calendarCheck(keys, start_date, end_date)
    logging.debug("After calendar check: ")
    logging.debug(keys)

    dates = []
    chips = []

    for i in range(len(keys)):
        dates.append(keys[i])
        chips.append(dict[keys[i]].replace('static', '/static'))

    logging.debug(chips)
    logging.debug(dates)
    with open(f"{unique_dir}/chipslist.json", "w") as out:
        out.write(json.dumps({'dates': dates, 'chips': chips}))

    return True
