#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import cbm
import bs4
import urllib.request


def check():

    try:
        def version(repo):
            try:
                soup = bs4.BeautifulSoup(urllib.request.urlopen(
                    f'https://pypi.org/project/{repo}/'), 'lxml')

                title = []
                for item in soup.find_all('h1',
                                          {'class': 'package-header__name'}):
                    title.append(item.text)

                return title[0].split()[-1]
            except urllib.error.URLError as err:
                print('No internet connection', err)

        def compare(local, remote=version('cbm')):
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

        cbm_version = compare(cbm.__version__)
        if cbm_version:
            print("There is a new version of 'cbm' library:", cbm_version,
                  "you can upgrade it with 'pip install cbm -- upgrade'")
    except Exception:
        pass
