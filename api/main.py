#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import csv
import json
import glob
import logging
import traceback
from io import StringIO
from time import strftime
from decimal import Decimal
from functools import wraps
from flasgger import Swagger
from logging.handlers import TimedRotatingFileHandler
from flask import (Flask, request, send_from_directory, make_response,
                   render_template, abort, url_for, current_app)

from scripts import (db_queries, users, info_page,
                     file_manager, backgroundExtract)
from scripts.chip_extract import (creodiasCARDchips, rawChipExtractor,
                                  chipS2Extractor, rawChipBatchExtract,
                                  rawS1ChipBatchExtract)

# Global variables
UPLOAD_ENABLE = False  # Enable upload page (http://HOST/files/upload).
DEFAULT_AOI = ''
STORAGE = 'files'  # Storage folder


app = Flask(__name__)
app.secret_key = os.urandom(12)
datasets = db_queries.get_datasets()

try:
    import flask_monitoringdashboard as dashboard
    dashboard.bind(app)
    # dashboard.config.init_from(file='config/dashboard.cfg')
except Exception as err:
    print("!ERROR! Can not start dashboard.", err)


# -------- Core functions ---------------------------------------------------- #

# app.debug = True
logname = 'logs/main.log'
handler = TimedRotatingFileHandler(logname, when='midnight', interval=1)
handler.suffix = '%Y%m%d'
logger = logging.getLogger('tdm')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
user = 'None'


