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
from werkzeug.utils import secure_filename
from logging.handlers import TimedRotatingFileHandler
from flask import (Flask, request, send_from_directory, make_response,
                   render_template, flash, redirect, abort, url_for,
                   current_app)


from scripts import db_queries, image_requests, users, info_page


app = Flask(__name__)
app.secret_key = os.urandom(12)
app.config["MS_FILES"] = 'ms_files'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Enable upload page (http://HOST/upload).
UPLOAD_ENABLE = True  # True or False
DEBUG = False
DEFAULT_AOI = ''
datasets = db_queries.get_datasets()


try:
    import flask_monitoringdashboard as dashboard
    dashboard.bind(app)
    dashboard.config.init_from(file='dashboard.cfg')

except Exception:
    print("!ERROR! Can not start dashboard.")

# -------- Core functions ---------------------------------------------------- #

# Logging
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
    elif DEBUG is True:
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
    if DEBUG is True:
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


# Authentication decorator.
def auth_required(f):
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
                aoi = request.args.get('aoi')
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


swag = Swagger(app, decorators=[auth_required],
               template_file='static/swagger.yaml')


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(CustomJsonEncoder, self).default(obj)


def get_user_id():
    return user


dashboard.config.group_by = get_user_id


@app.route('/query/', methods=['GET'])
@auth_required
def query():
    return "DIAS API"


@app.route('/query/info', methods=['GET'])
@auth_required
def options():
    info_dict = info_page.generator(user)
    return current_app.response_class(json.dumps(info_dict, indent=4),
                                      mimetype="application/json")


@app.route('/dump/<unique_id>/<png_id>')
# @auth_required
def dump(unique_id, png_id):
    try:
        return send_from_directory(f"chip_extract/dump/{unique_id}", png_id)
    except FileNotFoundError:
        abort(404)


# -------- Queries - Background Images --------------------------------------- #

@app.route('/query/backgroundByLocation', methods=['GET'])
@auth_required
def backgroundByLocation_query():
    """
    Generate an extract from either Google or Bing.
    It uses the WMTS standard to grab and compose, which makes it fast
    (does not depend on DIAS S3 store).
    _
    tags:
      - backgroundByLocation
    responses:
      200:
        description: An HTML page that displays the selected chip as a PNG tile.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Start by getting the request IP address
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        rip = request.environ['REMOTE_ADDR']
    else:
        rip = request.environ['HTTP_X_FORWARDED_FOR']

    lon = request.args.get('lon')
    lat = request.args.get('lat')

    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    else:
        chipsize = '256'

    if 'extend' in request.args.keys():
        chipextend = request.args.get('extend')
    else:
        chipextend = '256'

    if 'tms' in request.args.keys():
        tms = request.args.get('tms')
    else:
        tms = 'Google'

    if 'iformat' in request.args.keys():
        iformat = request.args.get('iformat')
    else:
        iformat = 'png'

    unique_id = f"static/dump/{rip}E{lon}N{lat}_{chipsize}_{chipextend}_{tms}".replace(
        '.', '_')

    data = image_requests.getBackgroundByLocation(
        lon, lat, chipsize, chipextend, tms, unique_id, iformat, False)

    if data:
        if 'raw' in request.args.keys() or iformat == 'tif':
            with open('config/main.json') as f:
                configs = json.load(f)
            host = configs["server"]["host"]
            return f"{host}/{unique_id}/{tms.lower()}.{iformat}"
        else:
            flist = glob.glob(f"{unique_id}/{tms.lower()}.{iformat}")
            full_filename = url_for(
                'static', filename=flist[0].replace('static/', ''))
            return render_template("bg_page.html", bg_image=full_filename)
    else:
        return json.dumps({})


@app.route('/query/backgroundByParcelId', methods=['GET'])
@app.route('/query/backgroundByParcelID', methods=['GET'])
@auth_required
def backgroundByID_query():
    """
    Generate an extract from either Google or Bing.
    It uses the WMTS standard to grab and compose, which makes it fast
    (does not depend on DIAS S3 store).
    _
    tags:
      - backgroundByLocation
    responses:
      200:
        description: An HTML page that displays the selected chip as a PNG tile.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Start by getting the request IP address
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        rip = request.environ['REMOTE_ADDR']
    else:
        rip = request.environ['HTTP_X_FORWARDED_FOR']

    aoi = request.args.get('aoi')
    year = request.args.get('year')
    pid = request.args.get('pid')
    dataset = datasets[f'{aoi}_{year}']
    withGeometry = False
    ptype = ''

    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"

    lon, lat = db_queries.getParcelCentroid(dataset, pid, ptype)

    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    else:
        chipsize = '256'

    if 'extend' in request.args.keys():
        chipextend = request.args.get('extend')
    else:
        chipextend = '256'

    if 'tms' in request.args.keys():
        tms = request.args.get('tms')
    else:
        tms = 'Google'

    if 'iformat' in request.args.keys():
        iformat = request.args.get('iformat')
    else:
        iformat = 'png'

    if 'withGeometry' in request.args.keys():
        if request.args.get('withGeometry') == 'True':
            withGeometry = [aoi, year, pid, ptype]
        else:
            withGeometry = False

    unique_id = f"static/dump/{rip}E{lon}N{lat}_{chipsize}_{chipextend}_{tms}".replace(
        '.', '_')

    data = image_requests.getBackgroundByLocation(
        lon, lat, chipsize, chipextend, tms, unique_id, iformat, withGeometry)

    if data:
        if 'raw' in request.args.keys() or iformat == 'tif':
            return f"{unique_id}/{tms.lower()}.{iformat}"
        else:
            flist = glob.glob(f"{unique_id}/{tms.lower()}.{iformat}")
            full_filename = url_for(
                'static', filename=flist[0].replace('static/', ''))
            return render_template("bg_page.html", bg_image=full_filename)
    else:
        return json.dumps({})


# -------- Queries - Chip Images --------------------------------------------- #

@app.route('/query/chipsByLocation', methods=['GET'])
@auth_required
def chipsByLocation_query():
    """
    Get chips images by location.
    Generates a series of extracted Sentinel-2 LEVEL2A segments
    of 128x128 pixels as a composite of 3 bands.
    _
    tags:
      - chipsByLocation
    responses:
      200:
        description: An HTML page that displays the selected chips in a table
        with max. 8 columns.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Start by getting the request IP address
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        rip = request.environ['REMOTE_ADDR']
    else:
        rip = request.environ['HTTP_X_FORWARDED_FOR']

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

    unique_id = f"dump/{rip}E{lon}N{lat}L{lut}_{plevel}_{bands}".replace(
        '.', '_')

    data = image_requests.getChipsByLocation(
        lon, lat, start_date, end_date, unique_id, lut, bands, plevel)

    if data:
        return send_from_directory(f"chip_extract/{unique_id}", 'dump.html')
    else:
        return json.dumps({})


@app.route('/query/chipsByParcelID', methods=['GET'])
@auth_required
def chipsByParcelID_query():
    """
    Get chips images by parcel id.
    Generates a series of extracted Sentinel-2 LEVEL2A segments
    of 128x128 pixels as a composite of 3 bands.
    _
    tags:
      - chipsByParcelID
    responses:
      200:
        description: Returns a html with the images
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Start by getting the request IP address
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        rip = request.environ['REMOTE_ADDR']
    else:
        rip = request.environ['HTTP_X_FORWARDED_FOR']

    aoi = DEFAULT_AOI
    ptype = ''
    withGeometry = False
    wgs84 = False
    year = request.args.get('year')
    pid = request.args.get('pid')

    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"

    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi')

    dataset = datasets[f'{aoi}_{year}']
    pdata = db_queries.getParcelByID(dataset, pid, ptype, withGeometry, wgs84)
    if not pdata:
        parcel = json.dumps({})
    elif len(pdata) == 1:
        parcel = json.dumps(dict(zip(list(pdata[0]),
                                     [[] for i in range(len(pdata[0]))])))
    else:
        parcel = json.dumps(dict(zip(list(pdata[0]),
                                     [list(i) for i in zip(*pdata[1:])])))

    lon = str(json.loads(parcel)['clon'][0])
    lat = str(json.loads(parcel)['clat'][0])

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    band = request.args.get('band')

    if 'plevel' in request.args.keys():
        plevel = request.args.get('plevel')
    else:
        plevel = 'LEVEL2A'

    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    else:
        chipsize = '1280'

    unique_id = f"dump/{rip}E{lon}N{lat}_{plevel}_{chipsize}_{band}".replace(
        '.', '_')

    data = image_requests.getRawChipByLocation(
        lon, lat, start_date, end_date, unique_id, band, chipsize, plevel)

    if data:
        return send_from_directory(f"chip_extract/{unique_id}", 'dump.json')
    else:
        return json.dumps({})


@app.route('/query/rawChipByLocation', methods=['GET'])
@auth_required
def rawChipByLocation_query():
    """
    Get chips images by parcel location.
    Generates a series of extracted Sentinel-2 LEVEL2A segments of 128x128 (10m
    resolution bands) or 64x64 (20 m) pixels as list of full resolution GeoTIFFs
    _
    tags:
      - rawChipByLocation
    responses:
      200:
        description: A JSON dictionary with date labels and
        relative URLs to cached GeoTIFFs.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Start by getting the request IP address
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        rip = request.environ['REMOTE_ADDR']
    else:
        rip = request.environ['HTTP_X_FORWARDED_FOR']

    lon = request.args.get('lon')
    lat = request.args.get('lat')

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    band = request.args.get('band')

    if 'plevel' in request.args.keys():
        plevel = request.args.get('plevel')
    else:
        plevel = 'LEVEL2A'

    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    else:
        chipsize = '1280'

    unique_id = f"dump/{rip}E{lon}N{lat}_{plevel}_{chipsize}_{band}".replace(
        '.', '_')

    data = image_requests.getRawChipByLocation(
        lon, lat, start_date, end_date, unique_id, band, chipsize, plevel)

    if data:
        return send_from_directory(f"chip_extract/{unique_id}", 'dump.json')
    else:
        return json.dumps({})


@app.route('/query/rawChipByParcelID', methods=['GET'])
@auth_required
def rawChipByParcelID_query():
    """
    Get chips images by parcel ID.
    Generates a series of extracted Sentinel-2 LEVEL2A segments of 128x128 (10m
    resolution bands) or 64x64 (20 m) pixels as list of full resolution GeoTIFFs
    _
    tags:
      - rawChipByLocation
    responses:
      200:
        description: A JSON dictionary with date labels and
        relative URLs to cached GeoTIFFs.
    """
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Start by getting the request IP address
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        rip = request.environ['REMOTE_ADDR']
    else:
        rip = request.environ['HTTP_X_FORWARDED_FOR']

    aoi = DEFAULT_AOI
    ptype = ''
    withGeometry = False
    wgs84 = False
    year = request.args.get('year')
    pid = request.args.get('pid')

    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"

    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi')

    dataset = datasets[f'{aoi}_{year}']
    pdata = db_queries.getParcelByID(dataset, pid, ptype, withGeometry, wgs84)
    if not pdata:
        parcel = json.dumps({})
    elif len(pdata) == 1:
        parcel = json.dumps(dict(zip(list(pdata[0]),
                                     [[] for i in range(len(pdata[0]))])))
    else:
        parcel = json.dumps(dict(zip(list(pdata[0]),
                                     [list(i) for i in zip(*pdata[1:])])))

    lon = str(json.loads(parcel)['clon'][0])
    lat = str(json.loads(parcel)['clat'][0])

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    band = request.args.get('band')

    if 'plevel' in request.args.keys():
        plevel = request.args.get('plevel')
    else:
        plevel = 'LEVEL2A'

    if 'chipsize' in request.args.keys():
        chipsize = request.args.get('chipsize')
    else:
        chipsize = '1280'

    unique_id = f"dump/{rip}E{lon}N{lat}_{plevel}_{chipsize}_{band}".replace(
        '.', '_')

    data = image_requests.getRawChipByLocation(
        lon, lat, start_date, end_date, unique_id, band, chipsize, plevel)

    if data:
        return send_from_directory(f"chip_extract/{unique_id}", 'dump.json')
    else:
        return json.dumps({})


# -------- Queries - raw Chip Images Batch ----------------------------------- #

@app.route('/query/rawChipsBatch', methods=['POST'])
@auth_required
def rawChipsBatch_query():
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Start by getting the request IP address
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        rip = request.environ['REMOTE_ADDR']
    else:
        rip = request.environ['HTTP_X_FORWARDED_FOR']

    required = ["lon", "lat", "tiles", "bands", "chipsize"]

    if request.is_json:
        params = request.get_json()

        i = 0
        for k in params.keys():
            if k not in required:
                return json.dumps({"error": f"{k} not allowed as key"})
            else:
                i += 1
        if i != len(required):
            return json.dumps({"error": f"{i} parameters supplied, {len(required)} required"})

    unique_id = f"dump/{rip}_{params.get('lon')}_{params.get('lat')}_{params.get('chipsize')}_RAW".replace(
        '.', '_')
    logger.info(unique_id)

    if not os.path.exists(f"chip_extract/{unique_id}"):
        logger.info("Creating dir")
        os.makedirs(f"chip_extract/{unique_id}")

    with open(f"chip_extract/{unique_id}/params.json", "w") as sink:
        logger.info("Dumping params")
        sink.write(json.dumps(params))

    data = image_requests.getRawChipsBatch(unique_id)

    if data:
        return send_from_directory(f"chip_extract/{unique_id}", 'dump.json')
    else:
        return json.dumps({})


@app.route('/query/rawS1ChipsBatch', methods=['POST'])
@auth_required
def rawS1ChipsBatch_query():
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    # Start by getting the request IP address
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        rip = request.environ['REMOTE_ADDR']
    else:
        rip = request.environ['HTTP_X_FORWARDED_FOR']

    required = ["lon", "lat", "dates", "chipsize", "plevel"]

    if request.is_json:
        params = request.get_json()

        i = 0
        for k in params.keys():
            if k not in required:
                return json.dumps({"error": f"{k} not allowed as key"})
            else:
                i += 1
        if i != len(required):
            return json.dumps({"error": f"{i} parameters supplied, {len(required)} required"})

    unique_id = f"dump/{rip}_{params.get('lon')}_{params.get('lat')}_{params.get('chipsize')}_{params.get('plevel')}_RAW".replace('.', '_')
    logger.info(unique_id)

    if not os.path.exists(f"chip_extract/{unique_id}"):
        logger.info("Creating dir")
        os.makedirs(f"chip_extract/{unique_id}")

    with open(f"chip_extract/{unique_id}/params.json", "w") as sink:
        logger.info("Dumping params")
        sink.write(json.dumps(params))

    data = image_requests.getRawS1ChipsBatch(unique_id)

    if data:
        return send_from_directory(f"chip_extract/{unique_id}", 'dump.json')
    else:
        return json.dumps({})


# -------- Queries - Parcel Peers -------------------------------------------- #

@app.route('/query/parcelPeers', methods=['GET'])
@auth_required
def parcelPeers_query():
    """
    Get the parcel “peers” for a known parcel ID,
    _
    tags:
      - parcelPeers
    responses:
      200:
        description: The parcel “peers”.
    """
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    ptype = ''
    distance = 1000.0
    maxPeers = 10

    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"

    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi')

    if 'distance' in request.args.keys():
        distance = float(request.args.get('distance'))
    if 'max' in request.args.keys():
        maxPeers = int(request.args.get('max'))

    if distance > 5000.0:
        distance = 5000.0
    if maxPeers > 100:
        maxPeers = 100

    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelPeers(dataset, pid, distance, maxPeers, ptype)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]),
                                   [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]),
                                   [list(i) for i in zip(*data[1:])])))


# -------- Queries - Time Series --------------------------------------------- #

@app.route('/query/parcelTimeSeries', methods=['GET'])
@auth_required
def parcelTimeSeries_query():
    """
    Get the time series for a parcel ID.
    _
    tags:
      - parcelTimeSeries
    responses:
      200:
        description: Time series table.
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

    if 'scl' in request.args.keys():
        scl = True if request.args.get('scl') == 'True' else False

    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"

    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi')

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
            return json.dumps({})
        elif len(data) == 1:
            return json.dumps(dict(zip(list(data[0]),
                                       [[] for i in range(len(data[0]))])))
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
    _
    tags:
      - parcelByLocation
    responses:
      200:
        description: Parcel information.
    """
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    ptype = ''
    withGeometry = False
    wgs84 = False

    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"

    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi')

    if 'wgs84' in request.args.keys():
        wgs84 = True if request.args.get('wgs84') == 'True' else False

    if 'withGeometry' in request.args.keys():
        withGeometry = True if request.args.get(
            'withGeometry') == 'True' else False

    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelByLocation(dataset, lon, lat, ptype,
                                          withGeometry, wgs84)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]),
                                   [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]),
                                   [list(i) for i in zip(*data[1:])])))


@app.route('/query/parcelById', methods=['GET'])
@app.route('/query/parcelByID', methods=['GET'])
@auth_required
def parcelByID_query():
    """
    Get a parcel information for a known parcel ID,
    _
    tags:
      - parcelByID
    responses:
      200:
        description: Parcel information.
    """
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    pid = request.args.get('pid')
    ptype = ''
    withGeometry = False
    wgs84 = False

    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"

    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi')

    if 'wgs84' in request.args.keys():
        wgs84 = True if request.args.get('wgs84') == 'True' else False

    if 'withGeometry' in request.args.keys():
        withGeometry = True if request.args.get(
            'withGeometry') == 'True' else False

    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelByID(dataset, pid, ptype, withGeometry, wgs84)

    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]),
                                   [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]),
                                   [list(i) for i in zip(*data[1:])])))


@app.route('/query/parcelsByPolygon', methods=['GET'])
@auth_required
def parcelsByPolygon_query():
    """
    Find a parcel ID for within a given polygon.
    _
    tags:
      - parcelsByPolygon
    responses:
      200:
        description: List of parcels.
    """
    aoi = DEFAULT_AOI
    year = request.args.get('year')
    polygon = request.args.get('polygon')
    ptype = ''
    withGeometry = False
    only_ids = True
    wgs84 = False

    if 'ptype' in request.args.keys():
        if request.args.get('ptype') != '':
            ptype = f"_{request.args.get('ptype')}"

    if 'aoi' in request.args.keys():
        aoi = request.args.get('aoi')

    if 'withGeometry' in request.args.keys():
        withGeometry = True if request.args.get(
            'withGeometry') == 'True' else False

    if 'only_ids' in request.args.keys():
        only_ids = True if request.args.get(
            'only_ids') == 'True' else False

    if 'wgs84' in request.args.keys():
        wgs84 = True if request.args.get('wgs84') == 'True' else False

    dataset = datasets[f'{aoi}_{year}']
    data = db_queries.getParcelsByPolygon(
        dataset, polygon, ptype, withGeometry, only_ids, wgs84)

    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]),
                                   [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]),
                                   [list(i) for i in zip(*data[1:])])))


# -------- Uploader ---------------------------------------------------------- #


def allowed_file(filename):
    # Allow specific file types.
    return '.' in filename and \
           filename.split('.', 1)[1].lower() in ['zip', 'tar.gz']


@app.route('/files', methods=['GET', 'POST'])
@auth_required
def download_files():
    aoi = request.args.get('aoi')
    if aoi.lower() in [k.split('_')[0] for k in datasets]:
        aoi_files = glob.glob(f'{app.config["MS_FILES"]}/{aoi.upper()}/*')
    else:
        aoi_files = []
    return render_template("ms_files.html", files=aoi_files)


@app.route(f'/{app.config["MS_FILES"]}/<aoi>/<filename>')
@auth_required
def download_file(aoi, filename):
    return send_from_directory(f'{app.config["MS_FILES"]}/{aoi.upper()}',
                               filename, as_attachment=True)


@app.route('/upload', methods=['GET', 'POST'])
@auth_required
def upload_file():
    """
    Upload file.
    _
    tags:
      - upload
    """
    # Show upload page only if the uploader is enabled.
    if UPLOAD_ENABLE is True:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if not allowed_file(file.filename):
                flash('Not allowed file type selection')
                return render_template('not_allowed.html')
            if file.filename == '':
                flash('No selected file')
                return render_template('no_selection.html')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                flash('The file is uploaded.')
                return render_template('uploaded.html')
        return render_template('upload.html')
    else:
        return ''


# To download an uploaded file (http://0.0.0.0/uploads/FILENAME.zip).
@app.route('/uploads/<filename>')
@auth_required
def uploaded_file(filename):
    if UPLOAD_ENABLE is True:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ======== Main ============================================================== #
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True,
            host='0.0.0.0', port=80, threaded=True)
