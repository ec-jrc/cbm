# Required software

## Docker (Ubuntu 18.04)
Note these instructions are for Ubuntu 18.04 and may not work for other platforms.
Installation instructions for other platforms can be found at [docs.docker.com](https://docs.docker.com/engine/install).

The open virtualization software Docker was used to deploy all the applications
required for CbM development. The Docker is a set of platform as a service
products that use OS-level virtualization to deliver software in packages called
containers.
To run the extraction routines it is recommended to install the latest version
of docker with the below steps:
```sh
sudo snap remove docker
rm -R /var/lib/docker
sudo apt-get remove docker docker-engine docker.io
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository    "deb [arch=amd64] https://download.docker.com/linux/ubuntu
     $(lsb_release -cs) \
     stable"
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
sudo groupadd docker
sudo usermod -aG docker $USER
```
exit the VM and re-connect, now run
```sh
docker run hello-world
sudo systemctl enable docker
```

## PostGIS

For this project we use PostgreSQL database with the PostGIS extension. Postgis
extends the open source PostgreSQL database server with spatial data constructs
(e.g. geometries) and spatial querying capacities, allowing storage and query of
information about location and mapping.

To run a postgres database with postgis extension run:
```sh
docker run --name cbm_db -d --restart always -v database:/var/lib/postgresql -v "$PWD"/sql:/root/sql --shm-size=2gb -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASS=mydiaspassword kartoza/postgis
```


Change the POSTGRES_PASS=mydiaspassword to a secure password for the database.    

This will return with a long docker container ID. Check if all is well:
```sh
docker ps -a
CONTAINER ID        IMAGE             COMMAND                  CREATED             STATUS                   PORTS                    NAMES
75fc1f296c79        kartoza/postgis   "docker-entrypoint.s…"   9 seconds ago       Up 7 seconds             0.0.0.0:5432->5432/tcp   cbm_db
```
You need postgresql client tools to access the database. Make sure these match
the database version (which is 10 in the example case). For example, for the
command line interface on ubuntu:
```sh
sudo apt-get install postgresql-client-common postgresql-client-10
```
You can now connect to the database:
```sh
psql -h localhost -d postgres -U postgres

psql (10.12 (Ubuntu 10.12-0ubuntu0.18.04.1), server 10.7 (Debian 10.7-1.pgdg90+1))
Type "help" for help.

postgres=#
```
To enable the required postgis extensions for cbm run:

```sql
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_raster;
```

The postgis image may contain the TIGER data base per default (this is a often
    used in postgis training). We don't need it, so remove with:
```
postgres=# drop schema tiger cascade;
```
and exit and reconnect (you are now in schema *public*). List the default tables
in that schema:
```
postgres=# \q
psql -h localhost -d postgres -U postgres
postgres=# \d
               List of relations
 Schema |       Name        | Type  |  Owner   
--------+-------------------+-------+----------
 public | geography_columns | view  | postgres
 public | geometry_columns  | view  | postgres
 public | raster_columns    | view  | postgres
 public | raster_overviews  | view  | postgres
 public | spatial_ref_sys   | table | postgres
(5 rows)
```
These tables are required for the handling of spatial constructs (geometries,
    raster data, projection information).

### Optimizing

The main configuration settings for PostgreSQL are in a text file postgresql.conf
(/etc/postgresql/"version"/main/postgresql.conf). PostgreSQL ships with a basic
configuration tuned for wide compatibility rather than performance.

It is strongly recommended to configure the settings of the PostgreSQL database
based on your hardware configuration and application, suggested configurations can be found at
[PGTune](https://pgtune.leopard.in.ua/) or at [PGConfig](https://www.pgconfig.org/).

### Essential CbM tables

We now need to create the tables that we will use in the CbM context:

```sql
postgres=# create table public.aois (
    name text not null,
    wkb_geometry public.geometry(Polygon,4326)
);

postgres=# create table public.dias_catalogue (
    id serial,
    obstime timestamp without time zone not null,
    reference character varying(120) not null,
    sensor character(2) not null,
    card character(2) not null,
    status character varying(12) DEFAULT 'ingested'::character varying not null,
    footprint public.geometry(Polygon,4326)
);

postgres=# create table public.signatures_2020_s2 (
    pid int,
    obsid int,
    band char(2),
    count real,
    mean real,
    std real,
    min real,
    max real,
    p25 real,
    p50 real,
    p75 real
);
```

The table *aois* is an ancillary table in which one can define the geometries of
the areas of interest. The *dias_catalogue* is an essential table that stores
the metadata for the relevant Sentinel-1 and -2 image frames. The table
*aoi_s2_signatures* will store the time series extracts which will be linked to
the parcel ID (pid) from the to-be-uploaded parcel reference table for each
observation id (obsid) in the *dias_catalogue*.

Generate a new *aoi_s2_signatures* table for each aoi. This will typically be
needed for separate years, as parcel references change. For instance, a table
name like *nld2019_s2_signatures* would store all S2 records for the NL
reference for 2019.

For Sentinel-1 time series create the equivalent tables with *bs*
(backscattering coefficients) and *c6* (6-day coherence) instead of *s2* in the table name.


## Jupyter server

The Jupyter Server is an open source web application that allows to create and
share documents that contain live code, equations, visualizations and narrative
text. Uses include: data cleaning and transformation, numerical simulation,
statistical modeling, data visualization, machine learning, and much more
(https://jupyter.org). JupyterLab is the next-generation user interface for
Project Jupyter offering all the familiar building blocks of the classic Jupyter
Notebook (notebook, terminal, text editor, file browser, rich outputs, etc.) in
a flexible and powerful user interface. JupyterLab will eventually replace the
classic Jupyter Notebook (https://jupyterlab.readthedocs.io).

**Instaling DIAS Jupyter (Jupyter Notebook Tensorflow Python Stack for CbM)**

GTCAP cbm_jupyter docker image is based on the tensorflow-notebook of Jupyter
Notebook Scientific Python Stack and configured for Copernicus DIAS for CAP
“checks by monitoring” with all the requirements. This is the recommended way to
run a Jupyter server. Some DIAS providers may provide preinstalled Jupyter
environments as well.

**Run GTCAP Jupyter docker image**

To run a jupyter server with the default setup:
```sh
docker run --name cbm_jupyter -p 8888:8888 gtcap/cbm_jupyter
```

This will run the jupyter server on port '8888' and can be accessed from a web
browser on 'localhost:8888'.

To expose the jupyter server to port 80, change -p 8888:8888 to -p 80:8888, or
to any other port.

**More options**

To pull the docker image from [dockerhub](https://hub.docker.com/r/gtcap/cbm_jupyter) use:
```sh
docker pull gtcap/cbm_jupyter
```

To configure and access the current local directory within the jupyter server run:
```sh
docker run -it --privileged=true --user root -e NB_USER="$USER" -e NB_UID="$UID" -e NB_GID="$UID" -p 8888:8888 -v "$PWD":/home/"$USER" --name=cbm_jupyter gtcap/cbm_jupyter
```

To run the Jupyter server with a predefined token, add at the end of the command:
```sh
start-notebook.sh --NotebookApp.token='abcdefghijk1234567890'
```

**Note**: JupyterLab can be accessed by adding /lab at the url, instead of /tree (e.g. localhost/lab).

To run with enabled JupyterLab by default add -e JUPYTER_ENABLE_LAB=yes flag.

To run with enabled JupyterLab by default and mount the current directory run:
```sh
docker run -it --privileged=true --user root -e NB_USER="$USER" -e NB_UID="$UID" -e NB_GID="$UID" -e JUPYTER_ENABLE_LAB=yes -p 8888:8888 -v "$PWD":/home/"$USER" --name=jupyter4cbm gtcap/cbm_jupyter
```

For more options visit [jupyter-docker-stacks.readthedocs.io](https://jupyter-docker-stacks.readthedocs.io/en/latest)

To access jupyter server, open in the web browser the link with the token that is provided in the terminal (e.g. http://localhost/tree?token=abcdefghijk1234567890).

**Usage Instructions**

All Jupyter Notebooks files have the extension '.ipynb' and are identifiable by
the notebook icon next to their name.
To create a new notebook in JupyterLab, go to File -> New and select 'New Notebook'.
Notebooks currently running will have a green dot, while non-running ones will not.
To run a cell with a script, click on the run icon or press Shift+Enter

More information can be found at: https://jupyter.org/documentation


The token to access the jupyter server will be in the command line output:
```sh
[I 08:51:48.705 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
[C 08:51:48.708 NotebookApp]

   To access the notebook, open this file in a browser:
       file:///home/jovyan/.local/share/jupyter/runtime/nbserver-8-open.html
   Or copy and paste one of these URLs:
       http://abcd12345678:8888/?token=abcd12345678
    or http://127.0.0.1:8888/?token=abcd12345678
```

You will be able to access the Jupyter server on port 8888 (or any other port) on VM's public ip e.g.: **0.0.0.0:8888**
Copy the token from the command line and add it to the web interface.


### Build Jupyter image from source

To build cbm_jupyter docker image from source see the [Jupyter for cbm README.md file.](https://github.com/ec-jrc/cbm/tree/main/docker/cbm_jupyter#readme)

