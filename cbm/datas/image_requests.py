#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import logging
from scripts import backgroundExtract as bgext
from scripts import chipS2Extractor2 as ces2
from scripts import rawChipBatchExtract as rceb
from scripts import rawChipExtractor as rce
from scripts import rawS1ChipBatchExtract as rces1

aois_table = 'public.aois'
dias_cat_table = 'public.dias_catalogue'

logging.basicConfig(filename='logs/queryHandler.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)


# Parcel Images

def getBackgroundByLocation(lon, lat, chipsize, chipextend, tms,
                            unique_id, iformat):
    try:
        logging.debug(unique_id)
        logging.debug(f"{unique_id} {iformat}")
        bgext.getWindowedExtract(lon, lat, chipsize, chipextend,
                                 unique_id, tms, iformat)
        return True
    except Exception as err:
        print(err)


def getChipsByLocation(lon, lat, start_date, end_date, unique_id, lut='5_95',
                       bands='B08_B04_B03', plevel='LEVEL2A'):
    logging.debug(lut)
    logging.debug(bands)
    logging.debug(f"""{lon} {lat} {start_date} {end_date}
        {unique_id} {lut} {bands} {plevel}""")

    numchips = ces2.parallelExtract(
        lon, lat, start_date, end_date, unique_id, lut, bands, plevel)

    if numchips == -1:
        print(f"Request results in too many chips, please revise selection")
    elif numchips > 0:
        print(f"New chips ara in {unique_id}")
    else:
        print(f"Chips already cached in {unique_id}")

    print(ces2.buildHTML(unique_id, start_date, end_date))

    return True


def getRawChipByLocation(lon, lat, start_date, end_date, unique_id, band,
                         chipsize='1280', plevel='LEVEL2A'):
    logging.debug(
        f"{lon} {lat} {start_date} {end_date} {unique_id} {band} {plevel}")

    numchips = rce.parallelExtract(lon, lat, start_date, end_date, unique_id,
                                   band, chipsize, plevel)

    if numchips == -1:
        print(f"Request results in too many chips, please revise selection")
    elif numchips > 0:
        print(f"New chips ara in {unique_id}")
    else:
        print(f"Chips already cached in {unique_id}")

    print(rce.buildJSON(unique_id, start_date, end_date))
    return True


def getRawChipsBatch(unique_id):
    # params are dumped in params.json on unique_id directory

    logging.debug(unique_id)
    numchips = rceb.parallelExtract(unique_id)

    if numchips == -1:
        print(f"Request results in too many chips, please revise selection")
    elif numchips > 0:
        print(rceb.chipCollect(unique_id))
    else:
        print(f"Chips already cached in {unique_id}")

    print(rceb.buildJSON(unique_id))
    return True


def getRawS1ChipsBatch(unique_id):
    # params are dumped in params.json on unique_id directory

    logging.debug(unique_id)

    numchips = rces1.parallelExtract(unique_id)

    if numchips == -1:
        print(f"Request results in too many chips, please revise selection")
    elif numchips > 0:
        print(rces1.chipCollect(unique_id))
    else:
        print(f"Chips already cached in {unique_id}")

    print(rces1.buildJSON(unique_id))
    return True
