#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import subprocess
from ipywidgets import (Text, Label, Password, Button,
                        Output, HBox, VBox)
from IPython.display import display

from cbm.utils import config


def btn_update():
    """Update the repository.
    Args:
        None
    Returns:
        update_widget : A widget for updating the repository
    Raises:
        Error:
    Example:

    """

    wb_update = Button(
        description='Update',
        disabled=False,
        button_style='success',
        icon='angle-up'
    )

    wb_fupdate = Button(
        description='Force Update',
        disabled=False,
        button_style='danger'
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)
    
    wbox = VBox(children=[wb_update, progress])

    @wb_fupdate.on_click
    def wb_fupdate_on_click(b):
        pass
#         git_url, git_user, git_pass = config.credentials('git')
#         url = git_url.replace('http://', '')
#         url = url.replace('https://', '')
#         with progress:
#             run_update(['git', '-C', './', 'reset', '--hard', 'HEAD'])
#             run_update(['git', '-C', './', 'pull',
#                         f'http://{git_user}:{git_pass}@{url}'])

    @wb_update.on_click
    def wb_update_on_click(b):
        pass
#         git_url, git_user, git_pass = config.credentials('git')
#         url = git_url.replace('http://', '')
#         url = url.replace('https://', '')
#         with progress:
#             if git_pass == '':
#                 outlog("Please add the password for the git server.")
#             else:
#                 run_update(['git', '-C', './', 'pull',
#                             f'http://{git_user}:{git_pass}@{url}'],
#                            wb_fupdate)

    return wbox


def run_update(command, widget=None, silent=False):
    out = subprocess.Popen(command,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    
    display(Label(stdout.decode()))
    if stderr is not None:
        display(Label(stderr))
    if 'Aborting' in stdout.decode():
        text = ("Warning! The above files will be overwritten.\n",
              "If you have important changes,",
              "be sure to make a backup of them first.")
        warning = Label(' '.join(text))
        display(VBox([warning, widget]))


def check():
    progress = Output()
    def outlog(*text):
        with progress:
            print(*text)

#     git_url, git_user, git_pass = config.credentials('git')
#     url = git_url.replace('http://', '')
#     url = url.replace('https://', '')
#     command = ['git', '-C', './', 'remote', 'show',
#                f'http://{git_user}:{git_pass}@{url}']
#     out = subprocess.Popen(command,
#                            stdout=subprocess.PIPE,
#                            stderr=subprocess.STDOUT)
#     stdout, stderr = out.communicate()
#     if 'out of date' in stdout.decode():
#         display(progress)
#         outlog("There is an new version CbM.",
#               "Do you want to update your local CbM repository?")
#         display(btn_update())
