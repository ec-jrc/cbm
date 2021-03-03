# Build a RESTful API

**Build a RESTful API for CbM.**

In order to facilitate the access to parcel time series, also for users who do not have a DIAS account, a RESTful API with [Flask](https://www.fullstackpython.com/flask.html) can be build. Flask is a micro web frameworks servers that can handle [RESTful](https://en.wikipedia.org/wiki/Representational_state_transfer) requests/responses written in Python.

## Prerequisites

- Installed Docker (see [1.2](https://jrc-cbm.readthedocs.io/en/latest/prerequisites.html)).
- Database with extractions (see [3.1](https://jrc-cbm.readthedocs.io/en/latest/parcel_extraction.html)).

To build a RESTful API with flask, first [enter the virtual machine](https://jrc-cbm.readthedocs.io/en/latest/prerequisites.html#connecting-to-the-tenant-host-vm-via-ssh) and download the CbM repository:
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
python users.py create username password # To Create a new user.
python users.py delete username          # Delete a user.
python users.py list                     # Print a list of the users.
```
(Change the 'username' and 'password' with a username and password of the user)

Or import the module in a python script or notebook cell:

```python
import users # Import the users module
# Create a new user with:
users.create('admin','admin')

# To delete a user.
users.delete('admin')

# Print a list of the users.
print(users.get_list())
```

## Database connection

Open the config/db.json file with a text editor (e.g. **nano config/db.json**)
and set the database connection information. e.g.:
```json
{
    "db": {
        "main": {
            "desc": "Main database connection information.",
            "conn": {
                "host": "0.0.0.0",
                "port": "5432",
                "name": "postgres",
                "sche": "public",
                "user": "postgres",
                "pass": "MyPassword"
            }
        }
    }
}
```

## Deploy the RESTful API docker container

A docker image is available on [docker hub](https://hub.docker.com/r/gtcap/cbm_api). This image includes flask and all the required python libraries needed to build a RESTful API For CbM. It can be easily deployed with:

    docker run -it --name api -v "$PWD":/app -p 5000:5000 gtcap/cbm_api

<!-- $ -->

*Must run from within the 'cbm/api/' folder

To expose the RESTful server to port 80, change -p 5000:5000 to -p 80:5000, or to any other port.


### Build from source

To build the cbm_api docker image from source, go to the docker folder of cbm package
```bash
cd cbm/docker/cbm_api
```
And run:
```bash
docker build --tag cbm_api .
```
Go back to api folder **cbm/api** and deployed the container with:

    docker run -it --name api -v "$PWD":/app -p 5000:5000 cbm_api

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


**Important notes**

* In case the tables names are different and not as proposed in the [Chapter 1.2.](https://jrc-cbm.readthedocs.io/en/latest/setup_prerequisites.html#essential-cbm-tables) the table names of the Postges queries in the file [query_handler.py](https://github.com/ec-jrc/cbm/blob/main/api/query_handler.py) will need to be changed accordingly with the database tables names.

* This is for testing and development purposes, for production use a more secure method to store the password should be considered.
