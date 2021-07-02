#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


"""
Project: Copernicus DIAS for CAP 'checks by monitoring'.

Access DIAS object storage with boto3
Options:
    -h, --help    Show this screen.
    --version     Show version.

Exaple code:
    from cbm.datas import object_storage
    s3file = ''  # The file from the s3 storage # noqa
    localfile = ''  # The new name of the file on the local storage. Use only if 'to_memory' is False
    progress_bar = True  # Disable or enable the progress bar, accepts True or False (Default False).
    to_memory = True  # Download directly to memory or to a file on local storage (Default False).
    object_storage.get_file(s3file, localfile, to_memory, progress_bar)  # Download the file from 3s storage
    object_storage.listFileFromS3('card')  # List of the files in the 3s bucket
"""

import boto3
from cbm.utils import config


class crls:
    """
    """
    try:
        values = config.read()
        ACCESS_KEY = values['s3']['access_key']
        SECRET_KEY = values['s3']['secret_key']
        S3HOST = values['s3']['host']
        BUCKET = values['s3']['bucket']
        SERVICE_PROVIDER = values['s3']['dias']
    except Exception as err:
        print(f"Could not read config file: {err}")


def connection(arg=None):
    session = boto3.session.Session(aws_access_key_id=crls.ACCESS_KEY,
                                    aws_secret_access_key=crls.SECRET_KEY)
    if arg == 'session':
        return session
    elif arg == 'resource':
        return session.resource('s3', endpoint_url=crls.S3HOST)
    else:
        return session.client('s3', endpoint_url=crls.S3HOST)


def get_file(s3file, localfile, bucket_, progress_bar=False, to_memory=False, status=False):
    import botocore
    """Download a file from the s3 storage"""
    session = boto3.session.Session(aws_access_key_id=crls.ACCESS_KEY,
                                    aws_secret_access_key=crls.SECRET_KEY)
    s3 = session.resource('s3', endpoint_url=crls.S3HOST)
    bucket_ = s3.Bucket(crls.BUCKET)
    object_ = bucket_.Object(s3file)
    filesize = object_.content_length

    try:
        if to_memory is True:
            import io
#             localfile = io.BytesIO()
            print("-Downloading to memory-")
            if progress_bar is True:
                if isnotebook() is True:
                    from tqdm import tqdm_notebook as tqdm  # For Jupyter Notebook
                    with tqdm(total=filesize, unit='B', unit_scale=True, desc=None) as t:
                        object_.download_fileobj(localfile, Callback=hook(t))
                        print("File downloaded in memory adress: ", localfile)
                else:
                    from tqdm import tqdm  # For comadline
                    with tqdm(total=filesize, unit='B', unit_scale=True, desc=None) as t:
                        object_.download_fileobj(localfile, Callback=hook(t))
                        print("File downloaded in memory adress: ", localfile)
            else:
                object_.download_fileobj(localfile)
                print("File downloaded in memory adress: ", localfile)
                return 1
        else:
            #             print("-Downloading to local file-")
            if progress_bar is True:
                if isnotebook() is True:
                    from tqdm import tqdm_notebook as tqdm  # For Jupyter Notebook
                    with tqdm(total=filesize, unit='B', unit_scale=True, desc=None) as t:
                        bucket_.download_file(
                            s3file, localfile, Callback=hook(t))
                        print("File downloaded as: ", localfile)
                else:
                    from tqdm import tqdm  # For comadline
                    with tqdm(total=filesize, unit='B', unit_scale=True, desc=None) as t:
                        bucket_.download_file(
                            s3file, localfile, Callback=hook(t))
                        print("File downloaded as: ", localfile)
            else:
                bucket_.download_file(s3file, localfile)
                if status:
                    print("File downloaded as: ", localfile)
                return 1
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return 0
        else:
            raise


def list_files(prefix=None, print_list=False):
    """Displays the contents of a single bucket"""
    try:
        if crls.BUCKET == '':
            print("!Warning! The bucket name is set to 'None', Please enter a default")
            print("'bucket_name' in the configuration file (config/config.json)")
        s3 = connection()
        if prefix is None:
            prefix = ''
        bucket_files = s3.list_objects_v2(
            Bucket=crls.BUCKET, Prefix=prefix)['Contents']
        if print_list is True:
            for key in bucket_files:
                print(key)
        else:
            return bucket_files
    except Exception as err:
        print(
            f"Could not retrieve list of the files from the selected buckets: {err}")


