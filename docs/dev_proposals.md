# CbM Enhancement Proposals

## Test Arrow-IPC
Check Arrow-IPC as alternative to PostgreSQL data base table for time series storage.

Would allow easier transfer of large data sets, but needs to be as performant as clustered indexed db.


## Terrain Correction
Introduce Radiometric Terrain Correction in CARD-BS processing.

RTC normalizes for SAR viewing configuration, allowing better comparison of ASC and DESC and multiple orbit data.


## S2 Multi-band
Implemented multi-band and index extraction for Sentinel-2 L2A.

Significant for marker generation. Database size may become an issue, thus, this is strictly done for cloud free parcels only.


## Dask tests
Test dask and decide whether it can replace (some of) the docker based parallelisation.

Dask allows for parallel processing of large and deep image stacks, e.g. for extraction and local image processing tasks (e.g. segmentation).


## ML Revision
Revisit the 2018 machine learning code (DNN in tensorflow) and update with latest best-practice.

The old code needs to be revisited and implemented as a "crop" marker. Documentation to be completed. Best to start with S1 signatures.


## RESTful meteo
Create a RESTful service that accesses open meteorological "now cast" data (e.g. ERA5, GFS).

Interpretation of time series often requires temperature and precipitation data to understand spurious trends.
