# Build a RESTful API

**Build a RESTful API for CbM.**

In order to facilitate the access to parcel time series, also for users who do not have a DIAS account, a RESTful API with [Flask](https://www.fullstackpython.com/flask.html) can be build. Flask is a micro web frameworks servers that can handle [RESTful](https://en.wikipedia.org/wiki/Representational_state_transfer) requests/responses written in Python.

## Prerequisites

- Installed Docker (see [1.2](https://jrc-cbm.readthedocs.io/en/latest/prerequisites.html)).
- Database with extractions (see [3.1](https://jrc-cbm.readthedocs.io/en/latest/parcel_extraction.html)).

To build a RESTful API with flask first enter the virtual machine and download the CbM repository:
```bash
    git clone https://github.com/ec-jrc/cbm.git
```
Then go to the repository folder:
```bash
    cd api
```

## Create RESTful API users

To create users that can access the RESTful API for CbM, execute in the terminal: (Change the 'name','user' with a username and password)

in a python script or notebook cell:
```python
import users
users.add('admin','admin')
```
Or in the command line available options::
```bash
python users.py add username password  # Add a new user.
python users.py delete user            # Delete a user.
python users.py users                  # Print a list of the users.
```

## Database connection

Open the config/db.json file with a text editor e.g. nano config/db.json
And set the database connection information. e.g.:
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

A docker image is available on docker hub with flask and all the required python libraries needed to build a RESTful API For CbM. It can be easily deployed while in the cbm/api folder, with:

    docker run -it --name api -v "$PWD":/app -p 5000:5000 gtcap/cbm_api

<!-- $ -->

## Set available options (Optional)

To make it easier for the users to retrieve the available options, create a .json file "api_options.json" in the **"config/"** folder with the available options in the below format:

```json
{
    "aois": {
        "aio": {
            "desc": "Area of Interest",
            "years": ["2019","2018"]
        },
        "test": {
            "desc": "Sample test dataset",
            "years": ["2019"]
        }
    }
}
```

This can be retrieved from the users with the request:

    http(s):/Host.Name.Or.IP/query/options


**Important notes**

* In case the tables names are different and not as proposed in the [Chapter 1.2.](https://github.com/ec-jrc/cbm/wiki/1.2.-Pre-Requirements.-Installation-instructions-for-the-required-tools-used-for-CbM-development.) the table names of the Postges queries in the file [query_handler.py](https://github.com/ec-jrc/cbm/blob/main/cbm/api/query_handler.py) will need to be changed accordingly with the database tables names.

* This is for testing and development purposes, for production use a more secure method to store the password should be considered
