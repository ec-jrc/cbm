#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Gilbert Voican, Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from ipywidgets import (HTML, VBox, widgets)


def widget_box():

    wbox = VBox(children=[ipycbm_help(), about()])
    return wbox


def ipycbm_help():

    html = """
<H2>'Get' and 'View' functions.</H2>
With the 'get' function you can download data from the server to your local jupyter environment.<br>
The 'view' function is to load local files and display them with different methods, or provide example code for each selected dataset.<br>
<H4>Available options:</H4>
<b>Get data example:</b><br>
<code>import cbm.ipycbm</code><br>
<code>ipycbm.get()</code>
<br>
<b>View data example:</b><br>
<code>import cbm.ipycbm</code><br>
<code>ipycbm.view()</code><br>
<br>
'**tmp**' folder structure example for parcel with ID 12345:<br>

    <code>tmp/
        cat2019/12345/info.json
        cat2019/12345/time_series.csv
        cat2019/12345/chipimages/images_list.csv
        cat2019/12345/chipimages/S2A_MSIL2A_2019---.B04.tif
        cat2019/12345/chipimages/...</code>
    """

    wbox = widgets.HTML(
        value=html,
        placeholder="Documantation",
        description="")

    return wbox


def about():
    from cbm import __version__
    html = f"""
    <H1>About</H1>
<H3>JRC D5 Food security - GTCAP</H3>
<H4>DIAS for CAP Checks by Monitoring, development platforms and services.</H4>
Authors:<br>
Guido Lemoine<br>
Konstantinos Anastasakis<br>
<br>
Copyright 2021, Joint Research Centre (JRC) European Commission<br>
License: 3-Clause BSD , Version: {__version__}

    """

    wbox = HTML(
        value=html,
        placeholder='About',
        description='',
    )

    return wbox


def widget_box_foi():

    wbox = VBox(children=[ipycbm_help_foi(), about()])
    return wbox


