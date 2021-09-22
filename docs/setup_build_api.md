# Build a RESTful API

**Build a RESTful API for CbM.**

In order to facilitate the access to parcel time series, also for users who do not have a DIAS account, a RESTful API with [Flask](https://www.fullstackpython.com/flask.html) can be build. Flask is a micro web frameworks servers that can handle [RESTful](https://en.wikipedia.org/wiki/Representational_state_transfer) requests/responses written in Python.

## Prerequisites

- Installed Docker (see: [Software requirements](https://jrc-cbm.readthedocs.io/en/latest/setup_prerequisites.html#required-software)).
- Database with extractions (see: [Parcel extraction](https://jrc-cbm.readthedocs.io/en/latest/setup_extract.html)).

To build a RESTful API with flask, first [access the virtual machine](https://jrc-cbm.readthedocs.io/en/latest/setup_prerequisites.html#connecting-to-the-tenant-host-vm-via-ssh) and download the CbM repository:
```bash
    git clone https://github.com/ec-jrc/cbm.git
```
Then go to the api folder of the downloaded package:
```bash
    cd cbm/api
```

## Create RESTful API users

To create and manage users that can access the RESTful API for CbM, execute in the terminal:

```bash
python3 scripts/users.py add username password dataset # To Create a new user.
python3 scripts/users.py delete username               # Delete a user.
python3 scripts/users.py list                          # Print a list of the users.
```
Change the 'username' and 'password' with a username and password of the user.
Set the dataset to the data that the user will be restricted to.

Example:
```bash
python3 scripts/users.py add john_doe Pass4John aoi
```

Alternatively import the module in a python script or notebook cell:

```python
from scripts import users # Import the users module (set the import accordingly to your path)
# Create a new user with:
users.add('username', 'password', 'dataset')

# To delete a user.
users.delete('username')

# Print a list of the users.
print(users.get_list())
```

## Database connection

Open the config/db.json file with a text editor (e.g. **nano config/main.json**)
and set the database connection information. e.g.:
```json
{
    "db": {
        "main": {
            "desc": "Main database connection information.",
            "host": "0.0.0.0",
            "port": "5432",
            "name": "postgres",
            "sche": "public",
            "user": "postgres",
            "pass": "MyPassword"
        }
    },
    "s3": {
        "dias": "EOSC",
        "host": "http://data.cloudferro.com",
        "bucket": "DIAS",
        "access_key": "anystring",
        "secret_key": "anystring"
    }
}
```


## Dataset configuration

All dataset configuration are set in the config/dataset.json file.
```json
{
    "default_2020": {
        "db": "main",
        "description": "Dataset description",
        "center": "51.0,14.0",
        "zoom": "5",
        "year": "",
        "start_date": "",
        "end_date": "",
        "extent": "",
        "flip_coordinates": "False",
        "tables": {
            "parcels": "par",
            "dias_catalog": "dias_catalogue",
            "scl": "hists_2020",
            "s2": "s2_sigs_2020",
            "bs": "bs_sigs_2020",
            "c6": "c6_sigs_2020",
            "bs_tf": "bs_tensorflow"
        },
        "pcolumns": {
            "parcel_id": "id",
            "crop_name": "name",
            "crop_code": "code"
        }
    }
}
```


## Deploy the RESTful API docker container

A docker image is available on [docker hub](https://hub.docker.com/r/gtcap/cbm_api). This image includes flask and all the required python libraries needed to build a RESTful API For CbM. It can be easily deployed with:

    docker run -it --name api -v "$PWD":/app -p 80:80 gtcap/cbm_api

<!-- $ -->

*Must run from within the 'cbm/api/' folder

To expose the RESTful server to another port, change the port parameter -p [PORT]:80.


### Build from source

To build the cbm_api docker image from source, go to the docker folder of cbm package
```bash
git clone https://github.com/ec-jrc/cbm.git
cd cbm/docker/cbm_api
```
And run:
```bash
docker build --tag gtcap/cbm_api .
```
Go back to api folder **cbm/api** and deployed the container with:

    docker run -it --name api -v "$PWD":/app -p 5000:80 gtcap/cbm_api

<!-- $ -->

## Provide available options (Optional)

Add in the file "config/options.json" the available RESTful API options in the below format:

```json
{
    "aois": {
        "aio": {
            "desc": "Area of Interest",
            "year": ["2019","2018"]
        },
        "test": {
            "desc": "Sample test dataset",
            "year": ["2019"]
        }
    }
}
```

This can be retrieved from the users with the request:

    http(s):/Host.Name.Or.IP/query/options


## Adding orthophotos (Optional)

It is often handy to have a high resolution overview of the parcel situation.
A (globally) useful set are the Google and Bing (or Virtual Earth) background image sets.
To add new base maps add in the 'tms/' folder the xml files.

Bing base maps example:

```xml
<GDAL_WMS>
    <Service name="VirtualEarth">
        <ServerUrl>http://a${server_num}.ortho.tiles.virtualearth.net/tiles/a${quadkey}.jpeg?g=90</ServerUrl>
    </Service>
    <DataWindow>
        <UpperLeftX>-20037508.34</UpperLeftX>
        <UpperLeftY>20037508.34</UpperLeftY>
        <LowerRightX>20037508.34</LowerRightX>
        <LowerRightY>-20037508.34</LowerRightY>
        <TileLevel>19</TileLevel>
        <TileCountX>1</TileCountX>
        <TileCountY>1</TileCountY>
        <YOrigin>top</YOrigin>
    </DataWindow>
    <Projection>EPSG:900913</Projection>
    <BlockSizeX>256</BlockSizeX>
    <BlockSizeY>256</BlockSizeY>
    <BandsCount>3</BandsCount>
    <MaxConnections>4</MaxConnections>
    <Cache />
</GDAL_WMS>
```


**Important notes**

* In case the tables names are different and not as proposed in the ['essential-cbm-tables' chapter](https://jrc-cbm.readthedocs.io/en/latest/setup_prerequisites.html#essential-cbm-tables) the table names of the Postges queries in the file [query_handler.py](https://github.com/ec-jrc/cbm/blob/main/api/query_handler.py) will need to be changed accordingly with the database tables names.

* This is for testing and development purposes, for production use a more secure method to store the password should be considered.
