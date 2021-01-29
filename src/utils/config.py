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
from os.path import dirname, abspath

folder_repo = os.path.dirname(dirname(dirname(abspath(__file__))))
file_config = f"_config.json"


def get_value(dict_keys={}, file=file_config, var_name=None, help_text=True):
    """Get value from config.json file, with an arbitrary length key.

    Examples:

        config.get_value(['information', 'aoi'])

        To display the variable name and and some information use:
        config.get_value(['information', 'aoi'], 'AOI' config.file_config, False)

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


def update(dict_keys={}, val=None, file=file_config):
    """Update config.json file, with an arbitrary length key.

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
        tempfile = os.path.join(folder_repo, str(uuid.uuid4()))
        with open(tempfile, 'w') as f:
            json.dump(config_dict, f, indent=4)

        # rename temporary file replacing old file
        os.rename(tempfile, file)
    except Exception as err:
        print(f"Could not update key in the file '{file}': {err}")


def delete(dict_keys={}, file=file_config):
    """Delete keys from config.json file.

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

        tempfile = os.path.join(folder_repo, str(uuid.uuid4()))
        with open(tempfile, 'w') as f:
            json.dump(config_dict, f, indent=4)

        # rename temporary file replacing old file
        os.rename(tempfile, file)
    except Exception as err:
        print(f"Could not delete key in the file '{file}': {err}")


def read(file=file_config):
    """Read <file>.json file

    Returns:
        data - A python dict of the selected file.

    """
    try:
        # if os.path.isfile(file) is True:
        with open(file, 'r') as f:
            data = json.load(f)
            return data
    except Exception as err:
        if file == file_config:
            try:
                create(file)
                with open(file, 'r') as f:
                    data = json.load(f)
                return data
            except Exception as err:
                print(f"Could not read file '{file}': {err}")
        else:
            print(f"Could not read file '{file}': {err}")


def create(file=file_config):
    """Automatically create a config file if it does not exist.
    """
    filepath = f"{folder_repo}/{file}"

    # if file does not exist, create it
    if os.path.isfile(filepath) is False:
        try:
            # Default configuration file
            file_default = "src/utils/config_default.json"
            with open(file_default, 'r') as f:
                config_default = json.load(f)
            with open(filepath, 'w') as f:
                json.dump(config_default, f, indent=4)
            time.sleep(0.5)  # Sleep for half second to run the function.
            file_name = filepath.split('/')[-1]
            print("The configuration file did not exist, a new default "
                  f"{file_name} file was created.")
        except Exception as err:
            print(f"Could not create the configuration file: {err}")


def update_keys():
    """Update missing keys of old configuration files."""
    create()
    file_default = "src/utils/config_default.json"
    with open(file_config, 'r') as f:
        dict1 = json.load(f)
    with open(file_default, 'r') as f:
        dict2 = json.load(f)

    for idx, key in enumerate(dict2.keys()):
        if key not in dict1:
            dict1[key] = dict2[key]
        for k in dict2[key].keys():
            if k not in dict1[key]:
                dict1[key][k] = dict2[key][k]

    with open(file_config, 'w') as f:
        json.dump(dict1, f, indent=4)

    if idx > 0:
        print(f"{idx+1} new json configuration objects are added to the configuration file.")


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


def clean_temp(hide=False):
    import shutil
    from IPython.display import display
    from ipywidgets import Button, Output, HBox

    progress = Output()
    def outlog(*text):
        progress.clear_output()
        with progress:
            print(*text)

    temppath = get_value(['paths', 'temp'])
    directory = os.listdir(temppath)

    if len(directory) > 0:
        outlog(f"Your temp folder '{temppath}' has old files:",
              f" '{directory}', do you want to delete them? ")

    clean_temp = Button(
        value=False,
        description='Empty temp folder',
        disabled=False,
        button_style='danger',
        tooltip='Delete all data from the temporary folder.',
        icon='trash'
    )

    clean_box = HBox([clean_temp, progress])

    @clean_temp.on_click
    def clean_temp_on_click(b):
        temppath = get_value(['paths', 'temp'])
        directory = os.listdir(temppath)
        for i in directory:
            try:
                shutil.rmtree(f'{temppath}{i}')
            except Exception:
                os.remove(f'{temppath}{i}')
        outlog(f"The '{temppath}' folder is now empty.")

    if hide is False:
        return clean_box
    elif hide is True and len(directory) > 0:
        return clean_box
    else:
        return HBox([])

