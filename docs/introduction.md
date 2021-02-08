# Introduction

**DIAS for CAP Checks by Monitoring**


The “Data and Information Access Systems” (DIAS) are the European Union’s Copernicus program element funding the deployment of five cloud-based platforms  providing  centralised  access  to  Copernicus  data  and  information,  as  well as to processing tools. Four DIAS instances (CREODIAS, MUNDI, ONDA and SOBLOO), managed under contract with the European Space Agency (ESA), became operational in 2018 and provide access, amongst others, to high resolution Sentinel-1 and Sentinel-2. The fifth is managed by EUMETSAT, and became operational in late 2019. 
![DIAS](https://www.copernicus.eu/sites/default/files/DIAS_0.jpg)

In support to Member States (MS) opting for “CAP checks by monitoring” (CAP-CbM) starting in 2019, DIAS accounts are provided to demonstrate the processing requirements for Sentinel-1 and -2 data. Each DIAS implements access to the full archive of Sentinel data [for Europe] and provides computing resources in a cloud environment, which are closely coupled with the data store. Thus, processing to the required level of analysis and further data extraction and analysis can be run on the DIAS cloud platforms. The obvious advantage of such a set-up is in:
* the proximity of the processing to the massive data volumes (i.e. no need for downloads) 
* the possibility to scale processing to large data volume needs and complex analysis (i.e. without the need for extensive local hardware and software maintenance)
* and the possibility to create modular processing pipelines, that are tailored to the specific needs of CbM and the technical capacities of the end user.

 
The DIAS contracts finance the establishment and maintenance of this core computing and storage infrastructure. The actual DIAS use by end users, such as MS Paying Agencies (PA), or any other public or private user, is managed through DIAS accounts, i.e. subscription services that are costed on the basis of actual use of computing resources (e.g. CPU time, data transfer, additional storage requirements, etc.).
 
In the context of CAP CbM, DG AGRI together with DG DEFIS (the Copernicus program managers, previously known as DG GROW) have decided to fund the DIAS onboarding of Member State PA’s in 2019 and 2020 through ESA work orders. In 2019, the work orders were structured in 3 phases: (1) technical readiness review (2) onboarding MS PA on one of the DIAS instances and (3) operational use of the DIAS in the 2019 CAP CbM. In 2020, the first 2 phases are no longer required, and, based on the experience built up in 2019, onboarding MS can jump directly into the operational phase.

The work orders are supported, on a technical level, by DG JRC with the definition of high level requirements, technical adequacy review, methodological assistance for the generation of CARD (see next section) and the definition and initial demonstration of CAP CbM relevant functionalities.


## Copernicus Application Ready Data (CARD)

One essential step, common to all PAs, is the generation of Copernicus Application (or Analysis) Ready Data (CARD), which, as a minimum, includes georeferenced, calibrated sensor data (Level 2). Sentinel-1 and -2 data are, by default, delivered by ESA through the Copernicus Hub as Level 1 data. Since March 2018, Level 2 (atmospherically corrected) Sentinel-2 data is also made available. For Sentinel-1, this is not the case (yet).

In the context of the CAP CbM work orders, the DIAS are required to make Level 2 CARD available as follows:

- Sentinel-2 Level 2 (CARD-S2): copy from ESA hub when available, generate with SEN2COR otherwise; 
- Sentinel-1 geocoded backscattering coefficients (CARD-BS): process from Level 1 GRD with s1tbx using a common graph (processing recipe); 
- Sentinel-1 geocoded coherence (CARD-COH6): process 6-day Level 1 SLC pairs with s1tbx using a common graph;

This processing set-up has been tested in Phase 1 of the work order. For each PA, the DIAS can run these processes by default in 2 modes: (1) “burst” mode at the start, i.e. all data for 2017 and 2018 (and eventually 2016) will be copied or processed in a purposed cluster, and (2) “batch” mode for the current season, processing new acquisitions that are ingested in the ESA hub and transferred to the DIAS.

In practice this means that a PA user can assume that CARD data is available for further analysis, within a time delay after Sentinel acquisition that spans the latencies in ESA hub ingestion, transfer and processing by the DIAS and ingestion into the DIAS catalogue (usually after a few hours, typically within 24 hours).

To get an idea of the data and processing volume, CARD processing for Denmark (approx. 50,000 sqkm) was tested on the various DIAS instances for comparison. For 2018, this required the transfer and processing of 1720 Sentinel-1 GRD, 1690 Sentinel-1 SLC and 4085 Sentinel-2 images, with an approximate input volume of 18 TB. Each of the DIAS were able to collect and process all data sets with common recipes that were provided by JRC and tested and revised in the initial phase. It was evident that DIAS instances are capable of processing the 2018 volume to CARD data within several days, depending on cluster configuration and allocated VM resources. Most DIAS instances now provide CARD generation as a backend service.

## Time series extraction

The availability of Sentinel CARD ensures that the spectral and temporal information (i.e. time series) for a geographical position, e.g. as delineated by an agricultural parcel, can be extracted consistently. In CbM, time series play an essential role in marker generation. Although it is technically feasible to generate a CARD time series on demand, it is often convenient to extract large sets of parcels, for pre-selected bands, in a batch process. DIAS use is specifically tailored to these kind of tasks, since extraction is typically a massively parallel processing step that can benefit from the use of multiple machines.
Technical details are given in [the documentation page on parcel extraction](https://jrc-cbm.readthedocs.io/en/latest/parcel_extraction.html)

Time series extraction fits in the overall concept of "reduction", which is an essential element of CbM. Since CbM covers 100% of the territory, it needs to be supported by smart, automated analytics that filter out the most relevant anomalies quickly and consistently. Reduction generates the signal statistics that can be used in such analytics, e.g. to support outlier identification, detection of heterogeneity, marker generation, etc. At all times, the direct link to the CARD inputs is maintained, which means that the source of the particular indicator can be (automatically) retrieved, e.g. for more detailed inspection.

Extracted time series are stored in a spatial postgresql data base.


## Data access and analytics

A DIAS platform provides several options to access and analyse the data it stores. The most direct way is to provide access to a DIAS account that has the credentials to access the various data sets (e.g. the S3 store where Sentinel CARD is stored, the data base with extracted time series, etc.). A DIAS account user may be given privileges to generate and centrally store other kinds of reductions that could benefit a wider range of end users. For instance, an expert user applies machine learning algorithms to the extracted time series and writes the results into the data base, so that others can use these in outlier analysis. 

For a wider range of users, who do not necessary need a DIAS account, the DIAS platform can provide access to data via server interfaces. These servers can range from:

* direct access to the data base server, e.g. for use in QGIS or data analysis scripts;
* access to data via RESTful servers, which is useful to serve standard queries and abstract more complex tasks;
* a Jupyter Hub server, configured to hide the intrinsic access protocols, and supporting interactive scripting and data visualization;
* A mixture of those (e.g. a Jupyter notebook running on the Jupyter Hub, which uses a mix of direct access to the data base and RESTful services)

An essential character of the RESTful services is that they follow standard calling conventions, which allow their use both in interactive testing and scriptable machine access. RESTful services are further described in [the documentation pages on RESTful service use](https://jrc-cbm.readthedocs.io/en/latest/api_ts.html) and subsequent pages. 

An alternative use pattern would be to transfer the time series data base (eventually including other reductions) to a dedicated server set up outside the DIAS cloud infrastructure, for instance, into the PA's ICT infrastructure. RESTful services running on DIAS can then be used to maintain access to the DIAS CARD data store to support on demand generation of image fragments, for instance.

## Differences with SEN4CAP

There are important differences between the modular CbM DIAS set up and the SEN4CAP approach. The key difference is the modularity, i.e. CbM DIAS users can decide which modules are essential in their use context and configure those to suit their needs. CbM modules are NOT tailored to generate crop map products. In fact, the philosophy behind CbM is that PAs already have the best possible crop map as soon as the GSAA parcel declarations are filed. The traffic light approach in CbM prescribes that methods are needed to quickly shift through these declarations to confirm these against the relevant schemes with the best possible evidence derived from the Sentinel CARD (switch to 'green'). The clear aim is again "reduction", i.e. focus effort on those cases ('yellow') for which further evidence is required, either from additional CARD observations in time or from other sources (e.g. geotagged imagery, other evidence). A modular set up that supports a wide range of, expandable, analytical tools is best suited for such a dynamic, automated evaluation framework. 


## Expertise required

Given the above DIAS and processing particulars, a profile for PA expertise required for DIAS onboarding can be defined as follows:

- Strong skills in linux system configuration and administration;
- Strong skills in the use of relevant open source components for EO image processing and geospatial data analysis (as a minimum: good working knowledge of PostgreSQL/Postgis, GDAL, web map services);
- Strong skills in programming and scripting (preferably python) and relevant data processing libraries;
- Working knowledge of cloud or cluster computing solutions (openstack, docker, docker swarm, kubernetes);
- Working knowledge of Sentinel data specifications, processing toolkits, and use case requirements (in agriculture);
- Good English communication skills to explain technical issues to DIAS support, JRC;