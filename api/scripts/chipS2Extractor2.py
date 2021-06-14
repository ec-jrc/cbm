#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" chipS2Extract.py -- A routine to extract a small subset from imagery in S3 object storage.
                        Essential part of DIAS functionality for CAP Checks by Monitoring
    Author: Guido Lemoine, European Commission, Joint Research Centre
    License: see git repository
    Version 1.3 - 2020-03-17

    Revisions in 1.1:
    - Implementation of parallel multi-band retrieval
    - Using python3 formatted strings
    Revisions in 1.2:
    - Refactored, including VM transfer and HTML preparation
    Revisions in 1.3:
    - lut and bands parameter handling
    Revisions in 1.4 by Konstantinos Anastasakis:
    - Remove parallel processing

"""

import os
import glob
import time
import sys
import logging
from datetime import datetime
# from concurrent.futures import ProcessPoolExecutor, as_completed

from scripts.dias import creodiasCARDchips as ccc
from scripts import chipRipper2

logging.basicConfig(filename=os.path.basename(sys.argv[0]).replace(
    '.py', '.log'), filemode='w',
    format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def parallelExtract(lon, lat, start_date, end_date,
                    unique_dir, lut, bands, plevel):
    start = time.time()
    logging.debug(start)
    # Read in chip list, make sure to skip duplicates that have
    # least complete overlap or lower version numbers
    chiplist = ccc.getS2Chips(float(lon), float(
        lat), start_date, end_date, 1280, plevel)
    logging.debug(chiplist)
    chiplist = ccc.rinseAndDryS2(chiplist)
    logging.debug("INITIAL CHIPS")
    logging.debug(chiplist)
    logging.debug(unique_dir)
    if os.path.exists(unique_dir):
        # Check which chips are already in the unique_dir
        # (simple form of caching)
        cachedList = glob.glob(f"{unique_dir}/*.png")

        cachedList = [f.split('/')[-1].replace('.png', '') for f in cachedList]
        logging.debug("CACHED")
        logging.debug(cachedList)
        for f in cachedList:
            if f in chiplist:
                chiplist.remove(f)
        logging.debug("FINAL CHIPS")
        logging.debug(chiplist)

        if len(chiplist) == 0:
            logging.debug("No new chips to be processed")
            return 0
    else:
        logging.debug(f"Creating {unique_dir} on host")
        os.makedirs(unique_dir)

    logging.debug(f"Processing {len(chiplist)} chips")

    if len(chiplist) > 24:
        logging.debug("Too many chips requested")
        return -1

    # chip_set = {}
    for i in range(len(chiplist)):
        reference = chiplist[i]
        chipRipper2.main(lon, lat, reference, unique_dir, lut, bands, plevel)

    logging.debug(
        f"Total time required for {len(chiplist)} images with {3} bands: {time.time() - start} seconds")
    logging.debug(f"Generated {len(chiplist)} chips")
    return len(chiplist)


def calendarCheck(klist, start_date, end_date):
    # Check whether keys are within the time window
    s_date = datetime.strptime(start_date, '%Y-%m-%d')
    e_date = datetime.strptime(end_date, '%Y-%m-%d')
    dlist = [datetime.strptime(k, '%Y%m%dT%H%M%S') for k in klist]
    slist = [d.strftime('%Y%m%dT%H%M%S') for d in dlist if s_date < d < e_date]
    return slist


def buildHTML(unique_dir, start_date, end_date, columns=8):
    flist = glob.glob(f"{unique_dir}/*.png")

    dict = {}

    for f in flist:
        dict[f.split('_')[-5]] = f

    keys = sorted(dict.keys())
    logging.debug("Before calendar check: ")
    logging.debug(keys)
    keys = calendarCheck(keys, start_date, end_date)
    logging.debug("After calendar check: ")
    logging.debug(keys)

    html = []
    html.append("<!DOCTYPE html><html><head>")
    html.append("<style>table { border-spacing: 10px; }")
    html.append("</style></head><body>")
    html.append("<table style=\"width:100%\">")

    for i in range(len(keys)):
        if i % columns == 0:
            html.append("<tr>")

        html.append(
            f"""<td><label><img id = "{keys[i]}" src="{dict[keys[i]].replace('dump', '/dump')}"/><br/>{keys[i]}</label></td>""")
        if i % columns == columns - 1:
            html.append("</tr><br/>")

    html.append("</tr></table></body></html>")
    with open(f"{unique_dir}/dump.html", "w") as out:
        out.write("".join(html))

    return True
