# DIAS for CAP Checks by Monitoring

The Joint Research Centre (JRC) Checks by Monitoring (CbM) is as a proof of concept that demonstrates the feasibility of agricultural monitoring systems for the common agricultural policy (CAP) of the European Union (EU) based on Copernicus [Sentinel](https://sentinels.copernicus.eu/) data and on cloud-based infrastructures, particularly the [Data and Information Access Systems (DIAS)](https://www.copernicus.eu/en/access-data/dias). Its goal is to help Paying Agencies (PA) of Member States (MS) and their technological partners to get started with CbM and to define a set of best practices in context of the [Integrated Administration and Control Systems (IACS)](https://ec.europa.eu/info/food-farming-fisheries/key-policies/common-agricultural-policy/financing-cap/financial-assurance/managing-payments_en). The same approach can potentially be applied to the area monitoring system (AMS) of the future CAP.  

In this section of the [Guidance and Tools for CAP (GTCAP) WEBSITE](https://marswiki.jrc.ec.europa.eu/) we present an overview of JRC CbM. The detailed description of methods and tools is provided in the [JRC CbM TECHNICAL DOCUMENTATION](https://jrc-cbm.readthedocs.io) and the code is made available as open source in [JRC CbM GitHub REPOSITORY](https://github.com/ec-jrc/cbm)..  

The general documentation is organized in four components: one for the general description of the system and three for the main groups of tasks.

1. **[Overview of the system architecture](dias4cbm_architecture.md)**: overview of the cloud-based CbM elements. Target users: all.
2. **[System development](dias4cbm_setup.md)**: manuals to set up the software and hardware infrastructure (backend). Target users: system administrators.
3. **[Data analysis](dias4cbm_analysis.md)**: tutorials to create methods and tools to detect the agricultural events of interest through specific interfaces for data analysis (frontend/backend). Target users: analysts.
4. **[Data use](dias4cbm_use.md)**: demos to apply the system's outputs to the control of farmers' declarations using simple graphical interfaces (frontend). Target users: final users/decision makers.

---

## DIAS and CbM
### DIAS, Sentinel and (C)ARD
The **DIAS** are cloud-based platforms providing centralised access to Copernicus data and information, as well as to processing tools (processing as a service) closely coupled with the data store. The European Commission has funded the deployment of five [DIAS instances](https://www.copernicus.eu/en/access-data/dias) (CREODIAS, MUNDI, ONDA, SOBLOO, WEKEO) managed under contract with the European Space Agency (ESA) that facilitate and standardise access to the **full archive of Sentinel-1 and Sentinel-2 data**. The [Sentinels](https://sentinels.copernicus.eu/) are a family of satellite missions for the operational needs of the EU Copernicus earth observation programme. Sentinel-1 provides all-weather, day and night radar imagery, nominally acquired every 6 days with 5 meters spatial resolution. Sentinel-2 provides multispectral high-resolution optical imagery with approximately  5 days revisit time and 10 meters spatial resolution. Their image archive provides free images of agricultural areas since June 2015 for all Europe.  
Each of the five DIAS competitive platforms also provides access to additional commercial satellite or non-space data sets as well as premium offers in terms of support or priority. Thanks to a single access point for the entire Copernicus data and information, DIAS allows the users to develop and host their own applications in the cloud, while removing the need to download bulky files from several access points and process them locally.  
A key service offered by the DIAS and essential for all Member States/Paying Agencies is the generation of **Copernicus Application (or Analysis) Ready Data (CARD)**, which are data over the area of interest prepared for a user to analyse without having to pre-process the imagery themselves. It includes georeferenced, calibrated sensor data (Level 2). Sentinel 1 and 2 data are, by default, delivered by ESA through the Copernicus Hub as Level 1 data. Since March 2018, Level 2 (atmospherically corrected) Sentinel-2 data is also made available. For Sentinel-1, this is not the case (yet).

### CbM for the CAP

In 2018 **Checks by Monitoring (CbM)** were introduced for area-based support schemes as an alternative to classical on-the-spot-checks ([Article 40a of implementation  regulation (EU) 746/2018 of 18 May 2018](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32018R0746)) for the IACS managed by the European Union Member States. The CbM approach is based on the automated analysis on the whole population of aid recipients verifying the consistency of farmers' aid applications with satellite-based evidence. The DIAS provide the relevant functionalities and an optimized use of Sentinel-1 and Sentinel-2 imagery for the continuous detection of agricultural conditions and activities on all the individual land parcels retrieved from the Land Parcel Identification System (LPIS) and the Geospatial Aid Application (GSAA). The information extracted from the Sentinel data (signatures) per individual parcel and date (time series) can be used to observe specific events (e.g. mowing, ploughing) or sequence of events (scenarios) when certain conditions are met (markers). This process results in a simplification of the huge Sentinel data set and leads to the classification of the declared parcels according to the traffic light classes (green = compliant, red = non compliant, yellow = inconclusive - require further investigation) limiting the number of dossiers to be inspected. The final outcome is a more efficient and largely automated check of all aid applications by Paying Agencies.

---

## GTCAP support for JRC CbM
### JRC CbM DIAS
The ongoing implementation of the CAP and the development of a CAP post-2020 that comply with new EU commitments on climate change and sustainable development are priorities for the [Joint Research Centre (JRC)](https://ec.europa.eu/jrc/). In this framework, the JRC Directorate D5 and the [Directorate General Agriculture and Rural Development - DG Agri](https://ec.europa.eu/info/departments/agriculture-and-rural-development_en) signed an Administrative Arrangement for CAP Implementation Support Activities CAPISA 2 that covers the period from October 2020 to September 2022. One of the work packages (WP) is on supporting Member States/Paying Agencies on the deployment and use of cloud solutions for CAP area aid schemes. The GTCAP group in liaison with other JRC teams and in close consultation with DG AGRI  

* validates the specific functional requirements of the CAP on cloud instances and addresses deployment issues including portability  
* develops and operates a repository of shared technical solutions, best practices and algorithms, particularly on the implementation of methods based on earth observation (EO) signals  
* provides training sessions to Member States/Paying Agencies on the use of DIAS for CbM  
* implements and monitors contract for purchase of DIAS services  

In addition, we advice on long term cloud-based solutions for CAP monitoring to ensure their future/continued availability.  
JRC CbM has substantial differences compared to the ESA project [SEN4CAP](dias4cbm_sen4cap.md)  
Decisions on CAP 2022+ and Copernicus DIAS are key drivers for future development of JRC CbM.  

### Outreach activity
The Outreach activity offers to the Member State willing to take up initiative on detection of agricultural phenomena with Sentinel data the possibility to use an JRC CbM environment set up by GTCAP that takes care of the backend. Here final users and analysts can test the tools and the code with technical support before they create their own CbM system.  
