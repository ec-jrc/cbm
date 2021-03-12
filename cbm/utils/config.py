#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import os
import time
import json
import uuid
from os.path import dirname, abspath, join, normpath, exists, isfile

path_work = abspath(os.curdir)
path_repo = dirname(dirname(abspath(__file__)))
path_conf = 'config'
conf_main = 'main.json'
path_default = normpath(join(dirname(abspath(__file__)), 'default'))


def get_value(dict_keys={}, file=conf_main, var_name=None, help_text=True):
    """Get value from a configuration file, with an arbitrary length key.

    Examples:
        config.get_value(['information', 'aoi'])

        To display the variable name and and some information use:
        config.get_value(['information', 'aoi'], 'AOI' config.conf_main, False)

    Arguments:
        dict_keys, list of keys to add
        _dict, dict to update. Default is {}

    Return:
        The value of the given keys.
        If help text is enabled and a variable name is given, will print:
            'The value for 'AOI' is: 'MyAOI'.'
    """

    config_dict = read(file)
    try:
        if len(dict_keys) == 1:
            value = config_dict.get(dict_keys[0])
        else:
            dict_keys = [s.strip() for s in dict_keys]
            for key in dict_keys[:-1]:
                if '_x' not in locals():
                    if key not in config_dict:
                        config_dict[key] = {}
                    _x = config_dict.get(key)
                else:
                    if key not in _x:
                        _x[key] = {}
                    _x = _x.get(key)
            value = _x[dict_keys[-1]]
        if var_name is not None and help_text is True:
            if value != '':
                print(f"The value for '{var_name}' is: '{value}'.")
            else:
                print(f"!WARNING! The value for '{var_name}' is: '{value}'.")
        return value
    except Exception as err:
        print(f"Could not get value from file '{file}': {err}")
        return ''


def set_value(dict_keys={}, val=None, file=conf_main):
    """Update configuration file, with an arbitrary length key.

    Example:
        config.set_value(['information', 'aoi'], 'test')

    Arguments:
        dict_keys, list of keys to add
        _dict, dict to update. Default is {}
        val, any legal value to a key. Default is None.

    """
    config_dict = read(file)
    try:
        dict_keys = [s.strip() for s in dict_keys]
        for key in dict_keys[:-1]:
            if '_x' not in locals():
                if key not in config_dict:
                    config_dict[key] = {}
                _x = config_dict.get(key)
            else:
                if key not in _x:
                    _x[key] = {}
                _x = _x.get(key)
        _x[dict_keys[-1]] = val
        # create randomly named temporary file to avoid
        # interference with other thread/asynchronous request
        tempfile = normpath(join(path_conf, str(uuid.uuid4())))
        with open(tempfile, 'w') as f:
            json.dump(config_dict, f, indent=4)

        # rename temporary file replacing old file
        try:
            os.rename(tempfile, normpath(join(path_conf, file)))
        except WindowsError:
            os.remove(normpath(join(path_conf, file)))
            os.rename(tempfile, normpath(join(path_conf, file)))
    except Exception as err:
        print(f"Could not update key in the file '{file}': {err}")


def delete(dict_keys={}, file=conf_main):
    """Delete keys from the configuration file.

    Example:
        config.delete(['information', 'aoi'])

    Arguments:
        dict_keys, list of keys to add
        _dict, dict to update. Default is {}

    """
    try:
        config_dict = read(file)
        dict_keys = [s.strip() for s in dict_keys]
        for key in dict_keys[:-1]:
            if '_x' not in locals():
                if key not in config_dict:
                    config_dict[key] = {}
                _x = config_dict.get(key)
            else:
                if key not in _x:
                    _x[key] = {}
                _x = _x.get(key)
        del _x[dict_keys[-1]]

        tempfile = normpath(join(path_conf, str(uuid.uuid4())))
        with open(tempfile, 'w') as f:
            json.dump(config_dict, f, indent=4)

        # rename temporary file replacing old file
        try:
            os.rename(tempfile, normpath(join(path_conf, file)))
        except WindowsError:
            os.remove(normpath(join(path_conf, file)))
            os.rename(tempfile, normpath(join(path_conf, file)))
    except Exception as err:
        print(f"Could not delete key in the file '{file}': {err}")


