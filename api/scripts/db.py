#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import json
import psycopg2

db_conf_file = 'config/main.json'


def crls(db='main'):
    try:
        with open(db_conf_file) as json_file:
            db_conf = json.load(json_file)
    except Exception:
        db_conf = create_db_config(db_conf_file)
    dbhost = db_conf['db'][db]['host']
    dbport = db_conf['db'][db]['port']
    dbname = db_conf['db'][db]['name']
    dbuser = db_conf['db'][db]['user']
    dbpass = db_conf['db'][db]['pass']
    return dbhost, dbport, dbname, dbuser, dbpass


def conn_str(db='main'):
    """Get the database connection string to connect the application to the
    database. You will need the database credentials for this to work (database
    server address, port, databese name, username and password)."""

    connection_string = ("host={} port={} dbname={} user={} password={}"
                         .format(*crls(db)))
    return connection_string


def conn(db='main'):
    """Create a new database session and return a new connection object."""
    try:
        conn = psycopg2.connect(conn_str(db))
        return conn
    except (Exception, psycopg2.Error) as err:
        print(f"Could not connect to the database {db}: {err}")
        return ''


def conn_cur(db='main'):
    """Create a cursor to execute PostgreSQL command in a database session"""
    try:
        conn = psycopg2.connect(conn_str(db))
        cur = conn.cursor()
        return cur
    except Exception:
        return ''


def db_connect(db='main'):
    try:
        conn = psycopg2.connect(conn_str(db))
        cur = conn.cursor()
        # db_par = conn.get_dsn_parameters()
        cur.execute("SELECT version();")
        # record = cur.fetchone()
        status = """! Connected to the database. !<br>"""
    except Exception:
        status = "! Unable to connect to the database. !"
    return status


def create_db_config():
    if not os.path.isfile(db_conf_file):
        db_conf = """{
    "db": {
        "main": {
            "desc": "Main db",
            "host": "0.0.0.0",
            "port": "5432",
            "sche": "public",
            "name": "postgres",
            "user": "postgres",
            "pass": ""
        }
    }
}"""
        with open(db_conf_file, 'w') as outfile:
            json.dump(json.loads(db_conf), outfile, indent=4)
        print("The db_conf.json file did not exist, a new file was created.")
        return json.loads(db_conf)


def check(db='main'):
    try:
        conn = psycopg2.connect(conn_str(db))
        conn.close()
        return True
    except Exception:
        return False
