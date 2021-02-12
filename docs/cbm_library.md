# Python library cbm.

The cbm Python library provides an easy and organized way to run a variety of different tasks for checks by monitoring.

- cbm: Python library for Checks by Monitoring, includes:
    - api - RESTful API modules
    - card2db - Transfer metadata from the DIAS catalog
    - extract - Parcel extraction routines
    - foi - FOI comand line module
    - ipycbm - Interactive notebook tools, includes:
        - ext - Graphical interactive notebook widget for extraction procedures.
        - foi - Graphical interactive notebook widget for FOI analysis.
        - get - Graphical interactive notebook widget to download data.
        - qa - Graphical interactive notebook widget for Quality Assessment (QA) procedures.
        - view - Graphical interactive notebook widget to view data (graphs, images).

## cbm - Configuration file
The first time the cbm library is imported it will create the config/main.json configuration file if it does not exist and the tmp folder.
The tmp folder will be used to store all the intermediate data that are generated during some procedures. 
To configure the main configuration file manually, run in the terminal:

```bash
python3 -c "import cbm"
nano config/main.json
```

To configure the connection settings in a notebook open a widget e.g.:
```python
from cbm.ipycbm import foi
foi()
```
and go to the settings page

The main configuration file for cbm library ‘main.json’ is used in all the subpackages:

```json
{
    "set": {}, // ipycbm configurations
    "git": {}, // git repository information manly used for updating the local copy.
    "paths": {}, // The data and temp path are configurable and can be changed globally here
    "files": {}, // Location of files used it some functions
    "api": {}, // The RESTful API access information
    "db": {}, // Database access information
    "obst": {} // the object storage credentials
}
```

## cbm.api


## cbm.card2db


## cbm.extraction


## cbm.foi
FOI non interactive method (need to set manually the connection information):

```python
    vector_file = “data/parcels2020.shp”
    raster_file = “data/raster.tif”
    yaml_file = “pixelvalues_classes.yml”
    pre_min_het = 30
    pre_max_het = 70
    area_threshold = 2000

    foi(vector_file, raster_file, yaml_file,
    pre_min_het, pre_max_het, area_threshold)
```

## cbm.qa


## cbm.ipycbm

A python package 'ipycbm' is available for use in Jupyter Notebooks with interactive graphical configuration panels and data visualization tools for Checks by Monitoring. The 'ipycbm' functions use python widgets library and are only for use within Jupyter Notebooks, these functions provide easy to use graphical control panels with all the advantages of notebooks. This python library provide also code example generation for the selected datasets for extensive analysis.
The data can be retrieved from the DIAS API or directly from the database and object storage.

### Available functions

The ipycbm library have the following main functions with graphical panels:

| Panels   |  Description | Use |
|----------|------|------|
| get() |  Get data from servers with different methods (coordinates, parcels ids, map marker, polygon*) | D,R |
| view() | View the data in many different ways**, with easy selection of the view method. | D,R |
| process() | For running extraction routines and other cbm tasks | D |
| foi() | The FOI procedures notebook graphical interface | D |
| qa() | The Quality Assessment (QA) notebook graphical interface | D |

Use: D=Can be used with direct access, R=Can be used with RESTful API


There are two methods to get parcel data, one is with the use of a RESTful API and the other with direct access to the database and object storage, RESTful API is the preferred method to retrieve and view the parcels data (get, view). To get data from a RESTful API a relevant server is needed (see [5.1.](https://github.com/ec-jrc/cbm/wiki/5.1.-RESTful-API.-Build-a-RESTful-API-with-Flask-for-CbM.)).
To run the qa, foi and proc functions direct access is required.

To get the repository open a terminal and run:

```sh
git clone http://78.128.216.156/GTCAP/cbm.git
```

In the jupyterlab environment navigate to the 'cbm' folder and run the Example.ipynb notebook or create a notebook in the folder cbm and run in a cell:

```python
# Import ipycbm
from cbm import ipycbm

# run a function e.g.:
ipycbm.foi() 
```

### Configuring ipycbm



### Get function

The get() function of ipycbm library provides a graphical interface within the notebooks to get data from different sources, with variety of different methods (coordinates, parcels ids, map marker, polygon).

All data can be stored in the temporary folder 'tmp' or the 'data' folder. The difference is that every time the notebook is started, it will check if there is old data in the temporary folder and ask to delete them, the data in the data folder will not be checked.

Example folder structure for parcel with ID 12345 stored in data folder:
```sh
tmp/
    cat2019/parcel_123/123_information.json                      # Parcel information in json format
    cat2019/parcel_123/123_time_series_s2.csv                    # Time series form the parcel in csv
    cat2019/parcel_123/123_chipimages/12345_images_list.B04.csv  # A list of downloaded images
    cat2019/parcel_123/123_chipimages/S2A_MSIL2A_2019---.B04.tif # The downloaded chip images
    cat2019/parcel_123/123_chipimages/S2A_MSIL2A_...             # ...
```

### View function


