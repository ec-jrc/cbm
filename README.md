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

CbM applies to the complete territory of the Member States and makes use of
continuously updated data streams from the Sentinel-1 and -2 sensors. This
implies the use of Big Data Analytics solutions, that require parallel
processing compute infrastructure, such as cloud services. In support to CbM
implementation the European Commission's science and knowledge service, the
Joint Research Center (JRC), demonstrates compute solutions that are modular
and built exclusively on open source components. Although the modules are
tailored to use on a cloud infrastructure, such as Copernicus DIAS (Data and
Information Access Services), most can run on single platform solutions as well.
Central to the modules is the use of a spatial database component for storage of
PA parcel data sets, metadata storage and process control. Most processes read
from the database, execute relevant tasks, and (may) store results back in the
database.

A core concept in CbM is reduction. This is currently implemented primarily as
statistics extraction, which can then be used in subsequent analytics. Examples
modules that apply machine learning for outlier analysis have been developed.
Other components are aimed at providing access to users that need analytical
outputs for reporting, or data extraction, including image extracts, for further
client-side detailed analysis.

This code repository provides access to the CbM project code, which can be set
up, configured and run on an in-house or cloud computing infrastructure for
development and testing purposes. The modular approach is documented in the Wiki
pages. 


## Prerequisites

To start CbM it is essential to have:

1. Computing resources
2. Copernicus Analysis Ready Data (CARD)
3. Valid agricultural parcel data (FOI compliant)


## Deployment

There are several steps to set up the core components for Checks by Monitoring.
These steps require different types of technical expertise. 

- Setup server applications
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

- scripts/: Python scripts for:
    - Parcel extraction routines
    - Time series Calendar view
- docs/: Documentation pages (see [jrc-cbm.readthedocs.io](https://jrc-cbm.readthedocs.io))
- cbm: Python library for Checks by Monitoring
    - api - RESTful API modules (cbm/apicbm/)
    - card2db - Transfer metadata from the DIAS catalog
    - extraction - Parcel extraction routines
    - foi - FOI module
    - ipycbm - Interactive notebook widgets for:
        - FOI
        - QA
        - Extraction
        - Downloading data
        - Viewing data
- ipynb/: Jupyter Notebook examples
- docker/: Docker image files for:
    - [dias_py](https://hub.docker.com/r/glemoine62/dias_py)/: Parallel extraction
    - [cbm_jupyter](https://hub.docker.com/r/gtcap/cbm_jupyter)/: Jupyter notebooks server
    - [cbm_api](https://hub.docker.com/r/gtcap/cbm_api)/: RESTful API server
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