def read(file=conf_main):
    """Read configuration file
    Example:
        config.read("main.json")

    Arguments:
        file (str): the name of the configuration file

    Returns:
        data - A python dict of the selected file.

    """
    try:
        with open(normpath(join(path_conf, file)), 'r') as f:
            data = json.load(f)
            return data
    except Exception:
        create(file)
        with open(normpath(join(path_conf, file)), 'r') as f:
            data = json.load(f)
        return data


def create(to_file=conf_main, from_=path_default):
    """Automatically create a config file if it does not exist.
    """
    if not exists(normpath(join(path_work, path_conf))):
        os.makedirs(normpath(join(path_work, path_conf)))
    # if file does not exist, create it
    if isfile(normpath(join(path_conf, to_file))) is False:
        # Read from default configuration file
        from_file = normpath(join(from_, to_file))
        with open(from_file, 'r') as f:
            dict_default = json.load(f)
        # Create a new config file
        with open(normpath(join(path_work, path_conf, to_file)), 'w') as f:
            json.dump(dict_default, f, indent=4)
        time.sleep(0.5)  # Sleep for half second to run the function.
        print(f"The file 'config/{to_file}' did not exist, a new default ",
              " file was created.")


def update_keys(from_=path_default, to_file=conf_main):
    """Update missing keys of old configuration files."""
    if isfile(normpath(join(path_conf, to_file))) is False:
        create(to_file, from_)

    with open(normpath(join(from_, to_file)), 'r') as f:
        dict_new = json.load(f)

    with open(normpath(join(path_conf, to_file)), 'r') as f:
        dict_old = json.load(f)

    updated_keys = 0
    for key in dict_new.keys():
        if key not in dict_old:
            dict_old[key] = dict_new[key]
            updated_keys += 1
        for k in dict_new[key].keys():
            if k not in dict_old[key]:
                dict_old[key][k] = dict_new[key][k]
                updated_keys += 1

    # create randomly named temporary file to avoid
    # interference with other thread/asynchronous request
    tempfile = normpath(join(path_conf, str(uuid.uuid4())))
    with open(tempfile, 'w') as f:
        json.dump(dict_old, f, indent=4)

    # rename temporary file replacing old file
    try:
        os.rename(tempfile, normpath(join(path_conf, to_file)))
    except WindowsError:
        os.remove(normpath(join(path_conf, to_file)))
        os.rename(tempfile, normpath(join(path_conf, to_file)))

    if updated_keys > 0:
        print(f"{updated_keys+1} new json configuration",
              "objects are added to the configuration file.")


def credentials(service):
    try:
        url = get_value([service, 'url'])
        user = get_value([service, 'user'])
        pass_ = get_value([service, 'pass'])
    except Exception as err:
        print(f"Could not get credentials for '{service}'. {err}")
        url, user, pass_ = ''

    return url, user, pass_


def autoselect(match_text=None, import_list=[], help_text=True):
    """Automatically select the first object that the 'match_text' is included
    in its name. If no object has this word no object will be automatically
    selected. If 'help_text' value is False no output help text for the founded
    tables will be returned in case there are more entries in the list with the
    matching text.

    Arguments:
        match_text :  The desired text selection (str).

        import_list :  List of the options (List).

        help_text :  Display or not all the tables if more then one (Boolean).

    Returns:
        The selected value that match the input

    """
    value = ''
    try:
        if import_list is None:
            value = None
        elif match_text in import_list:
            value = match_text
        else:
            match_list = [t for t in import_list if match_text in t]
            if len(match_list) == 0 or match_text == '':
                value = None
            else:
                value = match_list[0]
            # if there is more than one return all matching entries.
            if len(match_list) > 1 and help_text is True and match_text != '':
                print(f"{len(match_list)} values found with the word"
                      f"'{match_text}' in the list: {match_list}")
    except Exception as err:
        print(f"Could not auto select a value '{match_text}' for from",
              f"the list '{import_list[0]} ...': {err}")
        value = None
    return value
