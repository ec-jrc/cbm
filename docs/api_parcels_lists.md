# Parcels lists

## parcelPeers

Get the parcel "peers" for a known parcel ID, i.e. parcels with the same crop type as the reference within a certain distance. This can be useful for checking the relative behavior of a parcel against its nearest neighbors (with the use of *parcelTimeSeries*)

| Parameters  | Description   | Values | Default Value |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. |   |
| **year**     | year of parcels dataset   | e.g.: 2018, 2019 |   |
| **pid**     | parcel id   |   |   |
| ptype     | parcels type   | b, g, m, atc. |   |
| distance     | maximum distance to search around parcel with **pid**   | < 5000.0 atc. | 1000.0 |
| max  | maximum number of peers to return   | < 100 | 10 |


Example:
https://cap.users.creodias.eu/query/parcelPeers?parcels=ms&year=2020&pid=315141

returns

| Key            | Values  | Description   |
| ---------------| ------- | ----------- |
| pid     | a list of parcel IDs     |   |
| distance        | a list of distances  | In ascending order |


## parcelsByPolygon

Get a list of parcels within a given polygon.

| Parameters  | Description   | Values | Default Value |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. |   |
| **year**     | year of parcels dataset   | e.g.: 2018, 2019 |   |
| **pid**     | parcel id   |   |   |
| ptype     | parcels type   | b, g, m, atc. |   |
| polygon     | polygon coordinates   |   |   |
| max  | maximum number of parcels to return   | < 100 | 10 |

Example:
https://cap.users.creodias.eu/query/parcelsByPolygon?aoi=AA&year=2020&polygon=[polygon_coordinates]

returns

a list of parcel IDs
