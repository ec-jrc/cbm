# Build

**Build a RESTful API for CbM.**

In order to facilitate the access to parcel time series, also for users who do not have a DIAS account, a RESTful API with [Flask](https://www.fullstackpython.com/flask.html) can be build. Flask is a micro web frameworks servers that can handle [RESTful](https://en.wikipedia.org/wiki/Representational_state_transfer) requests/responses written in Python.

## Prerequisites

 - Installed Docker (see [1.2](https://jrc-cbm.readthedocs.io/en/latest/prerequisites.html)).
 - Database with extractions (see [3.1](https://jrc-cbm.readthedocs.io/en/latest/parcel_extraction.html)).

To build a RESTful API with flask first enter the virtual machine and download the CbM repository:

    git clone https://github.com/ec-jrc/cbm.git

Then go to the repository folder:

    cd cbm


## Create RESTful API users

To create users that can access the RESTful API for CbM. Enter the running 'api' container:

    docker exec -it api bash

and then execute: (Change the 'name','user' with a username and spasword)

    python3 -c "from src.apicbm import users; users.add('user','pass')"


## Database configuration

If the ipycbm is used and configured this step may not be needed.
RESTful API for CbM uses the same structured _config.json file as ipycbm that store the database connection information as well.
Navigate to the db section and set the database connection information. if the file does not exist create the file _config.json in the cbm folder and add:

    {
        "db": {
            "1": {
                "desc": "",
                "conn": {
                    "host": "0.0.0.0",
                    "port": "5432",
                    "name": "postgres",
                    "sche": "public",
                    "user": "postgres",
                    "pass": ""
                }
            }
        }
    }


## Deploy the RESTful API docker container

A docker image is available on docker hub with flask and all the required python libraries needed to build a RESTful API For CbM. It can be easily deployed with:

    docker run -it --name api -v "$PWD":/app -p 5000:5000 gtcap/cbm_api

## Important notes

1. **In case the tables names are different and not as proposed in the [Chapter 1.2.](https://github.com/ec-jrc/cbm/wiki/1.2.-Pre-Requirements.-Installation-instructions-for-the-required-tools-used-for-CbM-development.) the table names of the Postges queries in the file [query_handler.py](https://github.com/ec-jrc/cbm/blob/main/cbm/api/query_handler.py) will need to be changed accordingly with the database tables names.**

2. **For production use a more secure method to store the password should be considered**
