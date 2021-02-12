# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

"""Patching m2r2"""
import m2r2

current_m2r2_setup = m2r2.setup

def patched_m2r2_setup(app):
    try:
        return current_m2r2_setup(app)
    except (AttributeError):
        app.add_source_suffix(".md", "markdown")
        app.add_source_parser(m2r2.M2RParser)
    return dict(
        version=m2r2.__version__, parallel_read_safe=True, parallel_write_safe=True,
    )

m2r2.setup = patched_m2r2_setup

# -- Project information -----------------------------------------------------

project = 'cbm'
copyright = '2021, European Commission, Joint Research Centre'
author = 'European Commission, Joint Research Centre'
authors = 'Guido Lemoine, Konstantinos Anastasakis'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_rtd_theme',
    'm2r2'
]

source_suffix = [".rst", ".md"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store','.ipynb_checkpoints']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
# Themes: sphinx_rtd_theme, alabaster
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']