![Image of European Commission](https://raw.githubusercontent.com/ec-jrc/cbm/main/docs/img/eu_science_hub.png)
# Code examples for "CAP Checks by Monitoring” (CbM)
### European Commission, Joint Research Center

**This work is in progress and may be subject to frequent changes**

The European Commission promotes the use of new technologies in the context of
the Common Agricultural Policy (CAP) and the Integrated Administration and
Control Systems (IACS) which are managed by the European Union Member States.
In 2018, "Checks by Monitoring" (CbM) were introduced for area-based support
schemes. The EU  Paying Agencies (PA) who adapt CbM will migrate to the use of
Copernicus Sentinel data to check aid applications.



## Prerequisites

To start CbM it is essential to have:

1. Computing resources
2. Copernicus Analysis Ready Data (CARD)
3. Valid agricultural parcel data (FOI compliant)


## Deployment

There are several steps to set up the core components for Checks by Monitoring.
These steps require different types of technical expertise. 

- Install server applications
    - Docker (containerization system)
    - Postgres database with PostGIS extension
    - Jupyter (interactive analysis and visualization environment)


- Adding data to the database
    - Parcels data to database
    - CARD Metadata and other required data


- Running code examples
    - Parcel extraction routines
    - Machine learning algorithms
    - Database backups
    - Analytical routines (e.g. market detection)


- Accessing and viewing results
    - Building RESTFul API
    - Using Jupyter Notebooks


See the documentation at [jrc-cbm.readthedocs.io](https://jrc-cbm.readthedocs.io)
for more details and setup instructions.


## Structure

This repository (cbm) contains example scripts and documentation to get started
with  CbM, includes:

- api - Modules to build a RESTful API for CbM
- cbm: Python library
    - card2db : Transfer metadata from the DIAS catalog
    - extract : Parcel extraction routines
    - foi : FOI modules
    - get : Download data to local directory
    - ipycbm : Interactive notebook widgets
    - report : Export reports
- docker/: Docker image files for:
    - [dias_py](https://hub.docker.com/r/glemoine62/dias_py) : Parallel extraction
    - [cbm_jupyter](https://hub.docker.com/r/gtcap/cbm_jupyter) : Jupyter notebooks server
    - [cbm_api](https://hub.docker.com/r/gtcap/cbm_api) : RESTful API server
- docs/: Documentation pages (see [jrc-cbm.readthedocs.io](https://jrc-cbm.readthedocs.io))
- ipynb/: Jupyter Notebook examples
- scripts/: Python scripts for:
    - extraction : Parcel extraction routines
    - calendar_view : Time series calendar view
- tests/: Test scripts for testing a variety of functionalities.

See the documentation at [jrc-cbm.readthedocs.io](https://jrc-cbm.readthedocs.io) for more details.


## Contributing

Please read ["creating-a-pull-request"](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request)
for details on the process for submitting pull requests.


## Authors

* **Guido Lemoine** - *Initial work* - [glemoine62](https://github.com/glemoine62)
* **Konstantinos Anastasakis** - *Initial work* - [konanast](https://github.com/konanast)

See also the list of [contributors](https://github.com/ec-jrc/cbm/contributors)
who participated in this project.


## License

This project is licensed under the [3-Clause BSD](https://opensource.org/licenses/BSD-3-Clause)
License - see the [LICENSE](LICENSE) file for details.


Copyright (c) 2021, [European Commission](https://ec.europa.eu/),
Joint Research Centre. All rights reserved.
