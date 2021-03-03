# Installation.

## Dependencies

The 'cbm' python library has one C library dependency: GDAL >=2.x. GDAL itself depends on many of other libraries provided by most major operating systems and also depends on the non standard GEOS and PROJ4 libraries.

For GDAL installation see: [pypi.org/project/GDAL](https://pypi.org/project/GDAL/).

## Installing from [PyPI](https://pypi.org/project/cbm/)

```bash
pip install cbm
```

## Installing from source:

```bash
git clone https://github.com/ec-jrc/cbm.git
cd cbm
python setup.py install
```

## Installing for development

```bash
git clone https://github.com/ec-jrc/cbm.git
cd cbm
pip install -e .
```

# Overview
The cbm Python library provides an easy and organized way to run a variety of different tasks for checks by monitoring.

Python library for Checks by Monitoring, includes:
- card2db : Transfer metadata from the DIAS catalog
- extract : Parcel extraction routines
- get : To download data locally
- foi : FOI analysis module
- report : For reports creation
- ipycbm : Interactive notebook tools, includes:
    - ext : Graphical interactive notebook widget for extraction procedures.
    - foi : Graphical interactive notebook widget for FOI analysis.
    - get : Graphical interactive notebook widget to download data.
    - qa : Graphical interactive notebook widget for Quality Assessment (QA) procedures.
    - view : Graphical interactive notebook widget to view data (graphs, images).

The first time the cbm library is imported it will create:
- config/main.json # The main configuration file
- temp # Folder to store all the intermediate data.
- data # Folder to store the user data

All data can be stored in the temporary folder 'temp' or the 'data' folder. The difference is that every time the notebook is started, it will check if there is old data in the temporary folder and ask to delete them.

There are two methods to get parcel data, one is with the use of a RESTful API and the other with direct access to the database and object storage, RESTful API is the preferred method to retrieve and view the parcels data. To get data from a RESTful API a relevant server is needed see [build a RESTful API server](https://jrc-cbm.readthedocs.io/en/latest/api_build.html).
To run the extract functions direct access is required.


## Notebook widgets

A subpackage 'ipycbm' is available for use in Jupyter Notebooks and provides interactive graphical configuration panels and data visualization tools for Checks by Monitoring.

**Main functions**

| Panels   |  Description | Use |
|----------|------|------|
| config() |  To configure the config/main.json file interactively | D,R |
| get() |  Get data from servers with different methods (coordinates, parcels ids, map marker, polygon*) | D,R |
| view() | View the data in many different ways**, with easy selection of the view method. | D,R |
| extract() | For running extraction routines and other cbm tasks | D |
| foi() | The FOI procedures notebook graphical interface | D,R |
| qa() | The Quality Assessment (QA) notebook graphical interface | D,R |

Use: D=Can be used with direct access, R=Can be used with RESTful API


# Configuration

To configure the main configuration file manually, run in the terminal:

```bash
python3 -c "import cbm"
nano config/main.json
```

The main configuration file for cbm library ‘main.json’ is used in all the subpackages:

```json
{
    "set": {}, // General configurations
    "paths": {}, // The data and temp path are configurable and can be changed globally
    "files": {}, // Location of files used it some functions
    "api": {}, // The RESTful API access information
    "db": {}, // Database access information
    "dataset": {}, // Dataset information and tables configuration
    "obst": {} // the object storage credentials
}
```

## Configuration widget
To configure the config/main.json file interactively, in the jupyterlab environment create a new notebook and run in a cell:

```python
# Import ipycbm
from cbm import ipycbm
# Open the configuration widget
ipycbm.config() 
```
![](https://raw.githubusercontent.com/konanast/cbm_media/main/ipycbm_config_01.png)

