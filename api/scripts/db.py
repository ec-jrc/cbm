#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

"""
Project: Copernicus DIAS for CAP 'checks by monitoring'.
Functions:
  connection(db='main')
      - Create a new database session and return a new connection object.
  connection_cursor(db='main'):
      - Create a cursor to execute PostgreSQL command in a database session.
  information(db='main')
      - Get database connection information.
  get_version(dict_keys, var_name=None)
      - Get the database version .

Options:
  -h, --help    Show this screen.
  --version     Show version.
"""

import json
import psycopg2
import pandas as pd
# from cbm.utils import config

db_conf_file = 'config/main.json'


def conn_dict(db='main'):
    """Get the database connection string to connect to the database.
    The database credentials is needed for this (database server address,
    port, databese name, username and password)."""
    try:
        with open(db_conf_file) as json_file:
            configs = json.load(json_file)
    except Exception:
        configs = create_db_config(db_conf_file)
    return configs['db'][db]


def conn(db='main'):
    """Create a new database session and return a new connection object."""
    try:
        conn = psycopg2.connect(conn_dict(db))
        return conn
    except (Exception, psycopg2.Error) as err:
        print(f"! Unable to connect to the '{db}' database. !: {err}")
        return ''


def conn_cur(db='main'):
    """Create a cursor to execute PostgreSQL command in a database session"""
    try:
        conn = psycopg2.connect(conn_dict(db))
        cur = conn.cursor()
        return cur
    except Exception:
        return ''


def db_version(db='main'):
    try:
        conn = psycopg2.connect(conn_dict(db))
        cur = conn.cursor()
        # db_par = conn.get_dsn_parameters()
        ver = cur.execute("SELECT version();")
        # record = cur.fetchone()
        status = f"""! Connected to the database. !<br> Version {ver}"""
    except Exception:
        status = "! Unable to connect to the database. !"
    return status


def create_db_config():
    import json
    from os.path import isfile
    if not isfile(db_conf_file):
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
        conn = psycopg2.connect(conn_dict(db))
        conn.close()
        return True
    except Exception:
        return False


# ###### Geting informationand and data

def info(db='main'):
    """Get postgres database connection information."""
    try:
        conn = psycopg2.connect(conn_dict(db))
        cur = conn.cursor()
        print("\n--> PostgreSQL Connection properties for database: ", db)
        print(conn.get_dsn_parameters(), "\n")
        # Print PostgreSQL version
        cur.execute("SELECT version();")
        record = cur.fetchone()
        print(f"You are connected to (db{db}) - {record}\n")
    except Exception as err:
        print("Error while connecting to PostgreSQL: ", err)
        print("Be sure the credentials are correct and restart the notebook.")


def tables(db='main', schema='public'):
    """Get the database tables as a python list"""
    list_ = []
    try:
        conn = psycopg2.connect(conn_dict(db))
        cur = conn.cursor()
        allTablesSql = f"""
          SELECT table_name
          FROM information_schema.tables
          WHERE table_type='BASE TABLE'
          AND table_schema='{schema}'
          ORDER BY table_name ASC;
        """
        # Execute the query
        cur.execute(allTablesSql)
        for row in cur:
            list_.append(row[0])
        return list_
    except Exception:
        return []


def table_data(table, where, db='main'):
    """Get the rows from a table with a limit 1000"""
    conn = psycopg2.connect(conn_dict(db))
    try:
        getTableDataSql = f"""
          SELECT * FROM {table}
          WHERE
          LIMIT 1000;
        """
        df_data = pd.read_sql_query(getTableDataSql, conn)
    except Exception:
        print("Did not found data, please select the right database and table")
        df_data = pd.DataFrame(columns=['name'])
    return df_data


def table_columns(table, db='main'):
    """Get a list of the columns from a table."""
    conn = psycopg2.connect(conn_dict(db))
    try:
        getTableColumns = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table}';
            """
        df_columns = pd.read_sql_query(getTableColumns, conn)
        columns_list = df_columns['column_name'].tolist()
    except Exception:
        print("Did not find any columns...")
        df_columns = pd.DataFrame(columns=['column_name'])
    return columns_list


def close_conn(close_1='', close_2=''):
    """Close the database connection"""
    try:
        conn.conn.close()
        print("The connection to the database is now closed.")
    except Exception:
        pass


def insert_function(func, db='main'):
    """
    Insert functions to database.
    Args:
    func: Sql text to add a new function to the database.
        type: srt
    db: Database configurarion
    """
    import psycopg2.extras
    import psycopg2.extensions
    conn = psycopg2.connect(conn_dict(db))
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Execute function.
    cur.execute(func)


def exact_count(table, db='main'):
    """Return the exact count of rown of the given table"""
    conn = psycopg2.connect(conn_dict(db))
    cur = conn.cursor()
    getExactCount = f"""
        SELECT count(*) AS exact_count
        FROM {table};"""

    cur.execute(getExactCount)
    return cur.fetchall()[0][0]


def execute_query(query, db='main'):
    """Return query"""
    conn = psycopg2.connect(conn_dict(db))
    cur = conn.cursor()
    cur.execute(query)
    data = cur.fetchall()
    conn.close()
    cur.close()
    return data


def execute_sql(sql, db='main'):
    """Execute sql"""
    try:
        conn = psycopg2.connect(conn_dict(db))
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()  # <--- makes sure the change is shown in the database
        conn.close()
        cur.close()
        return 0
    except Exception as err:
        return err


def tb_extent(table, db='main'):
    """Get the extent of the table"""
    data = []
    try:
        conn = psycopg2.connect(conn_dict(db))
        cur = conn.cursor()
        sql = f"""
        SELECT ST_AsText(ST_SetSRID(ST_Extent(st_transform(wkb_geometry, 4326)),
            4326)) As bextent
        FROM {table};"""
        cur.execute(sql)
        for row in cur:
            data.append(row)
        conn.commit()  # <--- makes sure the change is shown in the database
        conn.close()
        cur.close()
        data = data[0][0].replace(' ', '+')
        return data.replace('POLYGON((', '').replace('))', '')
    except Exception as err:
        return err


def tb_exist(table, db='main'):
    """Check if table exist"""
    tbExistSql = f"""
        SELECT * FROM information_schema.tables
        WHERE table_name = '{table}';
    """
    conn = psycopg2.connect(conn_dict(db))
    cur = conn.cursor()
    cur.execute(tbExistSql)
    exist = bool(cur.rowcount)
    conn.close()
    cur.close()
    return exist


def get_schemas(table, where, db='main'):
    """Get the rows from a table with a limit 1000"""
    conn = psycopg2.connect(conn_dict(db))
    getSchemasSql = f"""
        SELECT schema_name
        FROM information_schema.schemata;
    """
    df_data = pd.read_sql_query(getSchemasSql, conn)
    return df_data