def ipycbm_help_foi():

    html = """
<H2>FOI Assessment: Heterogeneity and Cardinality</H2>
The FOI assessment notebook is based on the principle that inside of a homogenous FOI there should be only one type of pixels. In the same idea, a FOI which respects the 1-1 cardinalityshould not include clusters of pixels larger than a specified threshold (we can consider dispersed pixels different than the main class as “noise”).<br>
The FOI Assessment performs a spatial analysis on a "thematic raster" produced in advance. The thematic raster can be the result of any image/raster processing method yielding a class label for each pixel - crop classification, behavior analysis of land phenomenon, gridded data on soil, slope, humidity, etc.<br>
As an example, if the thematic raster is the result of a crop classification, a homogeneous FOI should have only one type of pixels that represent the respective crop, a cardinal FOI should not include any cluster of pixels from other class larger than a specified threshold.
If the thematic raster is the result of a behavior analysis, all the pixels inside an FOI should behave in the same way during a period of time.<br>
For both heterogeneity and cardinality, the notebook provides two methods for the analysis: one based area calculation (version 1) and one based on cluster size calculation (version 2). Both methods have similar results.
<br>
<H2>Version 1</H2>
The first version requires the connection to a database server (PostgreSQL with PostGIS extension)<br>
For the heterogeneity analysis the following steps are required (the steps correspond to the numbering on the interface):<br>

1.	Connect to the database (at the moment only „Database connection settings” are required)<br>
a)	Upload the reference data shapefile to the server. It is provided a graphical interface for upload.<br>
b)	Import uploaded shapefile to the database, specifying the name for the table that will be created in the database.<br>
2.	Upload the raster „thematic” image. A graphical interface is provided. The accepted files are tif or tiff files. The thematic raster should be a one band raster file, with the pixel values representing the classes (like crop type or type of behaviour)<br>
3.	Prepare FOI procedure – Allows the user to create the database functions on the database server. This procedure creates the necessary function and stored procedures on the database server.<br>
4.	Select the required files for analysis:<br>
a)	Vector file: the data on which the analysis will be applied. In case that we have more shapefiles uploaded on the server, this functionality allows us to select the one that we want to analyze.<br>
b)	Thematic raster: the thematic raster provided. In case that we have more rasters uploaded on the server, this functionality allows us to select the one that we want to use on the analysis.<br>
c)	YAML file that holds the classes form the thematic raster file: this file specifies the classes of pixels from the thematic raster and can also provide the meaning of those classes. It should have the following structure:<br>
<code>example.yml</code><br>
<code>category_map:
  0: Unclasified
  1: Class1
  2: Class2
  3: Class3
  4: Class4
  5: Class5
  6: Class6
  7: Class7
  8: Class8
  9: Class9
  10: Class10</code><br>
Class1, Class2 can be replaced by the meaning of the class (like Wheat, Maize, etc. or by behavior name or any other ….).<br>
The YAML file should include all the classes that exist in the thematic raster. It is provided a graphical interface for upload.<br>
5.	Analysis parameters:<br>
Heterogeneity thresholds: in order to exclude the influence of „noise” pixels, the user can specify the heterogeneity thresholds (for example only the FOIs where one class of pixels have a percentage between 30 and 70 is considered heterogeneous).<br>
Minimum area for clusters selection: the user can specify the minimum area of the cluster that are considered a cardinality issue, in square meters. Of example the clusters smaller than 2000 square meters can be considered as not influencing the FOI cardinality.<br>
6.	Run FOI procedure.<br>
Starts the FOI analysis. The result of the analysis is represented by three shapefiles that are stored on the “output_data” folder (/cbm/tmp/foi/output_data).<br>
<b>name of the shapefile dataset (without extension) that needs to be tested + foih_v1.shp</b> – represents the initial shapefile and during the analysis the following attributes are added:<br>
•	foi_h – heterogeneity flag (0 for homogeneous FOIs and 1 for heterogeneous FOIs)<br>
•	number of pixels for each class (the name of the attribute is the name of the class)<br>
•	total number of pixel for the respective FOI<br>
•	percentage of pixels from each class (number of pixels for each class / total number of pixels inside the FOI)<br>
<b>name of the shapefile dataset (without extension) that needs to be tested + foic_v1.shp</b> - represents the initial shapefile and during the analysis the following attributes are added:<br>
•	foi_c – cardinality flag (0 for FOIs respecting the 1-1 cardinality and 1 for FOIs not respecting the 1-1 cardinality). As a result of this analysis, the FOIs that include more than one cluster of pixel from different classes bigger than the threshold are considered non-cardinal. For example and FOI that includes two clusters of pixels from different classes (one arable land and non-agricultural area), each of the clusters bigger than the threshold (ex. 2000 square meters), is considered as not respecting the 1-1 cardinality.<br>
<b>name of the shapefile dataset (without extension) that needs to be tested + foic_clusters_v1.shp</b> – represents only the clusters of pixels that are setting the FOI cardinality (for example if an FOI includes three clusters of pixels bigger that the threshold, only those clusters will be saved in this shapefile)<br>

<H2>Version 2</H2>
The second version does not require a database server. All the calculations are made at pixel level using Python function.<br>
The interface and the steps are similar to the ones from the Version 1. The main difference is that it does not include the functionality for database connection and creating the functions on the database server.<br>
The different options available:<br>
Connectivity type: 8 or 4 connected pixels (4 indicating that diagonal pixels are not considered directly adjacent for polygon membership purposes or 8 indicating they are)<br>
Negative buffer: user can apply a negative buffer on the FOI in order to reduce the influence of boundary influence on the analysis (roads, adjacent FOIs, etc.)<br>
Cluster size (in pixels): the minimum number of pixels for which a cluster is taken into account.<br>
The result of the analysis is represented by two shapefiles that are stored on the “output_data” folder (/cbm/tmp/foi/output_data).<br>
<b>name of the shapefile dataset (without extension) that needs to be tested + foih_v2.shp</b> – represents the initial shapefile and during the analysis the following attributes are added:<br>
•	foi_h – heterogeneity flag (0 for homogeneous FOIs and 1 for heterogeneous FOIs)<br>
•	number of pixels for each class (the name of the attribute is the name of the class)<br>
•	total number of pixel for the respective FOI<br>
•	percentage of pixels from each class (number of pixels for each class / total number of pixels inside the FOI)<br>
<b>name of the shapefile dataset (without extension) that needs to be tested + foic_v2.shp</b> - represents the initial shapefile and during the analysis the following attributes are added:<br>
•	foi_c – cardinality flag (0 for FOIs respecting the 1-1 cardinality and 1 for FOIs not respecting the 1-1 cardinality). As a result of this analysis, the FOIs that include more than one cluster of pixels from different classes bigger than the threshold are considered not respecting the 1-1 cardinality. For example and FOI that includes two clusters of pixels from different classes (one arable land and non-agricultural area), each of the clusters bigger than the threshold (ex. 20 pixels), is considered as not respecting the 1-1 cardinality.<br>
•	Clusters – the information about the clusters of pixels identified inside the FOI, as pair of pixel class and cluster size: for example (3, 25), (5, 120) means that inside the FOI we have identified two clusters: one of pixels from class 3 and the cluster size is 25 pixels and another one with pixels of class 5 and cluster size 120 pixels.<br>

Author:<br>
Gilbert Voican

    """

    wbox = widgets.HTML(
        value=html,
        placeholder="Documentation",
        description="")

    return wbox
