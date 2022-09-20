# Parcel peers

## parcelPeers

Get the parcel "peers" for a known parcel ID, i.e. parcels with the same crop type as the reference within a certain distance. This can be useful for checking the relative behavior of a parcel against its nearest neighbors (with the use of *parcelTimeSeries*)

| Parameters  | Description   | Values | Default Value |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. |   |
| **year**     | year of parcels dataset   | e.g.: 2018, 2019 |   |
| **pid**     | parcel id   |   |   |
| ptype     | parcels dedicated to different analyses   | b, g, m, atc. |   |
| distance     | maximum distance to search around parcel with **pid**   | < 5000.0 atc. | 1000.0 |
| max  | maximum number of peers to return   | < 100 | 10 |


Example:
https://cap.users.creodias.eu/query/parcelPeers?parcels=ms&year=2020&pid=315141

returns

| Key            | Values  | Description   |
| ---------------| ------- | ----------- |
| pid     | a list of parcel IDs     |   |
| distance        | a list of distances  | In ascending order |


## parcelStatsPeers

Get the parcel "peers" for a known parcel ID, i.e. parcels with the same crop type as the reference within a certain distance. This can be useful for checking the relative behavior of a parcel against its nearest neighbors (with the use of *parcelTimeSeries*)

| Parameters  | Description   | Values | Default Value |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. |   |
| **year**     | year of parcels dataset   | e.g.: 2018, 2019 |   |
| ptype     | parcels dedicated to different analyses   | b, g, m, atc. |   |
| band     | Sentinel 1 or 2 band   | B02, B03, B04, B05, B08, B11, VVc, VVb |   |
| values     | a specific value or value range e.g.: '100-200'.   | b, g, m, atc. |   |
| stype     | the stats type | mean, max, min, p25, p50, p75 | mean |
| max  | maximum number of peers to return   | - | 100 |


Example:
https://cap.users.creodias.eu/query/parcelStatsPeers?aoi=at&ptype=m&year=2020&start_date=2020-05-01&end_date=2020-06-01&band=B08&values=10000-11000

returns

| Key            | Values  | Description   |
| ---------------| ------- | ----------- |
| pids     | a list of parcel IDs     |   |


## parcelsByPolygon

Get a list of parcels within a given polygon.

| Parameters  | Description   | Values | Default Value |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. |   |
| **year**     | year of parcels dataset   | e.g.: 2018, 2019 |   |
| **pid**     | parcel id   |   |   |
| ptype     | parcels dedicated to different analyses  | b, g, m, atc. |   |
| polygon     | polygon coordinates   |   |   |
| max  | maximum number of parcels to return   | < 100 | 10 |

Example:
https://cap.users.creodias.eu/query/parcelsByPolygon?aoi=AA&year=2020&polygon=[polygon_coordinates]

returns

| Key            | Values  | Description   |
| ---------------| ------- | ----------- |
| pids     | a list of parcel IDs     |   |


**ptype** is used only in case there are different datasets dedicated to different type of analysis for the same year.
For example datasets dedicated to grazing use **g**, for mowing **m** etc.