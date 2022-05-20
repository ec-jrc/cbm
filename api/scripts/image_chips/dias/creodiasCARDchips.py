#!/usr/bin/env python
# coding: utf-8

#
# Get key to relevant CARD products in CREODIAS catalog
# Version 1.3 - 2020-05-14
# - Make end date inclusive
#
# Version 1.2 - 2020-04-14
# - Changed to JSON format parsing
# - added s1 selection
#
# Version 1.1 - 2020-03-24
# - Include intersection calculation
#

import requests
import pandas as pd

import logging

from osgeo import ogr, osr

# Define the query string for the DIAS catalog search


def ogr_intersect(lon, lat, chipsize, footprint):
    # footprint expected as GML
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(lon, lat)
    logging.debug(point)
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    # Do all calcs in EPSG:3857
    target = osr.SpatialReference()
    target.ImportFromEPSG(3857)

    transform = osr.CoordinateTransformation(source, target)

    point.Transform(transform)

    # env = [minX, maxX, minY, maxY]
    env = point.Buffer(chipsize // 2).GetEnvelope()

    chip = ogr.Geometry(ogr.wkbLinearRing)
    chip.AddPoint(env[0], env[2])
    chip.AddPoint(env[0], env[3])
    chip.AddPoint(env[1], env[3])
    chip.AddPoint(env[1], env[2])
    chip.AddPoint(env[0], env[2])

    chipPoly = ogr.Geometry(ogr.wkbPolygon)
    chipPoly.AddGeometry(chip)

    imagePoly = ogr.CreateGeometryFromGML(footprint)
    imagePoly.Transform(transform)
    intersection = imagePoly.Intersection(chipPoly)
    return intersection.GetArea() / chipPoly.GetArea()


def getS2Chips(lon, lat, startDate, endDate, chipsize=1280, ptype='LEVEL2A'):
    # Select all footprint that intersect with the chip centroid
    aoi = "POINT({}+{})".format(lon, lat)
    # Query must be one continuous line, without line breaks!!
    url = """https://finder.creodias.eu/resto/api/collections/Sentinel2/search.json?maxRecords=2000&startDate={}T00:00:00Z&completionDate={}T23:59:59Z&processingLevel={}&sortParam=startDate&sortOrder=descending&status=all&geometry={}&dataset=ESA-DATASET"""

    url = url.format(startDate, endDate, ptype, aoi)

    response = requests.get(url)

    contentType = response.headers.get('content-type').lower()

    entries = []
    references = []

    if contentType.find('json') == -1:
        print("FAIL: Server does not return JSON content for metadata, but {}.".format(
            contentType))
        print(response.content)
    else:
        featureCollection = response.json()

        for f in featureCollection['features']:
            reference = {}
            # The productIdentifier serves as key, but we want to keep orbitDirection
            reference['id'] = f['properties']['productIdentifier'].split(
                '/')[-1]
            footprint = f['properties']['gmlgeometry']
            reference['chipoverlap'] = ogr_intersect(
                lon, lat, chipsize, footprint)
            references.append(reference)

    return references


def rinseAndDryS2(references):
    # Chips can have the same time stamp but different processor versions. Eliminate the lowest version.
    df = pd.DataFrame(references, columns=['id', 'chipoverlap'])
    # S2 chips have id like: /eodata/Sentinel-2/MSI/L2A/2019/05/03/S2A_MSIL2A_20190503T104031_N0211_R008_T31TEG_20190503T112944.SAFE
    df['tstamp'] = df.id.apply(lambda r: r.split('_')[2])
    df['version'] = df.id.apply(lambda r: r.split('_')[3])
    df.sort_values(by=['chipoverlap', 'version', 'tstamp'], inplace=True)
    df.drop_duplicates(subset='tstamp', keep='last', inplace=True)
    return list(df.id)


def getS1Chips(lon, lat, startDate, endDate, chipsize=1280, ptype='CARD-BS'):
    aoi = "POINT({}+{})".format(lon, lat)
    # Query must be one continuous line, without line breaks!!
    url = """https://finder.creodias.eu/resto/api/collections/Sentinel1/search.json?maxRecords=2000&startDate={}T00:00:00Z&completionDate={}T23:59:59Z&productType={}&sortParam=startDate&sortOrder=descending&status=all&geometry={}&dataset=ESA-DATASET"""

    url = url.format(startDate, endDate, ptype, aoi)

    response = requests.get(url)

    contentType = response.headers.get('content-type').lower()
    references = []

    if contentType.find('json') == -1:
        print("FAIL: Server does not return JSON content for metadata, but {}.".format(
            contentType))
        print(response.content)
    else:
        featureCollection = response.json()

        for f in featureCollection['features']:
            reference = {}
            # The productIdentifier serves as key, but we want to keep orbitDirection
            reference['id'] = f['properties']['productIdentifier'].split(
                '/')[-1]
            reference['orbitDirection'] = f['properties']['orbitDirection']
            footprint = f['properties']['gmlgeometry']
            reference['chipoverlap'] = ogr_intersect(
                lon, lat, chipsize, footprint)
            references.append(reference)

    return references


def rinseAndDryS1(references):
    # Chips can have the same time stamp. Eliminate only if from same orbitDirection.
    df = pd.DataFrame(references, columns=[
                      'id', 'orbitDirection', 'chipoverlap'])
    # S1 chips have id like: /eodata/Sentinel-1/SAR/CARD-BS/2019/03/01/S1B_IW_GRDH_1SDV_20190301T172436_20190301T172501_015164_01C5BF_40F5_CARD_BS
    df['tstamp'] = df.id.apply(lambda r: r.split(
        '_')[4][0:8] if r.endswith('CARD_BS') else r.split('_')[1][0:8])
    df.sort_values(
        by=['chipoverlap', 'orbitDirection', 'tstamp'], inplace=True)
    df.drop_duplicates(subset='tstamp', keep='last', inplace=True)
    return list(df.id)


if __name__ == "__main__":
    references = getS2Chips(3.11804, 42.2436, '2019-05-01', '2019-06-01', 1280)
    print(references)
    print()
    print(rinseAndDryS2(references))

    # print(getS2Chips(5.772, 52.735, '2018-01-01', '2018-05-01', 'LEVEL2AP'))
    s1_refs = getS1Chips(5.772, 52.735, '2019-03-01', '2019-05-01', 2560)
    print(len(s1_refs))
    print()
    print(len(rinseAndDryS1(s1_refs)))
    print()
    for f in rinseAndDryS1(s1_refs):
        print(f)

    # CARD-COH6 should not have duplicates...
    s1_coh6 = getS1Chips(5.772, 52.735, '2019-03-01',
                         '2019-04-01', 1280, 'CARD-COH6')

    for f in rinseAndDryS1(s1_coh6):
        print(f)