@app.after_request
def after_request(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    if request.path.split('/')[1] == 'query' and user != 'None':
        logger.error('%s %s %s %s %s %s %s', timestamp, request.remote_addr,
                     user, request.method, request.scheme,
                     request.full_path, response.status)
    try:
        print('%s %s %s %s %s %s %s', timestamp, request.remote_addr,
              user, request.method, request.scheme, request.full_path,
              response.status)
    except Exception:
        print('%s %s %s %s %s %s', timestamp, request.remote_addr,
              request.method, request.scheme, request.full_path,
              response.status)
    return response


@app.errorhandler(Exception)
def exceptions(e):
    tb = traceback.format_exc()
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    try:
        print('%s %s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s', timestamp,
              user, request.remote_addr, request.method, request.scheme,
              request.full_path, tb)
    except Exception:
        print('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s', timestamp,
              request.remote_addr, request.method, request.scheme,
              request.full_path, tb)
    return e


def auth_required(f):  # Authentication decorator.
    @wraps(f)
    def decorated(*args, **kwargs):
        global user
        auth = request.authorization
        try:
            user = auth.username
        except Exception:
            user = 'None'
        if auth and users.auth(auth.username, auth.password) is True:
            if 'aoi' in request.args.keys():
                aoi = request.args.get('aoi').lower()
                if users.data_auth(aoi, auth.username):
                    return f(*args, **kwargs)
                else:
                    return make_response(
                        """Not authorized for this dataset.
                        Please contact the system administrator.""", 401)
            else:
                return f(*args, **kwargs)
        return make_response(
            'Could not verify.', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(CustomJsonEncoder, self).default(obj)


def get_user_id():
    return user


swag = Swagger(app, decorators=[auth_required],
               template_file='static/swagger.yaml')
try:
    dashboard.config.group_by = get_user_id
except Exception:
    print('could not load dashboard')


@app.route('/query/info', methods=['GET'])
@auth_required
def info():
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    else:
        aoi = ''
    info_dict = info_page.generator(user, aoi)
    return current_app.response_class(json.dumps(info_dict, indent=4),
                                      mimetype="application/json")


@app.route('/static/tmp/<unique_id>/<png_id>')
# @auth_required
def statictmp(unique_id, png_id):
    try:
        return send_from_directory(f"static/tmp/{unique_id}", png_id)
    except FileNotFoundError:
        abort(404)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico')


# -------- Queries - Background Images --------------------------------------- #

@app.route('/query/backgroundByLocation', methods=['GET'])
@auth_required
def backgroundByLocation_query():
    """
    Generate an extract from either Google or Bing.
    It uses the WMTS standard to grab and compose, which makes it fast
    (does not depend on DIAS S3 store).
    responses:
        description: An HTML page that displays the selected chip as a PNG tile.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    lon = request.args.get('lon')
    lat = request.args.get('lat')
    chipsize = '256'
    chipextend = '256'
    tms = 'Google'
    iformat = 'png'
    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    if 'extend' in request.args.keys():
        chipextend = request.args.get('extend')
    if 'tms' in request.args.keys():
        tms = request.args.get('tms')
    if 'iformat' in request.args.keys():
        iformat = request.args.get('iformat')

    unique_id = f"static/tmp/E{lon}N{lat}_{chipsize}_{chipextend}_{tms}".replace('.', '_')
    data = backgroundExtract.getBackgroundExtract(
        lon, lat, chipsize, chipextend, unique_id, tms, iformat, False)
    if data:
        if 'raw' in request.args.keys() or iformat == 'tif':
            return f"{unique_id}/{tms.lower()}.{iformat}"
        else:
            flist = glob.glob(f"{unique_id}/{tms.lower()}.{iformat}")
            full_filename = url_for(
                'static', filename=flist[0].replace('static/', ''))
            return render_template("bg_page.html", bg_image=full_filename)
    else:
        return {}


@app.route('/query/backgroundByParcelID', methods=['GET'])
@auth_required
def backgroundByID_query():
    """
    Generate an extract from either Google or Bing.
    It uses the WMTS standard to grab and compose, which makes it fast
    (does not depend on DIAS S3 store).
    responses:
        description: An HTML page that displays the selected chip as a PNG tile.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    ptype = ''
    chipsize = '256'
    chipextend = '256'
    tms = 'google'
    iformat = 'png'
    withGeometry = False
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    if 'extend' in request.args.keys():
        chipextend = request.args.get('extend')
    if 'tms' in request.args.keys():
        tms = request.args.get('tms').lower()
    if 'iformat' in request.args.keys():
        iformat = request.args.get('iformat')
    if 'withGeometry' in request.args.keys():
        if request.args.get('withGeometry') == 'True':
            withGeometry = [aoi, year, pid, ptype]

    dataset = datasets[f'{aoi}_{year}']
    lon, lat = db_queries.getParcelCentroid(dataset, pid, ptype)
    unique_id = f"static/tmp/E{lon}N{lat}_{chipsize}_{chipextend}_{tms}".replace('.', '_')
    data = backgroundExtract.getBackgroundExtract(
        lon, lat, chipsize, chipextend, unique_id, tms, iformat, withGeometry)
    if data:
        if 'raw' in request.args.keys() or iformat == 'tif':
            return f"{unique_id}/{tms.lower()}.{iformat}"
        else:
            flist = glob.glob(f"{unique_id}/{tms.lower()}.{iformat}")
            full_filename = url_for(
                'static', filename=flist[0].replace('static/', ''))
            return render_template("bg_page.html", bg_image=full_filename)
    else:
        return {}


# -------- Queries - Chip Images --------------------------------------------- #


@app.route('/query/chipsByLocation', methods=['GET'])
@auth_required
def chipsByLocation_query():
    """
    Get chips images by location.
    Generates a series of extracted Sentinel-2 LEVEL2A segments
    of 128x128 pixels as a composite of 3 bands.
    responses:
        description: An HTML page that displays the selected chips in a table
        with max. 8 columns.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if 'lut' in request.args.keys():
        lut = request.args.get('lut')
    else:
        lut = '5_95'
    if 'bands' in request.args.keys():
        bands = request.args.get('bands')
    else:
        bands = 'B08_B04_B03'
    if 'plevel' in request.args.keys():
        plevel = request.args.get('plevel')
    else:
        plevel = 'LEVEL2A'

    unique_id = f"static/tmp/E{lon}N{lat}L{lut}_{plevel}_{bands}".replace(
        '.', '_')
    data = chipS2Extractor.parallelExtract(
        lon, lat, start_date, end_date, unique_id, lut, bands, plevel)
    chipS2Extractor.buildHTML(unique_id, start_date, end_date)
    if data >= 0:
        return send_from_directory(unique_id, 'chipsview.html')
    else:
        return {}


@app.route('/query/chipsByParcelID', methods=['GET'])
@auth_required
def chipsByParcelID_query():
    """
    Get chips images by parcel id.
    Generates a series of extracted Sentinel-2 LEVEL2A segments
    of 128x128 pixels as a composite of 3 bands.
    responses:
        description: Returns a html with the images
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    band = request.args.get('band')
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'plevel' in request.args.keys():
        plevel = request.args.get('plevel')
    else:
        plevel = 'LEVEL2A'
    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    else:
        chipsize = '1280'
    ptype = ''
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    dataset = datasets[f'{aoi}_{year}']
    pdata = db_queries.getParcelByID(dataset, pid, ptype, False, False)
    if not pdata:
        parcel = {}
    elif len(pdata) == 1:
        parcel = dict(zip(list(pdata[0]),
                          [[] for i in range(len(pdata[0]))]))
    else:
        parcel = dict(zip(list(pdata[0]),
                          [list(i) for i in zip(*pdata[1:])]))

    lon = str(json.loads(parcel)['clon'][0])
    lat = str(json.loads(parcel)['clat'][0])
    unique_id = f"static/tmp/E{lon}N{lat}_{plevel}_{chipsize}_{band}".replace(
        '.', '_')
    data = chipS2Extractor.parallelExtract(
        lon, lat, start_date, end_date, unique_id, band, chipsize, plevel)
    if data:
        return send_from_directory(unique_id, 'chipslist.json')
    else:
        return {}


@app.route('/query/rawChipByLocation', methods=['GET'])
@auth_required
def rawChipByLocation_query():
    """
    Get chips images by parcel location.
    Generates a series of extracted Sentinel-2 LEVEL2A segments of 128x128 (10m
    resolution bands) or 64x64 (20 m) pixels as list of full resolution GeoTIFFs
    responses:
        description: A JSON dictionary with date labels and
        relative URLs to cached GeoTIFFs.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    band = request.args.get('band')
    if 'band' in request.args.keys():
        band = request.args.get('band')
    else:
        band = None
    if 'plevel' in request.args.keys():
        plevel = request.args.get('plevel')
    else:
        plevel = 'LEVEL2A'
    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    else:
        chipsize = '1280'
    if 'onlylist' in request.args.keys():
        onlylist = True if request.args.get('onlylist') == 'True' else False
        if onlylist:
            chiplist = creodiasCARDchips.getS2Chips(float(lon), float(
                lat), start_date, end_date, int(chipsize), plevel)
            chiplist = creodiasCARDchips.rinseAndDryS2(chiplist)
            return {'chips': chiplist}
    unique_id = f"static/tmp/E{lon}N{lat}_{plevel}_{chipsize}_{band}".replace(
        '.', '_')
    data = rawChipExtractor.parallelExtract(
        lon, lat, start_date, end_date, unique_id, band, chipsize, plevel)
    rawChipExtractor.buildJSON(unique_id, start_date, end_date)
    if data >= 0:
        return send_from_directory(unique_id, 'chipslist.json')
    else:
        return {}


@app.route('/query/rawChipByParcelID', methods=['GET'])
@auth_required
def rawChipByParcelID_query():
    """
    Get chips images by parcel ID.
    Generates a series of extracted Sentinel-2 LEVEL2A segments of 128x128 (10m
    resolution bands) or 64x64 (20 m) pixels as list of full resolution GeoTIFFs
    responses:
        description: A JSON dictionary with date labels and
        relative URLs to cached GeoTIFFs.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    ptype = ''
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    band = request.args.get('band')
    plevel = 'LEVEL2A'
    chipsize = '1280'
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    if 'plevel' in request.args.keys():
        plevel = request.args.get('plevel')
    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    if 'onlylist' in request.args.keys():
        onlylist = True if request.args.get('onlylist') == 'True' else False
    dataset = datasets[f'{aoi}_{year}']
    pdata = db_queries.getParcelByID(dataset, pid, ptype, False, False)
    if not pdata:
        parcel = {}
    elif len(pdata) == 1:
        parcel = dict(zip(list(pdata[0]),
                          [[] for i in range(len(pdata[0]))]))
    else:
        parcel = dict(zip(list(pdata[0]),
                          [list(i) for i in zip(*pdata[1:])]))
    lon = str(json.loads(parcel)['clon'][0])
    lat = str(json.loads(parcel)['clat'][0])
    if 'onlylist' in request.args.keys():
        onlylist = True if request.args.get('onlylist') == 'True' else False
        if onlylist:
            chiplist = creodiasCARDchips.getS2Chips(float(lon), float(
                lat), start_date, end_date, int(chipsize), plevel)
            chiplist = creodiasCARDchips.rinseAndDryS2(chiplist)
            return {'chips': chiplist}
    unique_id = f"static/tmp/E{lon}N{lat}_{plevel}_{chipsize}_{band}".replace(
        '.', '_')
    data = rawChipExtractor.parallelExtract(
        lon, lat, start_date, end_date, unique_id, band, chipsize, plevel)
    rawChipExtractor.buildJSON(unique_id, start_date, end_date)
    if data >= 0:
        return send_from_directory(unique_id, 'chipslist.json')
    else:
        return {}


# -------- Queries - raw Chip Images Batch ----------------------------------- #

@app.route('/query/rawChipsBatch', methods=['POST'])
@auth_required
def rawChipsBatch_query():
    """
    Get chips images with post requst.
    responses:
        description: A JSON dictionary with date labels and
        relative URLs to cached GeoTIFFs.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    required = ["lon", "lat", "tiles", "bands", "chipsize"]
    if request.is_json:
        params = request.get_json()
        i = 0
        for k in params.keys():
            if k not in required:
                return {"error": f"{k} not allowed as key"}
            else:
                i += 1
        if i != len(required):
            return {"error": f"{i} parameters supplied, {len(required)} required"}
    unique_id = f"static/tmp/{params.get('lon')}_{params.get('lat')}_{params.get('chipsize')}_RAW".replace('.', '_')
    logger.info(unique_id)

    if not os.path.exists(unique_id):
        os.makedirs(unique_id)
    with open(f"{unique_id}/params.json", "w") as f:
        logger.info("Dumping params")
        f.write(json.dumps(params))

    data = rawChipBatchExtract.parallelExtract(unique_id)
    rawChipBatchExtract.buildJSON(unique_id)
    if data >= 0:
        return send_from_directory(unique_id, 'chipslist.json')
    else:
        return {}


@app.route('/query/rawS1ChipsBatch', methods=['POST'])
@auth_required
def rawS1ChipsBatch_query():
    """
    Get S1 chips images with post requst.
    responses:
        description: A JSON dictionary with date labels and
        relative URLs to cached GeoTIFFs.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    required = ["lon", "lat", "dates", "chipsize", "plevel"]
    if request.is_json:
        params = request.get_json()
        i = 0
        for k in params.keys():
            if k not in required:
                return {"error": f"{k} not allowed as key"}
            else:
                i += 1
        if i != len(required):
            return {"error": f"{i} parameters supplied, {len(required)} required"}
    unique_id = f"static/tmp/{params.get('lon')}_{params.get('lat')}_{params.get('chipsize')}_{params.get('plevel')}_RAW".replace('.', '_')
    logger.info(unique_id)

    if not os.path.exists(unique_id):
        os.makedirs(unique_id)
    with open(f"{unique_id}/params.json", "w") as f:
        logger.info("Dumping params")
        f.write(json.dumps(params))

    data = rawS1ChipBatchExtract.parallelExtract(unique_id)
    rawS1ChipBatchExtract.buildJSON(unique_id)
    if data >= 0:
        return send_from_directory(unique_id, 'chipslist.json')
    else:
        return {}


# -------- Queries - Parcel Peers -------------------------------------------- #

@app.route('/query/parcelPeers', methods=['GET'])
@auth_required
def parcelPeers_query():
    """
    Get the parcel “peers” for a known parcel ID,
    responses:
        List of parcel IDs
    """

    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    distance = 2000.0
    maxPeers = 10
    ptype = ''
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    if 'distance' in request.args.keys():
        distance = float(request.args.get('distance'))
    if 'max' in request.args.keys():
        maxPeers = int(request.args.get('max'))

    # if distance > 5000.0: #  Set MAX distance
    #     distance = 5000.0
    if maxPeers > 10000:  # Set MAX number of parcel IDs
        maxPeers = 10000

    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelPeers(dataset, pid, distance, maxPeers, ptype)
    if not data:
        return {}
    elif len(data) == 1:
        return dict(zip(list(data[0]),
                        [[] for i in range(len(data[0]))]))
    else:
        return dict(zip(list(data[0]),
                        [list(i) for i in zip(*data[1:])]))


# -------- Queries - Time Series --------------------------------------------- #

@app.route('/query/parcelTimeSeries', methods=['GET'])
@auth_required
def parcelTimeSeries_query():
    """
    Get the time series for a parcel ID.
    """
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    ptype = ''
    tstype = 's2'
    band = ''
    scl = True
    ref = False
    tsformat = False
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    if 'scl' in request.args.keys():
        scl = True if request.args.get('scl') == 'True' else False
    if 'band' in request.args.keys():
        band = request.args.get('band')
    if 'tstype' in request.args.keys():
        tstype = request.args.get('tstype')
        if tstype.lower() in ['bs', 'c6']:
            scl = False
    if 'ref' in request.args.keys():
        ref = True if request.args.get('ref') == 'True' else False
    if 'tsformat' in request.args.keys():
        tsformat = True if request.args.get('tsformat') == 'csv' else False

    dataset = datasets[f'{aoi}_{year}']
    if tstype.lower() == 'scl':
        data = db_queries.getParcelSCL(dataset, pid, ptype)
    else:
        data = db_queries.getParcelTimeSeries(dataset, pid, ptype,
                                              tstype, band, scl, ref)
    if tsformat:
        io_file = StringIO()
        write = csv.writer(io_file, delimiter=',')
        write.writerows(data)
        csv_file = make_response(io_file.getvalue())
        fname = f"filename=timeseries_{aoi}{year}{ptype}_{pid}_{tstype}.csv"
        csv_file.headers["Content-Disposition"] = f"attachment; {fname}"
        csv_file.headers["Content-type"] = "text/csv"
        return csv_file
    else:
        if not data:
            return {}
        elif len(data) == 1:
            return dict(zip(list(data[0]),
                            [[] for i in range(len(data[0]))]))
        else:
            return json.dumps(dict(zip(list(data[0]),
                                       [list(i) for i in zip(*data[1:])])),
                              cls=CustomJsonEncoder)


@app.route('/query/weatherTimeSeries', methods=['GET'])
@auth_required
def meteo():
    """
    Get weather time series for a parcel ID.
    """

    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    ptype = ''
    tsformat = False
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    if 'tsformat' in request.args.keys():
        tsformat = True if request.args.get('tsformat') == 'csv' else False
    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelWeatherTS(dataset, pid, ptype)
    if tsformat:
        io_file = StringIO()
        write = csv.writer(io_file, delimiter=',')
        write.writerows(data)
        csv_file = make_response(io_file.getvalue())
        fname = f"filename=timeseries_{aoi}{year}{ptype}_{pid}_WeatherTS.csv"
        csv_file.headers["Content-Disposition"] = f"attachment; {fname}"
        csv_file.headers["Content-type"] = "text/csv"
        return csv_file
    else:
        if not data:
            return {}
        elif len(data) == 1:
            return dict(zip(list(data[0]),
                            [[] for i in range(len(data[0]))]))
        else:
            return json.dumps(dict(zip(list(data[0]),
                                       [list(i) for i in zip(*data[1:])])),
                              cls=CustomJsonEncoder)


# -------- Queries - Parcel information -------------------------------------- #

@app.route('/query/parcelByLocation', methods=['GET'])
@auth_required
def parcelByLocation_query():
    """
    Find parcel information for a geographical location.
    """

    aoi = DEFAULT_AOI
    year = request.args.get('year')
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    ptype = ''
    withGeometry = True if request.args.get(
        'withGeometry') == 'True' else False
    wgs84 = True if request.args.get('wgs84') == 'True' else False
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelByLocation(dataset, lon, lat, ptype,
                                          withGeometry, wgs84)
    if not data:
        return {}
    elif len(data) == 1:
        return dict(zip(list(data[0]),
                        [[] for i in range(len(data[0]))]))
    else:
        return dict(zip(list(data[0]),
                        [list(i) for i in zip(*data[1:])]))


@app.route('/query/parcelByID', methods=['GET'])
@auth_required
def parcelByID_query():
    """
    Get a parcel information for a known parcel ID,
    """
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    ptype = ''
    withGeometry = True if request.args.get(
        'withGeometry') == 'True' else False
    wgs84 = True if request.args.get('wgs84') == 'True' else False
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelByID(dataset, pid, ptype, withGeometry, wgs84)

    if not data:
        return {}
    elif len(data) == 1:
        return dict(zip(list(data[0]),
                        [[] for i in range(len(data[0]))]))
    else:
        return dict(zip(list(data[0]),
                        [list(i) for i in zip(*data[1:])]))


@app.route('/query/parcelsByPolygon', methods=['GET'])
@auth_required
def parcelsByPolygon_query():
    """
    Find a parcel IDs within a given polygon.
    """
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    ptype = ''
    polygon = request.args.get('polygon')
    withGeometry = True if request.args.get(
        'withGeometry') == 'True' else False
    only_ids = True
    wgs84 = True if request.args.get('wgs84') == 'True' else False
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    if 'only_ids' in request.args.keys():
        only_ids = True if request.args.get(
            'only_ids') == 'True' else False
    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelsByPolygon(
        dataset, polygon, ptype, withGeometry, only_ids, wgs84)

    if not data:
        return {}
    elif len(data) == 1:
        return dict(zip(list(data[0]),
                        [[] for i in range(len(data[0]))]))
    else:
        return dict(zip(list(data[0]),
                        [list(i) for i in zip(*data[1:])]))


@app.route('/query/markers', methods=['GET'])
@auth_required
def markers():
    """
    Get a parcel information for a known parcel ID,
    """
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    ptype = ''
    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi').lower()
    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"
    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.markers(dataset, aoi, year, pid, ptype)
    if not data:
        return {}
    elif len(data) == 1:
        return dict(zip(list(data[0]),
                        [[] for i in range(len(data[0]))]))
    else:
        return dict(zip(list(data[0]),
                        [list(i) for i in zip(*data[1:])]))


# -------- Uploader ---------------------------------------------------------- #


@app.route('/files', methods=['GET', 'POST'])
@auth_required
def download_files():
    """
    List of files.
    """
    users_list = users.get_list(only_names=False, aois=True)
    aoi = users_list[user][0]
    aoi_files = file_manager.get_files_list(STORAGE, aoi)
    return render_template("files.html", files=aoi_files, aoi=aoi.upper())


@app.route(f'/{STORAGE}/<aoi>/<filename>')
@auth_required
def download_file(aoi, filename):
    if aoi == 'admin':
        return send_from_directory(f'{STORAGE}',
                                   filename, as_attachment=True)
    else:
        return send_from_directory(f'{STORAGE}/{aoi.upper()}',
                                   filename, as_attachment=True)


@app.route('/files/upload', methods=['GET', 'POST'])
@auth_required
def upload_file():
    """
    Upload file.
    """
    users_list = users.get_list(only_names=False, aois=True)
    aoi = users_list[user][0]

    if UPLOAD_ENABLE is True:  # Show upload page only if it is enabled.
        if request.method == 'POST':
            file_manager.upload(request, STORAGE, aoi)
        return render_template('upload.html')
    else:
        return ''


# ======== Main ============================================================== #
if __name__ == "__main__":
    app.run(debug=False, use_reloader=True, port=80, threaded=True)
