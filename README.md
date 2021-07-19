![Image of European Commission](https://raw.githubusercontent.com/ec-jrc/cbm/main/docs/img/eu_science_hub.png)
# Code examples for "CAP Checks by Monitoring” (CbM)
### Europdfshgdfshdfshg














adfgdsfgdsfg



adfg

adfg
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
