#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Guido Lemoine, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

"""Authentication with hashed user passwords."""

from codecs import encode
import hashlib
import json
import os


def auth(username, password):
    """Authentication check with hashed passwords"""
    try:
        users = get_users()
        user = users[username.lower()]

        salt = encode(user['salt'].encode().decode('unicode_escape'),
                      "raw_unicode_escape")

        key = encode(user['key'].encode().decode('unicode_escape'),
                     "raw_unicode_escape")

        new_key = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt, 100000)

        if key == new_key:
            return True
        else:
            return False

    except Exception:
        return False


def add(username, password=''):
    """Add a new user
    
    from src.apicbm import users
    users.add('admin','admin')
    python3 -c "from src.apicbm import users; users.add('admin','admin')"
    """
    users = get_users()
    if users is None:
        users = {}

    salt = os.urandom(32)

    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    users[username] = {
        'salt': str(salt)[2:-1],
        'key': str(key)[2:-1]
    }
    with open('_users.json', 'w') as users_file:
        json.dump(users, users_file, indent=2)
    print(f"The user '{username}' was added.")


def get_users():
    """Get the list of active users"""
    try:
        with open('_users.json', 'r') as users_file:
            users = json.load(users_file)
#         print(f"Users list: {users.keys()}")
        return users
    except Exception:
        try:
            with open('_users.json', 'w') as users_file:
                users = json.dumps({}, sort_keys=False, indent=2)
        except Exception as err:
            return err