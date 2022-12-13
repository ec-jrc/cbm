#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" chipS2Extract.py -- A routine to extract a small subset from imagery in
        S3 object storage.
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
    - Revised by Konstantinos Anastasakis 2022-10
"""

import os
import glob
import time
import sys
import logging
from scripts.chip_extract import creodiasCARDchips, chiptools


logging.basicConfig(
    filename=os.path.basename(sys.argv[0]).replace('.py', '.log'), filemode='w',
    format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def parallelExtract(lon, lat, start_date, end_date, unique_dir,
                    lut, bands, plevel):
    start = time.time()
    logging.debug(start)
    # Read in chip list, make sure to skip duplicates that have least complete
    # overlap or lower version numbers
    chiplist = creodiasCARDchips.getS2Chips(
        float(lon), float(lat), start_date, end_date, 1280, plevel)
    chiplist = creodiasCARDchips.rinseAndDryS2(chiplist)
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
            print(f"Chips already cached in {unique_dir}")
            logging.debug("No new chips to be processed")
            return 0
    else:
        logging.debug(f"Creating {unique_dir} on host")
        os.makedirs(unique_dir)
    logging.debug(f"Processing {len(chiplist)} chips")
    if len(chiplist) > 24:
        print("Request results in too many chips, please revise selection")
        logging.debug("Too many chips requested")
        return -1
    chiptools.runjobs(chiplist, lon, lat, unique_dir,
                      'chipRipper2.py', f'{lut} {bands} {plevel}')

    logging.debug(f"Generated {len(chiplist)} chips")
    chiptools.chipCollect(unique_dir, 'png')  # Collect the generate chips
    return len(chiplist)


def buildHTML(unique_dir, start_date, end_date, columns=8):
    flist = glob.glob(f"{unique_dir}/*.png")

    dict = {}

    for f in flist:
        dict[f.split('_')[-5]] = f

    keys = sorted(dict.keys())
    logging.debug("Before calendar check: ")
    logging.debug(keys)
    keys = chiptools.calendarCheck(keys, start_date, end_date)
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

        html.append(f"""<td><label><img id = "{keys[i]}" src="{dict[keys[i]].replace('static', '/static')}"/><br/>{keys[i]}</label></td>""")
        if i % columns == columns - 1:
            html.append("</tr><br/>")

    html.append("</tr></table></body></html>")
    with open(f"{unique_dir}/chipsview.html", "w") as out:
        out.write("".join(html))

    return True
