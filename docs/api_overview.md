# Overview


JRC RESTful service example requests have predefined logical query names that need to be configured with a set parameters. All requests return a response as a JSON formatted dictionary. The values in this dictionary are always lists, i.e. even if the query produced no (empty list) or only 1 value.

If the query is not valid, and empty dictionary will be returned ({}).

In this page, we keep a list of actual queries and provide some use examples.


The server of JRC RESTful example currently runs from a CloudFerro server. The root URL of the RESTful server is https://cap.users.creodias.eu/query/
The URL requires authentication with a username and password (which has been provided to users upon request).

Query parameters are either required or optional. The order of parameters is not significant.

![Requests structure example](https://raw.githubusercontent.com/konanast/cbm_media/main/requests_structure_01.png)

**Current queries**
* Parcel information
    * parcelByLocation
    * parcelByID
* Parcel signatures time series
    * parcelTimeSeries
    * weatherTimeSeries
* Parcel sentinel images
    * chipByLocation
    * rawChipByLocation
    * rawChipByParcelID
* Parcel orthophotos
    * backgroundByLocation
    * backgroundByParcelID
* Parcels lists,
    * parcelPeers
    * parcelsByPolygon
