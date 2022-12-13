#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2022 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import os
import glob
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (make_response, render_template, flash)


def allowed_file(filename):
    # Allow specific file types.
    return '.' in filename and \
           filename.split('.', 1)[1].lower() in ['zip', 'tar.gz', 'pdf']


def get_files_list(path, aoi):
    if aoi == 'admin':
        aoi_files = glob.glob(f'{path}/*/*')
    else:
        aoi_files = glob.glob(f'{path}/{aoi.upper()}/*')

    aoi_files_size_date = []
    for file in aoi_files:
        file_stats = os.stat(file)
        if file_stats.st_size < 100000:
            file_size = f"{round(file_stats.st_size / 1024, 2)} kB"
        else:
            file_size = f"{round(file_stats.st_size / (1024 * 1024), 2)} MB"
        try:
            file_date = datetime.fromtimestamp(file_stats.st_birthtime).date()
        except AttributeError:
            file_date = datetime.fromtimestamp(file_stats.st_mtime).date()
        if aoi == 'admin':
            file_name = file
        else:
            file_name = file.split('/')[-1]

        aoi_files_size_date.append([file, file_name, file_size, file_date])

    return aoi_files_size_date


def creation_date(path_to_file):
    stat = os.stat(path_to_file)
    try:
        return stat.st_birthtime
    except AttributeError:
        return stat.st_mtime


def upload(request, files, aoi):
    file = request.files['file']
    if not allowed_file(file.filename):
        flash('Not allowed file type selection')
        return render_template('not_allowed.html')
    if file.filename == '':
        flash('No selected file')
        return render_template('no_selection.html')
    if file and allowed_file(file.filename):
        file = request.files['file']

        save_path = os.path.join(files, aoi.upper(),
                                 secure_filename(file.filename))
        current_chunk = int(request.form['dzchunkindex'])

        # If the file already exists it's ok if we are appending to it,
        # but not if it's new file that would overwrite the existing one
        if os.path.exists(save_path) and current_chunk == 0:
            # 400 and 500s will tell dropzone that an error occurred
            # and show an error
            return make_response('File already exists', 400)

        try:
            with open(save_path, 'ab') as f:
                f.seek(int(request.form['dzchunkbyteoffset']))
                f.write(file.stream.read())
        except OSError as err:
            # log.exception will include the traceback so we can see
            # what's wrong
            print('Could not write to file', err)
            return make_response("Couldn't write the file to disk", 500)

        total_chunks = int(request.form['dztotalchunkcount'])

        if current_chunk + 1 == total_chunks:
            # This was the last chunk, the file should be complete and
            # the size we expect
            if os.path.getsize(save_path) != int(request.form['dztotalfilesize']):
                print(f"File {file.filename} was completed, ",
                      f"but has a size mismatch.",
                      f"Was {os.path.getsize(save_path)} but we",
                      f" expected {request.form['dztotalfilesize']} ")
                return make_response('Size mismatch', 500)
            else:
                print(f'File {file.filename} has been uploaded',
                      'successfully (total_chunks:{total_chunks})')
        # else:
        #     print(f'Chunk {current_chunk + 1} of {total_chunks} '
        #           f'for file {file.filename} complete')

        return make_response("Upload successful", 200)
