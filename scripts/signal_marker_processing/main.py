#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

__title__ = "CbM"
__author__ = ["Daniele Borio"]
__copyright__ = "Copyright 2021, European Commission Joint Research Centre"
__credits__ = ["GTCAP Team"]
__license__ = "3-Clause BSD"
__maintainer__ = ["Daniele Borio", "Konstantinos Anastasakis"]
__email__ = ""
__status__ = "Development"

###################### IMPORT LIBRARIES #######################################

import parcel_data_sources as pds
import time_series_sources as tss
import pre_processors as pps
import markers_processing as mp
import data_displayer as dd
import data_sink as ds
import marker_aggregation as ma
import scenario_evidence as se


# Utilities for computing geometric properties of the parcel
import geom_utils as gu

import json

# The following code block has been added to support input from command line/notebook
import sys


# Load additional inputs from coomand line
# Code from 
# https://stackoverflow.com/questions/39390418/python-how-can-i-enable-use-of-kwargs-when-calling-from-command-line-perhaps
if len(sys.argv) > 1 :
    # There is at least one argument after the file name
    kwargs = { kw[0]:kw[1] for kw in [ar.split('=') for ar in sys.argv if ar.find('=')>0]}
    args = [arg for arg in sys.argv if arg.find('=')<0]
else :
    kwargs = {}
    args = []

if ("notebook" in kwargs) and (kwargs["notebook"]=="True"):
    from tqdm.notebook import tqdm
    
    ##################### Option File #############################################
    optionFilePath = "./config/main.json"
else:
    from tqdm import tqdm    

    ##################### Option File #############################################
    optionFilePath = "./notebook/config/main.json"


optionFile = open(optionFilePath)
options = json.load(optionFile)

##################### Get the parcel files ####################################
# Create the parcel data factory and the parcel data
parcel_df = pds.parcel_data_factory()
parcel_ds = parcel_df.get_parcel_data_source(options)
print("Parcel data loaded \n")
fid_list = parcel_ds.get_fid_list()

# Get the length of the parcels to process
if "parcel_num" in kwargs :
    parcel_num = int(kwargs["parcel_num"])
else :
    parcel_num = len(fid_list)

##################### Get the signal files ####################################
# Create the signal factory and retrieve the signal files
ts_source_factory = tss.time_serie_source_factory()
ts_sources = ts_source_factory.get_time_series_sources(options)
print("Time series loaded")

##################### Build the pre-processing stage ##########################
pp_factory = pps.processor_factory()
pre_processors = pp_factory.get_pre_processors(options)

##################### Build the marker detectors ##############################
md_factory = mp.marker_detector_factory()
marker_detectors = md_factory.get_marker_detectors(options)

##################### Build the marker aggregator #############################
marker_agg = ma.marker_aggregator(options)

##################### Build the marker data sink ##############################
if "marker-sink" in options :
    ms_option_list = options["marker-sink"]
    
    mk_sink = ds.marker_sink(ms_option_list[0])
    
    if len(ms_option_list) > 1 :
        agmk_sink = ds.marker_sink(ms_option_list[1])
    else:
        agmk_sink = None
else :
    mk_sink = None
    agmk_sink = None

##################### Build the data displayer ################################
data_disp_factory = dd.data_displayer_factory()
data_disps = data_disp_factory.get_data_displayers(options)
    
############################ Scenario evidence writer #########################
if 	"scenario-evidence" in options :
    scenario_ev = se.scenario_evidence(options["scenario-evidence"])
else :
    scenario_ev = None
    
###############################################################################

# Main processing loop
for fid in tqdm(fid_list[:parcel_num]) :
    
    # get the parcel geometry
    parcel_geometry = parcel_ds.get_parcel( fid )
    
    # get the data related to the specific parcel
    parcel_data = {}
    
    for ts_source in ts_sources :
        data = ts_source.get_ts(fid)
        if len(data) > 0 :
            parcel_data[ts_source.get_signal_type()] = data
    
    # parcel_data is a dictionary with different pandas dataframes. Each
    # dataframe is indexed by a signal/TS key

    # Get the properties
    geom_prop = gu.get_geometric_properties( parcel_geometry )
    
    # eventually skip the parcel
    # ADD HERE LOGIC TO EVENTUALLY SKIP THE PARCEL
    # A similar approach can be adopted to check signal properties
    
    # Pre-process the data
    markers = {}
    if len(parcel_data) > 0 :
        for pre_pro in pre_processors :
            parcel_data = {**parcel_data, **(pre_pro.process(parcel_data))}
            
        # # Extract the markers

        for marker_det in marker_detectors :
            markers = {**markers, **(marker_det.get_markers(parcel_data))}

    if mk_sink is not None :
        # Output the marker information
        mk_sink.dump_marker_info(fid, markers)    

    # Create the summary graphs and save it to file
    for data_disp in data_disps :
        data_disp.dump_to_file(parcel_data, markers, fid)    

    # Aggregate the markers
    aggregated_markers = marker_agg.aggregate_markers(markers)
    # print([x.type for x in aggregated_markers])
    
    if agmk_sink is not None :
        agmk_sink.dump_marker_info(fid, aggregated_markers)

    # Write information at the parcel level
    if scenario_ev is not None :
        scenario_ev.dump(fid, aggregated_markers, geom_prop)

if mk_sink is not None :    
    mk_sink.out_file.close()

if agmk_sink is not None :
    agmk_sink.out_file.close()
    
optionFile.close()        
    
if scenario_ev is not None :
    scenario_ev.out_file.close()
