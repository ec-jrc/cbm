#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (Text, VBox, HBox, Label, Password, Dropdown,
                        Button, Checkbox, Layout, Output, BoundedIntText)

from src.utils import config, update, data_options


def widget_box():
    """Update the repository.
    Args:
        None
    Returns:
        update_widget : A widget for general settings.
    Raises:
        Error:
    Example:

    """

    # User settings
    user_info = Label("General settings.")

    values = config.read()

    user_name = Text(
        value=values['set']['user'],
        placeholder='user name',
        description='User:',
        disabled=False
    )
    user_email = Text(
        value=values['set']['email'],
        placeholder='email@.com',
        description='email:',
        disabled=False
    )
    user_institution = Text(
        value=values['set']['institution'],
        placeholder='EU-',
        description='Institution:',
        disabled=False
    )
    ms_list = data_options.eu_ms()
    ms = Dropdown(
        options=[(ms_list[m], m) for m in ms_list]+[('','')],
        value=values['set']['member_state'],
        description='Member state:',
        disabled=False,
    )
    wbox_user = VBox([user_info, user_name, user_email,
                      user_institution, ms],
                      layout=Layout(border='1px solid black'))

    # System settings
    sys_info = Label(
        "System settings.")
    paths_info = Label(
        "Select the personal data folder and the temporary folder.")

    jupyterlab = Checkbox(
        value=eval(values['set']['jupyterlab']),
        description='Workin in Jupyter Lab (Uncheck for Voila and classical jupyter environment)',
        disabled=False,
        indent=False
    )

    def on_jupyterlab_change(change):
        config.update(['set', 'jupyterlab'], str(jupyterlab.value))
    jupyterlab.observe(on_jupyterlab_change, 'value')

    path_data = Text(
        value=values['paths']['data'],
        description='Data path:'
    )

    path_temp = Text(
        value=values['paths']['temp'],
        description='Temp path:'
    )

    files_info = Label(
        "Select where to store the parcel IDs list file from:")

    file_pids_poly = Text(
        value=values['files']['pids_poly'],
        description='Polygon:'
    )
    file_pids_dist = Text(
        value=values['files']['pids_dist'],
        description='Distance:'
    )

    plimit_info = Label(
        "Warning: No more than 25 parcels are tested, unexpected results may occur.")
    plimit = BoundedIntText(
        value=int(values['set']['plimit']),
        max=100_000_000,
        min=1,
        step=1,
        description='Max parcels that can be downloaded:',
        disabled=False
    )

    wbox_sys = VBox([sys_info, jupyterlab, plimit_info, plimit,
                    paths_info, path_data, path_temp,
                    files_info, file_pids_poly, file_pids_dist],
                    layout=Layout(border='1px solid black'))

    # Git settings
    git_info = Label(
        "Git Settings. (To easily get the latest version of notebooks and scripts.)")

    git_url, git_user, git_pass = config.credentials('git')

    git_url = Text(
        value=git_url,
        description='Url:'
    )
    git_user = Text(
        value=git_user,
        description='User name:'
    )
    git_pass = Password(
        value=git_pass,
        placeholder='******',
        description='Password:'
    )

    wbox_git = VBox([git_info, git_url,
                     git_user, git_pass],
                    layout=Layout(border='1px solid black'))

    btn_save = Button(
        description='Save',
        disabled=False,
        icon='save'
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    @btn_save.on_click
    def btn_save_on_click(b):
        progress.clear_output()
        config.update(['set', 'user'], str(user_name.value))
        config.update(['set', 'email'], str(user_email.value))
        config.update(['set', 'institution'], str(user_institution.value))
        config.update(['set', 'member_state'], str(user_email.value))
        config.update(['set', 'plimit'], str(plimit.value))
        config.update(['git', 'url'], str(git_url.value))
        config.update(['git', 'user'], str(git_user.value))
        config.update(['paths', 'data'], str(path_data.value))
        config.update(['paths', 'temp'], str(path_temp.value))
        config.update(['files', 'pids_poly'], str(file_pids_poly.value))
        config.update(['files', 'pids_dist'], str(file_pids_dist.value))
        if git_pass.value != '':
            config.update(['git', 'pass'], str(git_pass.value))
        outlog("The new settings are saved.")

    wbox = VBox([config.clean_temp(), wbox_user, wbox_sys,
                 wbox_git, HBox([btn_save, update.btn_update()]),
                 progress])

    return wbox


def direct_conn(db='1'):
    values = config.read()

    info_db = Label("Database connection settings.")

    db_host = Text(
        value=values['db'][db]['conn']['host'],
        placeholder='Database host',
        description='db Host:',
        disabled=False
    )
    db_port = Text(
        value=values['db'][db]['conn']['port'],
        placeholder='Database port',
        description='db Port:',
        disabled=False
    )
    db_name = Text(
        value=values['db'][db]['conn']['name'],
        placeholder='Database name',
        description='db Name:',
        disabled=False
    )
    db_user = Text(
        value=values['db'][db]['conn']['user'],
        placeholder='Database user',
        description='db User:',
        disabled=False
    )
    db_pass = Password(
        value=values['db'][db]['conn']['pass'],
        placeholder='******',
        description='db Pass:',
        disabled=False
    )

    info_os = Label("Object storage connection settings.")
    os_dias = Dropdown(
        options=['EOSC', 'CREODIAS', 'SOBLOO', 'MUNDI', 'ONDA', 'WEKEO', ''],
        value=values['obst']['osdias'],
        description='DIAS:',
        disabled=False,
    )
    os_host = Text(
        value=values['obst']['oshost'],
        placeholder='Storage host',
        description='s3 Host:',
        disabled=False
    )
    os_bucket = Text(
        value=values['obst']['bucket'],
        placeholder='Bucket name',
        description='Bucket name:',
        disabled=False
    )
    os_access_key = Text(
        value=values['obst']['access_key'],
        placeholder='Access key',
        description='Access Key:',
        disabled=False
    )
    os_secret_key = Password(
        value=values['obst']['secret_key'],
        placeholder='Secret key',
        description='Secret Key:',
        disabled=False
    )

    wb_save = Button(
        description='Save',
        disabled=False,
        icon='save'
    )

    progress = Output()

    def outlog(*text):
        with progress:
            print(*text)

    @wb_save.on_click
    def wb_save_on_click(b):
        progress.clear_output()
        # Save database connection information
        config.update(['db', db, 'conn', 'host'], str(db_host.value))
        config.update(['db', db, 'conn', 'port'], str(db_port.value))
        config.update(['db', db, 'conn', 'name'], str(db_name.value))
        config.update(['db', db, 'conn', 'user'], str(db_user.value))
        if db_pass.value != '':
            config.update(['db', db, 'conn', 'pass'], str(db_pass.value))
        # Save Object storage connection information
        config.update(['obst', 'osdias'], str(os_dias.value))
        config.update(['obst', 'oshost'], str(os_host.value))
        config.update(['obst', 'bucket'], str(os_bucket.value))
        config.update(['obst', 'access_key'], str(os_access_key.value))
        if os_secret_key.value != '':
            config.update(['obst', 'secret_key'], str(os_secret_key.value))

        outlog("All changes are saved.")

    wbox = VBox([info_db, db_host, db_port, db_name, db_user, db_pass,
                 info_os, os_dias, os_host, os_bucket, os_access_key,
                 os_secret_key, wb_save, progress])

    return wbox
