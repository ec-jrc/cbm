#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

"""Authentication with hashed user passwords."""

import os
import sys
import json
import hashlib
from codecs import encode

users_file = 'config/users.json'


def auth(username, password, aoi=None):
    """Authentication check with hashed passwords

    To be used in authentication decorator of flask app.

    Example:
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

        @app.route('/query/', methods=['GET'])
            @auth_required
            def query():
                return "DIAS API"

    Arguments:
        username, The user name (str)
        password, Tee user password (str)

    Return:
        True or False

    """
    try:
        users = get_list()
        user = users[username.lower()]

        salt = encode(user['salt'].encode().decode('unicode_escape'),
                      "raw_unicode_escape")

        key = encode(user['key'].encode().decode('unicode_escape'),
                     "raw_unicode_escape")

        new_key = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt, 100000)

        if key == new_key:
            if aoi:
                users = get_list(users_file)
                if aoi in users[username]['aois']:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    except Exception:
        return False


def data_auth(aoi, username):
    users = get_list(users_file)
    if aoi in users[username]['aois']:
        return True
    else:
        return False


def add(username, password='', aoi=''):
    """Create a new user

    Example:
        import users
        users.create('admin','admin')
    or in terminal:
        python users.py create username password

    Arguments:
        username, The user name (str)
        password, Tee user password (str)

    """
    users = get_list()

    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

    aois = aoi if type(aoi) is list else [aoi]

    users[username.lower()] = {
        'salt': str(salt)[2:-1],
        'key': str(key)[2:-1],
        'aois': aois
    }
    with open(users_file, 'w') as u:
        json.dump(users, u, indent=2)

    print(f"The user '{username}' was created.")


def get_list(file=users_file):
    """Get the list of active users

    Example:
        users.get_list('MyUserName')

    Return:
        A json object with the users

    """
    try:
        with open(file, 'r') as u:
            users = json.load(u)
        return [*users]
    except Exception:
        try:
            with open(file, 'w') as u:
                users = json.dumps({}, sort_keys=False, indent=2)
            return {}
        except Exception as err:
            return err


def delete(username):
    """Delete user from users_file file.

    Example:
        users.delete('MyUserName')

    Arguments:
        username, The user name to be deleted (str)

    """
    users = get_list()

    if username.lower() in users:
        del users[username.lower()]
        print(f"The user '{username}' is deleted.")
    else:
        print(f"Err: The user '{username}' was not found.")

    with open(users_file, 'w') as u:
        json.dump(users, u, indent=2)


if __name__ == '__main__':
    if sys.argv[1].lower() == 'add' or sys.argv[1].lower() == 'create':
        add(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1].lower() == 'delete':
        delete(sys.argv[2])
    elif sys.argv[1].lower() == 'list':
        for key in get_list():
            print(key)
    else:
        print("""Not recognized arguments. Available options:
    python users.py add username password  aoi # Create a new user.
    python users.py delete username            # Delete a user.
    python users.py list                       # Print a list of the users.
        """)