def list_buckets(print_list=False):
    """Retrieve a list of existing buckets in the object storage"""
    try:
        s3 = connection()

        buckets = s3.list_buckets()
        bucket_list = []
        if crls.BUCKET != '':
            bucket_list.append(crls.BUCKET)
        for bucket_ in buckets['Buckets']:
            bucket_list.append(bucket_['Name'])
        if print_list is True:
            for b_ in bucket_list:
                print(b_)
        else:
            return bucket_list
    except Exception as err:
        print(f"Could not retrieve list of the buckets: {err}")


def hook(t):
    """Calculate the progress from download callbacks (For progress bar)"""
    def inner(bytes_amount):
        t.update(bytes_amount)  # Update progress bar
    return inner


def isnotebook():
    """Test on which platform the script is running (For progress bar)"""
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True  # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter


def get_file_location(reference, dias=None, quiet=True):
    """Get the files path in the object storage. Each dias provider have
    different configurations. Depending on the provider the relative
    options will be selected.

    -Options-    -Type- -Description-
    reference : Str
        The reference from the dias catalog database.

    dias : Str
        The name of dias service provider.

    help_text : boolean
        Display or not the attributes of the files.

    example of a file path in the object storage:
    --SOBLOO--
    S2B/L1C/ S2B_MSIL1C_20170610T105029_N0205_R051_T31UET_20170610T105026/
    S2B_MSIL2A_20170610T105029_N0205_R051_T31UET_20170610T105026.SAFE/
    GRANULE/ L2A_T31UET_A001364_20170610T105026/ IMG_DATA/R20m/
    L2A_T31UET_20170610T105029_B07_20m.jp2

    --CREODIAS--
    Sentinel-2/MSI/L2A/2019/08/07/S2A_MSIL2A_20190807T073621_N0213_R092_
    T38SND_20190807T102313.SAFE/GRANULE/L2A_T38SND_A021539_20190807T074416/
    IMG_DATA/R10m/T38SND_20190807T073621_B08_10m.jp2

    Sentinel-1/SAR/CARD-BS/2018/08/21/S1A_IW_GRDH_1SDV_20180821T052345_
    20180821T052410_023340_0289E6_6558_CARD_BS/S1A_IW_GRDH_1SDV_20180821T052345_
    20180821T052410_023340_0289E6_6558_CARD_BS.data/Gamma0_VH.hdr

    --MUNDI--
    25/S/FA/2018/05/24/S2A_MSIL2A_20180524T125041_N0208_R095_T25SFA_
    20180524T190423/    GRANULE/L2A_T25SFA_A015250_20180524T125143/IMG_DATA/
    R10m/T25SFA_20180524T125041_B02_10m.jp2

    """

    if dias is None:
        dias = crls.SERVICE_PROVIDER
        if crls.SERVICE_PROVIDER == '':
            print("The Copernicus dias provider is not set. Please run the",
                  "'Configuration' notebook to set the name of the provider.")

    ref_list = reference.split('_')  # Split the reference to properties list.
    sat = ref_list[0]  # Set the satellite s1 or s2
    if sat[:2] == 'S1':
        obstime = ref_list[4][0:8]  # Set the observation time
        obspath = "{}/{}/{}".format(obstime[0:4], obstime[4:6], obstime[6:8])
        mgrs_tile = ref_list[2]
        full_tstamp = ref_list[5]
    elif sat[:2] == 'S2':
        obstime = ref_list[2][0:8]  # Set the observation time
        obspath = "{}/{}/{}".format(obstime[0:4], obstime[4:6], obstime[6:8])
        mgrs_tile = reference.split('_')[5]
        full_tstamp = reference.split('_')[2]

    # set local files directory.
    fpath = f"{config.folder_repo}/tmp/{sat}_{full_tstamp}/"
    info_dict = {"fpath": fpath, "sat": sat, "obstime": obstime,
                 "obspath": obspath, "mgrs_tile": mgrs_tile,
                 "full_tstamp": full_tstamp}

    if quiet is False:
        print("Satellite: ", sat)
        print('Observation time: ', obstime)
        print('Observation path: ', obspath)
        print('mgrs tile: ', mgrs_tile)
        print('Full time stamp: ', full_tstamp)

    # -- SOBLOO --
    if dias.lower() == 'sobloo':

        # Set the default root path depending of the satellite.
        if sat[:2] == 'S2':
            rootpath = sat + '/L1C'
        elif sat[:2] == 'S1':
            rootpath = sat + '/GRD'
        else:
            rootpath = ''
            s3path.replace('MSIL1C', 'MSIL2A', -1)
        # Path of the files on the object storage.
        s3path = f"{rootpath}/{reference}/{ref_list[0]}_MSIL2A_\
{ref_list[2]}_{ref_list[3]}_{ref_list[4]}_{ref_list[5]}_{ref_list[6]}.\
SAFE/GRANULE/L2A_{ref_list[5]}_"
#         return s3path.replace('MSIL1C', 'MSIL2A',-1), info_dict
        return s3path, info_dict

    # -- ONDA --
    elif dias.lower() == 'onda':
        print('ONDA is not supported yet.')

    # -- MUNDI --
    elif dias.lower() == 'mundi':
        import pandas as pd
        from datetime import datetime
        s3path = f"{mgrs_path} / {datetime.strftime(obstime, '%Y/%m/%d')} / {reference} / manifest.safe/"
        q = pd.Timestamp(obstime).quarter
        bucket_path = "s2-l2a-2018-q{}".format(pd.Timestamp(obstime).quarter)
        if get_files(bucket_path, s3path, fpath) == 1:
            print("Resource found in bucket {}".format(bucket_path))
        elif get_files('s2-l2a', s3path, fpath) == 1:
            print("Resource found in bucket {}".format('s2-l2a'))
            bucket_path = 's2-l2a'
        info_dict['bucket'] = bucket_path

        location_code = reference.split('_')[5]
        utm = location_code[1:3]
        latitude_band = location_code[3]
        square = location_code[4:]
        s3path = f'{utm}/{latitude_band}/{square}/{obspath}/{reference.replace(".SAFE","")}/GRANULE/'

        parsed_date = datetime.strptime(str(obstime), '%Y%m%d')
        timestamp = pd.Timestamp(parsed_date)
        bucket_path = f's2-l2a-{timestamp.year}-q{timestamp.quarter}'

        return s3path, info_dict

    # -- CREODIAS --
    elif dias.lower() == 'creodias' or dias.lower() == 'eosc':
        if sat == 'S1A' or sat == 'S1B':
            rootpath = 'Sentinel-1/SAR/CARD-BS'
            s3path = f"{rootpath}/{obspath}/{reference}/"
        elif sat == 'S2A' or sat == 'S2B':
            rootpath = 'Sentinel-2/MSI/L2A'
            s3path = f"{rootpath}/{obspath}/{reference}/GRANULE/"
        else:
            rootpath = ''
            s3path = ''
        return s3path, info_dict

    elif dias.lower() == 'wekeo':
        print('WEKEO is not supported yet.')
    # No provider
    else:
        print("The selected service provider is not in the configuration list.")

# Configure S3 access (-> to config loading)


def get_subset(fkey, features):
    import numpy as np
#     import pandas as pd
    import rasterio
    from rasterio.mask import mask
    from rasterio.session import AWSSession
    s3host_ = crls.S3HOST.replace('http://', '')
    s3host_ = s3host_.replace('https://', '')

    session = connection('session')
    with rasterio.Env(AWSSession(session), AWS_S3_ENDPOINT=s3host_,
                      AWS_HTTPS='NO', AWS_VIRTUAL_HOSTING=False) as env:
        with rasterio.open('/vsis3/{}/{}'.format(crls.BUCKET, fkey)) as src:
            out_image, out_transform = mask(src, features, crop=True,
                                            pad=False, all_touched=False)
#             print('--out_image.shape: ', out_image.shape)
            w_5 = np.percentile(out_image, 5.0)
            w_95 = np.percentile(out_image, 95.0)
#             print('--w_5, w_95: ', w_5, w_95)
            chip_set = np.clip(255 * (out_image - w_5) / (w_95 - w_5),
                               0, 255).astype(np.uint16)
    return chip_set, out_transform
