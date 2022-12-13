#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import socket
import logging
from ssh2.session import Session
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed


vms = ['192.168.0.11', '192.168.0.13', '192.168.0.8', '192.168.0.15']
USERNAME = 'eouser'
PRIVATEKEY = 'config/master.pem'
CHIPSDIR = f'/home/{USERNAME}/chips'
DOCKERRUN = f'docker run --rm -v {CHIPSDIR}:/usr/src/app -u 1000:1000 glemoine62/dias_py python'

def chipCollect(unique_dir, ftype='tif'):
    # Collect the generate chips
    for vm in vms:
        logging.debug(f"Collecting from {vm}")
        os.popen(f"scp -i {PRIVATEKEY} -o \"StrictHostKeyChecking no\" {USERNAME}@{vm}:{CHIPSDIR}/{unique_dir}/*.{ftype} {unique_dir}").readlines()
    # Clean up (caching is done on the master)
    for vm in vms:
        logging.debug(f"Cleaning up {vm}")
        os.popen(f"ssh -i {PRIVATEKEY} -o \"StrictHostKeyChecking no\" {USERNAME}@{vm} 'rm -Rf {CHIPSDIR}/{unique_dir}/*'").readlines()


def calendarCheck(klist, start_date, end_date):
    # Check whether keys are within the time window
    s_date = datetime.strptime(start_date, '%Y-%m-%d')
    e_date = datetime.strptime(end_date, '%Y-%m-%d')
    e_date = e_date + timedelta(days=1)
    dlist = [datetime.strptime(k, '%Y%m%dT%H%M%S') for k in klist]
    slist = [d.strftime('%Y%m%dT%H%M%S') for d in dlist if s_date < d < e_date]
    return slist


def runjobs(chiplist, lon, lat, unique_dir, script, args):
    chip_set = {}
    with ProcessPoolExecutor(len(chiplist)) as executor:
        jobs = {}
        for i in range(len(chiplist)):
            reference = chiplist[i]
            vm = i % len(vms)
            logging.debug(f"{reference} launched on {vms[vm]}")
            logging.debug(f"{DOCKERRUN} {script} {lon} {lat} {reference} {unique_dir} {args}")
            docker_launch = f"{DOCKERRUN} {script} {lon} {lat} {reference} {unique_dir} {args}"
            job = executor.submit(launchjob, vms[vm], docker_launch)
            jobs[job] = docker_launch

        for job in as_completed(jobs):
            instance = jobs[job]
            chip_set[instance] = job.result()


def launchjob(host, cmd):
    if not os.path.isfile(PRIVATEKEY):
        print(f"No such private key {PRIVATEKEY}")
        sys.exit(1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, 22))
    s = Session()
    s.handshake(sock)
    s.userauth_publickey_fromfile(USERNAME, PRIVATEKEY, passphrase='')
    chan = s.open_session()
    chan.execute(cmd)
    size, data = chan.read()
    while size > 0:
        print(data)
        size, data = chan.read()
