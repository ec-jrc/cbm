#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Version   : 


import boto3
import botocore
import json


def getFileFromS3(s3file, localfile, bucket=None):
    with open('s3_config.json', 'r') as f:
        config = json.load(f)

    session = boto3.session.Session(
        aws_access_key_id=config['s3']['access_key'],
        aws_secret_access_key=config['s3']['secret_key'])
    s3 = session.resource('s3', endpoint_url=config['s3']['host'])
    if not bucket:
        bucket = config['s3']['bucket']

    # print(s3file)
    # print(localfile)
    try:
        s3.Bucket(bucket).download_file(s3file, localfile)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # print("The object does not exist.")
            return 0
        else:
            raise

    return 1


def listFileFromS3(prefix, bucket=None):
    with open('s3_config.json', 'r') as f:
        config = json.load(f)

    session = boto3.session.Session(
        aws_access_key_id=config['s3']['access_key'],
        aws_secret_access_key=config['s3']['secret_key'])
    if not bucket:
        bucket = config['s3']['bucket']

    s3 = session.resource('s3', endpoint_url=config['s3']['host'])
    bucket = s3.Bucket(bucket)

    keys = []
    for o in bucket.objects.filter(Prefix=prefix):
        keys.append(o.key)

    return keys