![Image of European Commission](media/img/eu_science_hub.png)
# Code examples for "CAP Checks by Monitoring” (CbM)
### 2021 European Commission, Joint Research Center

**This work is in progress and may be subject to frequent changes**

The European Commission promoted the use of new technologies through many conferences and workshops and provided bilateral support to many paying agencies to use the Copernicus Sentinel data to check aid applications for some schemes and some groups of beneficiaries “checks by monitoring” (CbM).

CbM solutions developed by the European Commission's science and knowledge service, the Joint Research Center (JRC) are modular and built exclusively on open source components. Although the modules are tailored to use on a cloud infrastructure, such as DIAS, most can run on single platform solutions as well. Central to the modules is the use of a spatial database component for storage of PA parcel data sets, metadata storage and process control. Most processes read from the database, execute relevant tasks, and (may) store results back in the database.

A core concept in CbM is reduction. This is currently implemented primarily as statistics extraction, which can then be used in subsequent analytics. Examples modules that apply machine learning for outlier analysis have been developed. Other components are aimed at providing access to users that need analytical outputs for reporting, or data extraction, including image extracts, for further client-side detailed analysis.

This code repository with the documentation in the Wiki pages will get a copy of the CbM project up and running on an inhouse or cloud computing infrastructure for development and testing purposes.


## Prerequisites

To start CbM it is essential to have:

1. Computing resources
2. Copernicus Analysis Ready Data (CARD)
3. Valid parcel data


## Deployment

There are many steps that need to be completed for Checks by Monitoring. these steps require many different types of technical expertise.


- Setup server applications.
    - Docker (containerization system)
    - Postgres database with PostGIS extension
    - Jupyter (interactive computing environment)


- Adding data to the database.
    - Parcels data to database
    - CARD Metadata and other required data


- Running code examples.
    - Parcel extraction routines
    - Machine learning algorithms
    - Database backups


- Accessing and viewing results.
    - Building RESTFul API
    - Using Jupyter Notebooks


See the documentation in the [**Wiki Pages**](https://github.com/ec-jrc/cbm/wiki) for more details and setup instructions.


## CbM code repository structure

This repository (cbm) contains example scripts and documentation to get started with  “CAP checks by monitoring”. Some of them are:

- Command line scripts (scripts/) [Extraction routines](https://github.com/ec-jrc/cbm/wiki/3.1.-Parcel-extraction.-Parcel-extraction-routines-for-use-in-non-interactive-workflow), [TS calandar](https://github.com/ec-jrc/cbm/tree/main/scripts/calendar_view).
- Interactive notebook tools, inclouds QA and FOI tools (src/ipycbm/) [Wiki 6.1.](https://github.com/ec-jrc/cbm/wiki/6.1.-Jupyter-Notebooks.-Interactive-python-library-for-CbM-'ipycbm'.).
- Stand alone Jupyter Notebook examples (src/ipynb/) [Wiki 6.2.](https://github.com/ec-jrc/cbm/wiki/6.2.-Jupyter-Notebooks.-Examples'.).
- RESTful API modules (stc/apicbm/) [Wiki 5.1.](https://github.com/ec-jrc/cbm/wiki/5.1.-RESTful-API.-Build-a-RESTful-API-with-Flask-for-CbM.).
- Docker image files for parallel extraction, jupyter notebooks server and RESTful API server (docker/).
- Test scripts for testing a variety of functionalities (tests/).


## Contributing

Please read [creating-a-pull-request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request) for details on the process for submitting pull requests to us.


## Authors

* **Guido Lemoine** - *Initial work* - [glemoine62](https://github.com/glemoine62)
* **Konstantinos Anastasakis** - *Initial work* - [konanast](https://github.com/konanast)

See also the list of [contributors](https://github.com/ec-jrc/cbm/contributors) who participated in this project.

## License

This project is licensed under the [3-Clause BSD](https://opensource.org/licenses/BSD-3-Clause) License - see the [LICENSE](LICENSE) file for details
