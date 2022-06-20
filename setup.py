#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='cbm',
    version='0.0.18',
    python_requires='>=3.6',
    description='Checks by Monitoring (CbM)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/ec-jrc/cbm',
    author='Guido Lemoine, Konstantinos Anastasakis',
    author_email='',
    license='BSD 3-clause',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'numpy>=1.21',
        'matplotlib>=3.3.0',
        'pandas>=1.1.0',
        'rasterio>=1.1.5',
        'requests>=2.24.0',
        'descartes>=1.1.0',
        'scikit-image>=0.19.0',
        'psycopg2-binary'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
    ],
)
