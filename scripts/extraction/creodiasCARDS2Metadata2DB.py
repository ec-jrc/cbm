#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Version   : 

# # Query And Transfer CARD Metadata with XMLHttpRequests (CREODIAS)
#
# CREODIAS ingests the metadata for the generated CARD data in the [CREODIAS
#   public catalog](http://finder.creodias.eu)
#
# The catalog interface uses the OpenSearch API, a standard to define catalog
#   queries with a set of standards query parameters, and which produces either
#   JSON or XML formatted response which we can parse into our data base.
#
# In this notebook, we show how to find the data and transfer the relevant
#   metadata records and attributes to the DIAS data base. This is primarily
#   done to make sure we can run the same scripts across different DIAS
#   instances using the same data base table (so that portability is easy).
#
# We apply the concepts from the __SimpleDatabaseQueries__ notebook.
#
# Revision: 2019-09-03: Switch from georss to gml geometry parsing (georss does
#   not support MULTIPOLYGON geometry, introduced by ESA in 2019.

import sys
import requests
from lxml import etree
import psycopg2
from datetime import datetime

# Define the query string for the DIAS catalog search
# Get the bounding polygon for the Area of Interest
# Catalunya:
#   """POLYGON((0.58+40.5,3.33+41.8,3.33+42.5,0.61+42.9,0.04+40.7,0.58+40.5))"""
# Denmark:
#   POLYGON((8.0+54.8,8.0+57.0,10.7+57.8,13.2+55.2,15.3+55.3,15.4+54.9,12.0+54.5,8.0+54.7,8.0+54.8))
# NL + NRW:
#   POLYGON((3.0+51.27,6.49+50.27,9.66+51.22,9.135+52.618,7.28+52.47,7.213+53.515,4.774+53.56,3.0+51.27))

aoi = """POLYGON((3.0+51.27,6.49+50.27,9.66+51.22,9.135+52.618,7.28+52.47,7.213+53.515,4.774+53.56,3.0+51.27))"""

# Query must be one continuous line, without line breaks!!
url = """https://finder.creodias.eu/resto/api/collections/Sentinel2/search.atom?maxRecords=2000&startDate={}&completionDate={}&processingLevel={}&sortParam=startDate&sortOrder=descending&status=all&geometry={}&dataset=ESA-DATASET"""

# We adapt the period to make sure we get no more than 2000 records (the maximum
#   number of return records).
# For Catalonya, we expect in the order of 600 records for CARD-BS
startDate = '{}T00:00:00Z'.format(sys.argv[1])
endDate = '{}T00:00:00Z'.format(sys.argv[2])
ptype = sys.argv[3]   # LEVEL2A or LEVEL2AP
card = sys.argv[4]    # s2

url = url.format(startDate, endDate, ptype, aoi)

r = requests.get(url)

contentType = r.headers.get('content-type').lower()

# If all goes well, we should get 'application/atom.xml' as contentType
print(contentType)


# Prepare the database for record ingestion

insertSql = """
    INSERT into dias_catalogue (obstime, reference, sensor, card, footprint)
    values ('{}'::timestamp, '{}', '{}', '{}', ST_GeomFromText('{}', 4326))
    """

if contentType.find('xml') == -1:
    print("FAIL: Server does not return XML content for metadata, but {}.".format(
        contentType))
    print(r.content)
else:
    # Some special response handling
    respString = r.content.decode('utf-8').replace('resto:', '')

    # replace required to avoid namespace bug
    meta = etree.fromstring(bytes(respString, encoding='utf-8'))

    entries = meta.xpath(
        '//a:entry', namespaces={'a': 'http://www.w3.org/2005/Atom'})
    print(len(entries))


if len(entries) > 0:
    try:
        conn = psycopg2.connect(
            "dbname='postgres' user='postgres' host='172.17.0.2'")
    except Exception:
        print("I am unable to connect to the database")
        sys.exit(1)

cur = conn.cursor()

# The XML parsing will select relevant metadata parameters and reformats these
#   into records to insert into the __dias_catalogue__ table.
# Note that rerunning the parsing will skip records that are already in the
#   table with an existing reference attribute (the primary key).
# Rerunning will, thus, only add new records.

for e in entries:
    title = e.xpath('a:title', namespaces={'a': 'http://www.w3.org/2005/Atom'})
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
            cur.execute(insertSql.format(tstamp[0].text.replace(
                'T', ' '), title[0].text, sensor, card, footprint))
            conn.commit()
        except psycopg2.IntegrityError:
            print("Skipping duplicate record for {}!".format(title[0].text))
            conn.rollback()

    except Exception:
        print("Polygon parsing issues for {} with polygon {}".format(
            title[0].text, polygon))

# Important attributes in the __dias_catalogue__ table are:
#
#  - _reference_: this is the unique reference, with which the S3 object storage
#       key to locate the relevant file(s) can be created;
#  - _obstime_: the image acquisition time stamp (UTC);
#  - _sensor_: the sensor (1A, 1B, 2A or 2B);
#  - _card_: this is the CARD type. Together with _sat_ they point to the
#       expected CARD types, but _type_ is unique already;
#  - _footprint_: this is the footprint geometry of the CARD image;
#
# Note that, for Sentinel-1, we do not store the orbit direction (_ASCENDING_
#       or _DESCENDING_). As a general rule, UTC time stamps in the (local)
#       morning are for descending orbits, in the evening for ascending orbits.

# Get some statistics on CARD types that are available for this area of interest
getMetadataSql = """
    SELECT card, sensor, count(*), min(obstime), max(obstime)
    FROM dias_catalogue
    WHERE st_intersects(footprint, st_geomfromtext('{}', 4326))
    GROUP by card, sensor order by card, sensor;
""".format(aoi.replace('+', ' '))

cur.execute(getMetadataSql)
# Get the columns names for the rows
colnames = [desc[0] for desc in cur.description]
print(colnames)

for rows in cur:
    print(rows[0:3], datetime.strftime(rows[3], '%Y-%m-%d %H:%M:%S'),
          datetime.strftime(rows[4], '%Y-%m-%d %H:%M:%S'))


# Each record get the _status_ 'ingested' by default.
# Close database connection

cur.close()
conn.close()
