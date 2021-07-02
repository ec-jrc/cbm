#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


# # Query And Transfer CARD Metadata with XMLHttpRequests (CREODIAS)
#
# CREODIAS ingests the metadata for the generated CARD data in the
# [CREODIAS public catalog](http://finder.creodias.eu)
#
# The catalog interface uses the OpenSearch API, a standard to define catalog
# queries with a set of standards query parameters, and which produces either
# JSON or XML formatted response which we can parse into our data base.


import sys
import requests
from lxml import etree
import psycopg2
from datetime import datetime
from cbm.datas import db


def main(tb_prefix, aoi, start, end, card, option):
    """
    start, end : 2019-06-01
    option: s1 ptype CARD-COH6 or CARD-BS, s2 plevel : LEVEL2A or LEVEL2AP
    card : s2, c6 or bs
    """

    root = "https://finder.creodias.eu"
    path = "/resto/api/collections/Sentinel{}/search.atom?"

    # CREODIAS API Requests for card catalogue
    # We adapt the period to make sure we get no more than 2000 records
    # (the maximum number of return records).
    p1 = "maxRecords=2000&startDate={}&completionDate={}"
    if card == 's2':
        p2 = "&processingLevel={}&sortParam=startDate"
        sat = '2'
    else:
        p2 = "&productType={}&sortParam=startDate"
        sat = '1'
    p3 = "&sortOrder=descending&status=all&geometry={}&dataset=ESA-DATASET"
    url = f"{root}{path}{p1}{p2}{p3}"

    startDate = '{}T00:00:00Z'.format(start)
    endDate = '{}T00:00:00Z'.format(end)

    url = url.format(sat, startDate, endDate, option, aoi)

    r = requests.get(url)
    contentType = r.headers.get('content-type').lower()

    # If all goes well, we should get 'application/atom.xml' as contentType
    # print(contentType)

    # Prepare the database for record ingestion
    insertSql = """
        INSERT into {}_dias_catalogue (obstime, reference,
            sensor, card, footprint)
        values ('{}'::timestamp, '{}', '{}', '{}', ST_GeomFromText('{}', 4326))
        """

    if contentType.find('xml') == -1:
        print("FAIL: Server does not return XML content for metadata, {}.".format(
            contentType))
        print(r.content)
    else:
        # Some special response handling
        respString = r.content.decode('utf-8').replace('resto:', '')

        # replace required to avoid namespace bug
        meta = etree.fromstring(bytes(respString, encoding='utf-8'))

        entries = meta.xpath(
            '//a:entry', namespaces={'a': 'http://www.w3.org/2005/Atom'})
        print(f"{len(entries)} CARD entries found ...")

    try:
        conn = db.connection()
        cur = conn.cursor()
    except Exception:
        print("Can not connect to the database")
        sys.exit(1)


    # The XML parsing will select relevant metadata parameters and reformats
    # these into records to insert into the __dias_catalogue__ table.
    # Note that rerunning the parsing will skip records that are already in
    # the table with an existing reference attribute (the primary key).
    # Rerunning will, thus, only add new records.

    if len(entries) > 0:
        for e in entries:
            title = e.xpath('a:title', namespaces={
                            'a': 'http://www.w3.org/2005/Atom'})
            # print(title[0].text)
            sensor = title[0].text[1:3].strip()
            # print(sensor)
            tstamp = e.xpath('gml:validTime/gml:TimePeriod/gml:beginPosition',
                             namespaces={'gml': 'http://www.opengis.net/gml'})
            # print(tstamp[0].text)
            polygon = e.xpath('.//gml:coordinates',
                              namespaces={'gml': 'http://www.opengis.net/gml'})
            try:
                coords = polygon[0].text
                # print(coords)
                footprint = 'POLYGON(({}))'.format(coords.replace(
                    ' ', ';').replace(',', ' ').replace(';', ','))
                try:
                    cur.execute(insertSql.format(tb_prefix,
                                                 tstamp[0].text.replace('T', ' '),
                                                 title[0].text, sensor,
                                                 card, footprint))
                    conn.commit()
                except psycopg2.IntegrityError as err:
                    print("Skipping duplicate record!", err)
                    conn.rollback()

            except Exception:
                print("Polygon parsing issues for {} with polygon {}".format(
                    title[0].text, polygon))

        # Important attributes in the __dias_catalogue__ table are:
        #
        #  - _reference_: this is the unique reference, with which the S3 object
        #       storage key to locate the relevant file(s) can be created;
        #  - _obstime_: the image acquisition time stamp (UTC);
        #  - _sensor_: the sensor (1A, 1B, 2A or 2B);
        #  - _card_: this is the CARD type. Together with _sat_ they point to the
        #       expected CARD types, but _type_ is unique already;
        #  - _footprint_: this is the footprint geometry of the CARD image;
        #
        # Note that, for Sentinel-1, we do not store the orbit direction
        #   (_ASCENDING_ or _DESCENDING_). As a general rule, UTC time stamps in
        #   the (local) morning are for descending orbits, in the evening for
        #   ascending orbits.

        # Get statistics on CARD types that are available for this area of interest
        getMetadataSql = """
            SELECT card, sensor, count(*), min(obstime), max(obstime)
            FROM {}_dias_catalogue
            WHERE st_intersects(footprint, st_geomfromtext('{}', 4326))
            GROUP by card, sensor
            ORDER by card, sensor;
        """.format(tb_prefix, aoi.replace('+', ' '))

        cur.execute(getMetadataSql)
        # Get the columns names for the rows
        print("Sample entries:")
        colnames = [desc[0] for desc in cur.description]
        print(colnames)

        for rows in cur:
            print(rows[0:3], datetime.strftime(rows[3], '%Y-%m-%d %H:%M:%S'),
                  datetime.strftime(rows[4], '%Y-%m-%d %H:%M:%S'))

        # Each record get the _status_ 'ingested' by default.
        # Close database connection

    cur.close()
    conn.close()

if __name__ == "__main__":
    import sys
    main(sys.argv)
