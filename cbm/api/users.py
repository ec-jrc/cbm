#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

"""Authentication with hashed user passwords."""

from codecs import encode
import hashlib
import json
import os

users_file = '_users.json'

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
    
    from cbm.apicbm import users
    users.add('admin','admin')
    python3 -c "from cbm.apicbm import users; users.add('admin','admin')"
    """
    users = get_users()
    if users is None:
        users = {}

    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    users[username.lower()] = {
        'salt': str(salt)[2:-1],
        'key': str(key)[2:-1]
    }
    with open(users_file, 'w') as u:
        json.dump(users, u, indent=2)
    print(f"The user '{username}' was added.")


def get_users():
    """Get the list of active users"""
    try:
        with open(users_file, 'r') as u:
            users = json.load(u)
        return users
    except Exception:
        try:
            with open(users_file, 'w') as u:
                users = json.dumps({}, sort_keys=False, indent=2)
            return users
        except Exception as err:
            return err


def delete(username):
    """Delete user from users_file file.

    Example:
        config.delete('MyUserName')

    """
    users = get_users()

    for user in list(users):
        if user == username:
            del users[username]
            print(f"The user '{user}' is deleted.")

    with open(users_file, 'w') as u:
        json.dump(users, u, indent=2)
