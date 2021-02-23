#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from functools import wraps
from werkzeug.utils import secure_filename
from flask import (Flask, request, send_from_directory, make_response,
                   render_template, flash, redirect)


import query_handler as qh
import users

app = Flask(__name__)
app.secret_key = os.urandom(12)

# Enable uplaod page.
UPLOAD_ENABLE = False  # True or False


# -------- Core functions ---------------------------------------------------- #

# Authentication decorator.
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and users.auth(auth.username, auth.password) is True:
            return f(*args, **kwargs)
        return make_response('Could not verify.', 401,
                             {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(CustomJsonEncoder, self).default(obj)


# -------- Queries ----------------------------------------------------------- #

@app.route('/query/', methods=['GET'])
@auth_required
def query():
    return "DIAS API"


@app.route('/query/options', methods=['GET'])
@auth_required
def options():
    try:
        with open('api_options.json', 'r') as f:
            api_options = json.load(f)
        return make_response(jsonify(api_options), 200)
    except Exception as err:
        return str(err)


@app.route('/query/parcelTimeSeries', methods=['GET'])
@auth_required
def parcelTimeSeries_query():
    aoi = request.args.get('aoi')
    year = request.args.get('year')
    parcelid = request.args.get('pid')
    tstype = request.args.get('tstype')
    band = None

    if 'band' in request.args.keys():
        band = request.args.get('band')
    data = qh.getParcelTimeSeries(aoi, year, parcelid, tstype, band)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]),
                                   [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]),
                                   [list(i) for i in zip(*data[1:])])),
                          cls=CustomJsonEncoder)


@app.route('/query/parcelPeers', methods=['GET'])
@auth_required
def parcelPeers_query():
    parcelTable = request.args.get('parcels')
    pid = request.args.get('pid')
    distance = 1000.0
    maxPeers = 10
    if 'distance' in request.args.keys():
        distance = float(request.args.get('distance'))
    if 'max' in request.args.keys():
        maxPeers = int(request.args.get('max'))

    if distance > 5000.0:
        distance = 5000.0
    if maxPeers > 100:
        maxPeers = 100

    data = qh.getParcelPeers(parcelTable, pid, distance, maxPeers)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]),
                                   [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]),
                                   [list(i) for i in zip(*data[1:])])))


@app.route('/query/parcelByLocation', methods=['GET'])
@auth_required
def parcelByLocation_query():
    parcelTable = request.args.get('parcels')
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    withGeometry = False

    if 'withGeometry' in request.args.keys():
        withGeometry = True if request.args.get(
            'withGeometry') == 'True' else False
    data = qh.getParcelByLocation(parcelTable, lon, lat, withGeometry)
    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]),
                                   [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]),
                                   [list(i) for i in zip(*data[1:])])))


@app.route('/query/parcelById', methods=['GET'])
@auth_required
def parcelById_query():
    parcelTable = request.args.get('parcels')
    withGeometry = False

    if 'withGeometry' in request.args.keys():
        withGeometry = True if request.args.get(
            'withGeometry') == 'True' else False

    parcelid = request.args.get('parcelid')
    data = qh.getParcelById(parcelTable, parcelid, withGeometry)

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
    parcelTable = request.args.get('parcels')
    withGeometry = False
    only_ids = True

    if 'withGeometry' in request.args.keys():
        withGeometry = True if request.args.get(
            'withGeometry') == 'True' else False

    if 'only_ids' in request.args.keys():
        only_ids = True if request.args.get(
            'only_ids') == 'True' else False

    polygon = request.args.get('polygon')
    data = qh.getParcelsByPolygon(parcelTable, polygon, withGeometry, only_ids)

    if not data:
        return json.dumps({})
    elif len(data) == 1:
        return json.dumps(dict(zip(list(data[0]),
                                   [[] for i in range(len(data[0]))])))
    else:
        return json.dumps(dict(zip(list(data[0]),
                                   [list(i) for i in zip(*data[1:])])))


# -------- Uploader ---------------------------------------------------------- #

app.config['UPLOAD_FOLDER'] = 'uploads'


def allowed_file(filename):
    # Allow specific file types.
    return '.' in filename and \
           filename.split('.', 1)[1].lower() in ['zip', 'tar.gz']


@app.route('/upload', methods=['GET', 'POST'])
@auth_required
def upload_file():
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
        return send_from_directory(app.config['UPLOAD_FOLDER'],
                                   filename)


# ======== Main ============================================================== #
if __name__ == "__main__":
    logname = 'logs/app.log'
    handler = TimedRotatingFileHandler(logname, when='midnight', interval=1)
    handler.suffix = '%Y%m%d'
    logger = logging.getLogger('tdm')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    app.run(debug=True, use_reloader=True,
            host='0.0.0.0', port=5000, threaded=True)
