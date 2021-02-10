# Data analytics

**Using the RESTful services to support data analytics for CbM**

On this page, we work out a case study for a practical CbM case. For a limited area of interest, we select all parcel IDs.
For each of the parcel IDs, we first check the extracted signature statistics. Given some criteria, we sort on expected heterogeniety of the parcels. This is calculated from the signature statistics. Heterogeniety must be meaningful with respect to the crop stage for which we expect a homogenous parcel to have minimum variability.

For the top 10 heterogeneous parcels, we then extract chips for further testing. 

## parcel selection

To illustrate that we are dealing with a realistic scenario, we select an arbitrary area in NRW in 2018, and do a direct database extraction of all parcels in a 5000x5000 sqm square buffer around a coordinate of interest. We do not have a dedicated RESTful service for this, but in reality, the parcel IDs should come from the existing registry of the PA.


```
select ogc_fid, mon10_cr_2, st_area(wkb_geometry)/10000.0 as area, st_x(st_transform(st_centroid(wkb_geometry), 4326)) as clon, st_y(st_transform(st_centroid(wkb_geometry), 4326)) as clat from nrw2018 where st_intersects(wkb_geometry, st_envelope(st_buffer(st_transform(st_geomfromtext('POINT(6.365 51.0198)', 4326), 25832), 2500))) order by st_area(wkb_geometry) desc; 
```

this produces a list of 840 parcel IDs, sorted by descending parcel area size, which ranges from 30.6 to 0.013 ha. Only 39 parcels are smaller than 0.2 ha, so "small parcel occurrence" is not a very significant issue. In fact, it helps us appreciate the added value of our heterogeniety analysis: detecting a non-compliant subdivide of several hectares in any of the larger parcels is more significant that checking all the "small parcels" together **(focus!)**


## time series statistics

For each parcel ID, we can now collect the S2 (or S1) time series. In both, we assume heterogeneity is expressed in:

* a larger than "normal" standard deviation (or stdev ratio over mean) of the signal values 
* a skewed distribution of the signal values in the parcel histogram
* at the phenology phase at which we expect a full crop cover
* a clustering of values in distinct subsegments

We deal with clustering in the next section, because we can consider it as a post-processing step to confirm the findings in time series statistics. This is the main reason why the JRC DIAS implementation includes automated parcel extraction routines: most of the relevant heterogeniety information is in the statistical extracts. 
More complex analysis and visual inspection of chips is only needed to resolve the less obvious cases **(cost!)**

The steps outlined above are already served by the existing RESTful routines, in particular the _parcelTimeSeries_ routine. The challenge is to define what is a "normal" standard deviation of the signal and at which phenology stage (i.e. time window) we want to test. Obviously, the latter is depended on the crop type, e.g. we expect winter crops to have a different timing than summer crops. To a lesser extent, we need be aware of heterogeniety effects that may occur is crop covers (e.g. alfalfa, grass due to partial mowing).











## histogram analysis, clustering

## ...