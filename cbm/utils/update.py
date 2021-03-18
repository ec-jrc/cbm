#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import requests
import inspect
import cbm


def check(package=cbm):
    try:
        def version(package):
            response = requests.get(f'https://pypi.org/pypi/{package}/json')
            return response.json()['info']['version']

        def compare(local, remote):
            """Compare local to remote package version
            """
            lv = [int(v) for v in local.split('.')]
            rv = [int(v) for v in remote.split('.')]
            if lv[0] < rv[0]:
                return remote
            elif lv[1] < rv[1]:
                return remote
            elif lv[2] < rv[2]:
                return remote
            else:
                return None

        def retrieve_name(var):
            """
            Gets the name of var. Does it from the out most frame inner-wards.
            :param var: variable to get name from.
            :return: string
            """
            for fi in reversed(inspect.stack()):
                names = [var_name for var_name,
                         var_val in fi.frame.f_locals.items() if var_val is var]
                if len(names) > 0:
                    return names[0]

        package_version = compare(package.__version__,
                                  version(retrieve_name(package)))
        if package_version:
            print(f"There is a new version of {retrieve_name(package)}:",
                  package_version,
                  "you can upgrade it with 'pip install cbm --upgrade'")
    except Exception:
        pass
