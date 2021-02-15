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
from os.path import dirname, abspath, join

folder_repo = os.path.dirname(dirname(dirname(abspath(__file__))))
folder_config = f"{folder_repo}/config/"
main_config = "main.json"
main_default = f"{dirname(abspath(__file__))}/main_default.json"

def get_value(dict_keys={}, file=main_config, var_name=None, help_text=True):
    """Get value from a configuration file, with an arbitrary length key.

    Examples:
        config.get_value(['information', 'aoi'])

        To display the variable name and and some information use:
        config.get_value(['information', 'aoi'], 'AOI' config.main_config, False)

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


def update(dict_keys={}, val=None, file=main_config):
    """Update configuration file, with an arbitrary length key.

    Example:
        config.update(['information', 'aoi'], val='test')

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
        tempfile = join(folder_config, str(uuid.uuid4()))
        with open(tempfile, 'w') as f:
            json.dump(config_dict, f, indent=4)

        # rename temporary file replacing old file
        os.rename(tempfile, join(folder_config, file))
    except Exception as err:
        print(f"Could not update key in the file '{file}': {err}")


def delete(dict_keys={}, file=main_config):
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

        tempfile = join(folder_config, str(uuid.uuid4()))
        with open(tempfile, 'w') as f:
            json.dump(config_dict, f, indent=4)

        # rename temporary file replacing old file
        os.rename(tempfile, join(folder_config, file))
    except Exception as err:
        print(f"Could not delete key in the file '{file}': {err}")


def read(file=main_config):
    """Read configuration file
    Example:
        config.read("main.json")

    Arguments:
        file (str): the name of the configuration file

    Returns:
        data - A python dict of the selected file.

    """
    try:
        with open(f"{folder_config}{file}", 'r') as f:
            data = json.load(f)
            return data
    except Exception as err:
        if file == main_config:
            create()
            with open(join(folder_config, file), 'r') as f:
                data = json.load(f)
            return data
        elif file == 'api_options.json':
            create(join(folder_repo, '/cbm/api/', file), file)
            with open(join(folder_config, file), 'r') as f:
                data = json.load(f)
            return data
        else:
            print(f"Could not read file '{file}': {err}")


def create(from_file=main_default, to_file=main_config):
    """Automatically create a config file if it does not exist.
    """

    # if file does not exist, create it
    if os.path.isfile(join(folder_config, to_file)) is False:
        # Read from default configuration file
        with open(from_file, 'r') as f:
            dict_default = json.load(f)
        with open(join(folder_config, to_file), 'w') as f:
            json.dump(dict_default, f, indent=4)
        time.sleep(0.5)  # Sleep for half second to run the function.
        print("The configuration file did not exist, a new default ",
              f"{to_file} file was created.")


def update_keys(from_file=main_default, to_file=main_config):
    """Update missing keys of old configuration files."""
    if os.path.isfile(join(folder_config, to_file)) is False:
        create(from_file, to_file)

    with open(from_file, 'r') as f:
        dict_new = json.load(f)
    
    with open(join(folder_config, to_file), 'r') as f:
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
    tempfile = join(folder_config, str(uuid.uuid4()))
    with open(tempfile, 'w') as f:
        json.dump(dict_old, f, indent=4)

    # rename temporary file replacing old file
    os.rename(tempfile, join(folder_config, to_file))

    if updated_keys > 0:
        print(f"{updated_keys+1} new json configuration objects are added to the configuration file.")


def credentials(service):
    try:
        url = get_value([service, 'url'])
        user = get_value([service, 'user'])
        pass_ = get_value([service, 'pass'])
    except Exception as err:
        print(f"Could not get credentials for '{service}'. {err}")
        url, user, pass_ = ''

    return url, user, pass_


def autoselect(matching_text=None, import_list=[], help_text=True):
    """Automatically select the first object that the matching text is included
    in its name. If no object has this word no object will be automatically
    selected. If 'help_text' value is False no output help text for the founded
    tables will be returned in case there are more entries in the list with the
    matching text.

    Attributes
    ----------
    -Options-    -Type- -Description-
    matching_text : Str
        The selected database (1 or 2).

    import_list   : List
        List of the options.

    help_text     : Boolean
        True or False, display or not all the founded tables if more then one.

    Returns
    -------
    The selected value that match the input
    """
    value = ''
    try:
        if import_list is None:
            value = None
        elif matching_text in import_list:
            value = matching_text
        else:
            match_list = [t for t in import_list if matching_text in t]
            if len(match_list) == 0 or matching_text == '':
                value = None
            else:
                value = match_list[0]
            # if there is more than one return all matching entries.
            if len(match_list) > 1 and help_text is True and matching_text != '':
                print(f"{len(match_list)} values found with the word"
                      f"'{matching_text}' in the list: {match_list}")
    except Exception as err:
        print(f"Could not auto select a value '{matching_text}' for from the list '{import_list[0]} ...': {err}")
        value = None
    return value
