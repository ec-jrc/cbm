# Data preparation

**Data preparation**

## Adding shapefiles (.shp) to PostGIS database

More information at: http://postgis.net/documentation/

To add a shapefile to a postgis database using ogr2ogr, do the following:

    sudo apt-get install gdal-bin

to install the GDAL binaries, which is highly recommended also for other geospatial data analysis tools. You can also use ogr2ogr to import from other formats (e.g. GML, GeoJSON, etc.).

    ogr2ogr -f "PostgreSQL" PG:"host=localhost port=5432 user=postgres dbname=postgres" \
    -nln "roi_YYYY" -nlt PROMOTE_TO_MULTI parcels_2018.shp
    
This will import the shape file into the table *roi_YYYY* (choose a recognisable roi name and replace YYYY with the year of interest). The option *-nlt PROMOTE_TO_MULTI* may not be needed if all shape features are single polygons. If (some) features fail to upload (e.g. due to corrupt geometries), add the option *-skipfailures*, but check the completeness of the uploaded table afterwards.

See

    ogr2ogr --help
    
for more information.

The table *roi_YYYY* will be spatially indexed after upload, which significantly speeds up spatial querying.

You are now ready to [start transfering metadata from the catalogue](https://jrc-cbm.readthedocs.io/en/latest/data_preparation.html#transfer-metadata-from-the-dias-catalog) and then [run extracts](https://jrc-cbm.readthedocs.io/en/latest/parcel_extraction.html).


## Transfer metadata from the DIAS catalog

Each DIAS maintains a catalog of the Level 1 and Level 2 CARD data sets available in the S3 store. Even with the use of standard catalog APIs (e.g. OpenSearch), the actual metadata served by the catalog may contain different, or differently named, attributes. Thus, in order to minimize portability issues, we implement a metadata transfer step, which makes metadata available in a single, consistent, database table __dias_catalogue__ across the various DIAS instances.

As is the case for the later parcel extraction stage, metadata transfers can be done in (1) burst mode, e.g. for a long time series of processed CARD data for a new area on interest or (2) in update mode, for newly generated CARD data set, e.g. on a daily basis. Since database transfers are not particularly demanding on compute resources, there is no need for parallelization and both modes can run on a single VM. "Burst mode" can be run interactively from the command line interface (terminal) or as a notebook, while "update mode" can run as a scheduled python task in cron.


### OpenSearch compliant catalogs (CREODIAS, MUNDI)

Both CREODIAS and MUNDI provide online catalogs that implement the [OpenSearch](https://github.com/dewitt/opensearch) standard. This is the same standard as implemented by the [Copernicus Open Access Hub](https://scihub.copernicus.eu/). In short, this standard ensures that the catalog can be queried via so-called REST requests, typically with standard request parameters to define the area of interest and search period, product type and some other parameters (e.g. platform, sensor, etc.). The response is usually in a well-known parseable format, such as JSON or XML. It is relatively straightforward to build graphical user interfaces (GUI) to capture the request parameters interactively and display the response results (e.g. [CREODIAS FINDER](https://finder.creodias.eu/), [MUNDI Web Services](https://mundiwebservices.com/geodata/)). More importantly, though, the OpenSearch standard allows to capture search results in scripts as well, so that catalog updates can be automatically processed.

The transfer of metadata consists of the following steps:
- Build up the OpenSearch query for the area of interest, the search start and end date and the product type;
- Fire off the query to the catalog server
- Check whether the response type is as expected (XML in our case) and if so
- Parse the relevant attributes from the XML response and reformat to __dias_catalogue__ compatible table fields (e.g. the gml geometry for the CARD image footprint needs to become a WKT polygon)
- Insert each record into the __dias_catalogue__ table (duplicate records will fail to insert)

Batch processing is then simply scheduled to run overnight for a fixed incremental period (e.g. yesterday to today).

### Database catalog (SOBLOO)

SOBLOO maintains a dedicated database for processed CARD data, on a project-by-project basis. While this is a second-best solution, it is relatively straightforward to use, as we only need to transfer records between databases. All metadata is stored in a single table __datas__, so all relevant CARD metadata records can be transferred, for the area of interest, with a single spatial query. 

The transfer is modified as follows:
- Determine the database connection details for the SOBLOO __datas__ table (provided with the SOBLOO account)
- Build a spatial query for the area of interest, the search start and end date
- Fire off the query to the SOBLOO database
- Parse the relevant attributes in the query response and reformat to __dias_catalogue__ compatible table fields
- (Note that the geometries in the __datas__ table have their lon, lat coordinates flipped. We use the postgis function __ST_FlipCoordinates()__ to correct this).
- Insert each record into the __dias_catalogue__ table (duplicate records will fail to insert)


## Benchmarking data formats for fast image processing

(Work in progress)

Problem statement: for fast image processing and visualization, the image data organization play an essential role. Whereas many standard formats exist, there is still little information on how formats relate to "typical" timing of standard image processing and visualization needs. This is further complicated by the fact that image processing is now moving from single platform to cloud based solutions, and from limited selections of locally stored image data to global coverages of full data archives. Thus distributed data storage needs to be combined with massively parallel execution of processing code, and render meaningful results in increasingly demanding analytics and visualization workflow.

Pre-conditions

Data formats/solutions need to adhere to a minimum number of conditions:

- No changes to the original resolution of the source data: the new format shall neither change spatial resolution (pixel spacing), nor radiometric resolution (drop bands), nor data precision (bit depth of the image bands). It should also keep the original projection. In other words, there is full reproducability between the original data and the newly formatted data.

- The format shall ensure equal access delays to any arbitrary sub-part of the image.

- The format must support use on local storage (e.g. HDD, SDD) and distributed storage (e.g. S3 cloud storage).


Minimum processing requirements:

- Seamless recomposition of processing across image sub parts, without introduction of border artefacts

- Support standard projections "on-the-fly"

Qualified solutions:

- Tiled GeoTIFF or its current Cloud Optimized GeoTIFF variant, which extends GeoTIFF with upsampled overviews. In a tiled GeoTIFF, image sub-parts are indexed inside the GeoTIFF header information.

- Tiled formats: the image is broken up in smaller tiles and either indexed by an explicit metadata format (e.g. VRT) or by an implicit tile file naming. Individual tiles are stored with a common format (e.g. GeoTIFF). Tiled formats may also store upsampled overviews, e.g. in a hierarchical file directory structure ordered according to overview (zoom) level.

We limit ourselves to full resolution, so we will not deal with upsampled overviews (for now) 

Disqualified solutions:

- Data cubes are already out, because they prescribe resampling to a common grid, which does not adhere to the first pre-condition, and does not provide a globally consistent solution.

Benchmark

- Tiled GeoTIFF: single file, tile indexing in internal LUT, many standard tools read/write GeoTIFF;
- Tiled composites: many tiles, in directory structure, composed implicit index or through companion metadata file (e.g. VRT), possibly benefit from ZIP compression and archiving. VRT with virtual file system access protocols emerging standard.

The benchmark test is to select and arbitrary sized image subset for 100 random locations inside the image bounds. Mean and standard deviation across image bands are calculated to check data consistency. Tests to be run with single and multiple image bands.
