**Please note that this work is in progress and can be subject to frequent changes**

![Image of European Commission](media/img/eu_science_hub.png)
## Joint Research Centre (JRC)
### Code examples for CAP “Checks by Monitoring”

**JRC Ispra Unit D5 Food security**
**Main authors: Guido Lemoine, Konstantinos Anastasakis**

As part of its ongoing move to simplify and modernise the EU’s Common Agricultural Policy (CAP), the European Commission has adopted new rules that will for the first time expressly allow a range of modern technologies to be used when carrying out checks for area-based CAP payments. This includes the possibility to completely replace physical checks on farms with a system of automated checks based on analysis of Earth observation data.

To facilitate and standardize access to earth observation data, the European Commission has funded the deployment of five cloud-based platforms. They provide centralized access to Copernicus data and information, as well as to processing tools. These platforms are known as the DIAS, or Data and Information Access Services.

The DIAS online platforms allow users to discover, manipulate, process and download Copernicus data and information. All DIAS platforms provide access to Copernicus Sentinel data, as well as to the information products from the six operational services of Copernicus, together with cloud-based tools (open source and/or on a pay-per-use basis).

Each of the five competitive platforms also provides access to additional commercial satellite or non-space data sets as well as premium offers in terms of support or priority. Thanks to a single access point for the entire Copernicus data and information, DIAS allows the users to develop and host their own applications in the cloud, while removing the need to download bulky files from several access points and process them locally.

![DIAS](https://www.copernicus.eu/sites/default/files/DIAS_0.jpg)


This repository (cbm) contains example scripts and documentation for the setup and usage of Copernicus DIAS for CAP “checks by monitoring”.

## Repository main structure

- Command line scripts for extraction routines (scripts/extraction) [Wiki 3.1.](https://github.com/ec-jrc/cbm/wiki/3.1.-Parcel-extraction.-Parcel-extraction-routines-for-use-in-non-interactive-workflow)
- Command line scripts for generation time series calendar (scripts/calandar_view) [Readme](https://github.com/ec-jrc/cbm/tree/main/scripts/calendar_view)
- Interactive notebook tools, inclouds QA and FOI tools (src/ipycbm/) [Wiki 6.2.](https://github.com/ec-jrc/cbm/wiki/6.2.-Jupyter-Notebooks.-Interactive-python-library-for-CbM-'ipycbm'.)
- RESTful API modules (stc/apicbm/) [Wiki 5.1.](https://github.com/ec-jrc/cbm/wiki/5.1.-RESTful-API.-Build-a-RESTful-API-with-Flask-for-CbM.)
- Docker image files for parallel extraction, jupyter notebooks server and RESTful API server (docker)
- Test scripts for a variety of functionalities (tests)

## Basic deployment Steps

Main steps that are required to run the examples.

- Installing environments.
    - Docker (containerization system)
    - Postgres database with PostGIS extension
    - Jupyter (interactive computing environment)


- Adding data to the database
    - Transfer parcels data to database
    - Transfer metadata and other required data


- Running code examples
    - Parcel extraction routines
    - Machine learning algorithms
    - Database backups


- Accessing and viewing results
    - Building RESTFul API
    - Using Jupyter Notebooks


< --- [Documentation](https://github.com/ec-jrc/cbm/wiki) --- >