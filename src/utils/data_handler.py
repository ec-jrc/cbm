#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


# Data managment module
"""
Available options:
'Display raw data', 1 : Print raw dataframe
'Display pandas df', 2 : Print pandas dataframe
'To .json file', 10 : Save to new .json file.
'To .csv file', 11 : Save to new .csv file.
'To .csv file', 12 : Append to csv.
"""

import os
import json
import pandas as pd

def export(data, method=None, filename=None):
    if method == 10:  # Save to new .json file.
        file = f'{filename}.json'
        try:
            os.makedirs(os.path.dirname(file), exist_ok=True)
            with open(file, "w") as f:
                json.dump(data, f)
            return f"File saved at: {file}"
        except Exception as err:
            return f"Could not create the file: {err}"

    elif method == 11:  # Save to new .csv file.
        file = f'{filename}.csv'
        try:
            if isinstance(data, pd.DataFrame):
                data.to_csv(file, index=True, header=True)
            elif isinstance(data, dict):
                os.makedirs(os.path.dirname(file), exist_ok=True)
                df = pd.DataFrame.from_dict(data, orient='columns')
                df.to_csv(file, index=True, header=True)
            return f"File saved at: {file}"
        except Exception as err:
            return f"Could not create the file: {err}"

    elif method == 12:  # Append to csv.
        file = f'{filename}.csv'
        try:
            if os.path.isfile(f'{filename}.csv'):
                exist = False
            else:
                exist = True
            os.makedirs(os.path.dirname(file), exist_ok=True)
            df = pd.DataFrame.from_dict(data, orient='columns')
            df.to_csv(file, mode='a', header=exist)
            return f"File saved at: {file}"
        except Exception as err:
            return f"Could not create the file: {err}"

    elif method == 2:  # Display pandas dataframe
        df = pd.DataFrame.from_dict(data, orient='columns')
        print(df)

    else:  # Display raw dataframe
        print(data)
