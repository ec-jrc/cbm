# Parcel information

**parcelByLocation - parcelByID**

Get parcel information for a geographical location or a by the parcel ID. The parcels in the annual declaration sets have unique IDs, but these are not consistent between years (also, the actual parcel geometries may have changed). Thus, a query is needed to "discover" which parcel ID is at a particular geographical coordinate. Agricultural parcels are supposed to be without overlap, a unique ID will normally be returned (this is, however, not a pre-condition).

Table: **parcelByLocation** Parameters

| Parameters  | Description   | Values | Default Value |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. |   |
| **year**     | year of parcels dataset   | e.g.: 2018, 2019   |   |
| **lon**         | longitude in decimal degrees  | e.g.: 6.31 |   |
| **lat**         | latitude in decimal degrees | e.g.: 52.34 |   |
| ptype     | parcels type   | b, g, m, atc. |   |
| withGeometry  | adds geometry   | True or False | False |


Table: **parcelByID** Parameters

| Parameters  | Description   | Example call | Values |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. |   |
| **year**     | year of parcels dataset   | e.g.: 2018, 2019 |   |
| **pid**     | parcel id   |   |   |
| ptype     | parcels type   | b, g, m, atc. |   |
| withGeometry  | adds geometry   | True or False | False |


returns

| Key            | Values  | Description   |
| ---------------| ------- | ----------- |
| pid     | a list of parcel ID     | Normally, only 1 ID should be returned. Empty list is no parcel found |
| cropname  | a list of crop names    | Placeholder for the crop name, mapped to the original parcel table |
| cropcode  | a list of crop code     | Placeholder for the crop code, mapped to the original parcel table |
| srid        | a list of EPSG codes  | Describes the projection for the parcel geometry |
| area        | a list of area  | The area, in square meters, of the parcel geometry |
| clon        | a list of centroid longitude  | The longitude of the parcel centroid |
| clat        | a list of centroid latitude  | The latitude of the parcel centroid |
|*geom*      | a list of geometries  | WKT representations of the parcel geometry |


**ptype** is used only in case there are different datasets dedicated to different type of analysis for the same year.
For example datasets dedicated to grazing use **g**, for mowing **m** etc.