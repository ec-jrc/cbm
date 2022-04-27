# Parcel orthophotos


**backgroundByLocation - backgroundByParcelID**

It is often handy to have a high resolution overview of the parcel situation. A (globally) useful set are the Google and Bing (or Virtual Earth) background image sets.

This query generates an extract from either Google or Bing. It uses the WMTS standard to grab and compose, which makes it fast (does not depend on DIAS S3 store).

Currently, parameter values can be as follows:

Table: **backgroundByLocation** Parameters

| Parameters  | Description   | Values | Default Value |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **lon**         | longitude in decimal degrees  | e.g.: 6.31 | - |
| **lat**         | latitude in decimal degrees | e.g.: 52.34 | - |
| chipsize     | size of the chip in pixels   | < 1280 | 256 |
| extend  | size of the chip in meters | - | 256 |
| tms  | tile map server | Google, Bing, OSM or Orthophotos | Google |
| iformat  | image format | tif or png | png |


Table: **backgroundByParcelID** Parameters

| Parameters  | Description   | Example call | Values |
| ----------- | --------------------- | ------------------------ |------------------------ |
| **aoi** | Area of Interest (Member state or region code) | e.g.: at, pt, ie, etc. | - |
| **year**     | year of parcels dataset   | e.g.: 2018, 2019 | - |
| **pid**     | parcel id   |   | - |
| ptype     | parcels type   | b, g, m, atc. | - |
| chipsize     | size of the chip in pixels   | < 1280 | 256 |
| extend  | size of the chip in meters | - | 256 |
| tms  | tile map server | Google, Bing, OSM or MS Orthophotos | Google |
| iformat  | image format | tif or png | png |
| withGeometry  | show parcel polygon overlay on if iformat=png | True or False | False |

Examples:
- Example 1, returns a background google earth image of a selected location,
https://cap.users.creodias.eu//query/backgroundByLocation?lon=1.333370&lat=41.557789&chipsize=256&extend=500&tms=es2020&iformat=png
- Example 2, returns a background google earth image of a selected parcel,
https://cap.users.creodias.eu/query/backgroundByParcelId?aoi=ms&year=2020&pid=123&chipsize=256&extend=512&iformat=png

returns

An HTML page that displays the selected chip as a PNG tile. Generates a GeoTIFF as well, for use in rasterio processing.
