#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Sat Oct  9 06:39:26 2021

def dot_parcel_source( option : dict ) -> str :
    
    source_type = option["type"]
    
    dot_str = (f"\t parcelSource [\n"
               f"\t\t label = <<TABLE BGCOLOR=\"lightblue\">\n"
               f"\t\t <TR><TD><B><U>Parcel Source</U></B></TD></TR>\n"
               f"\t\t <TR><TD><B>type:</B> {source_type}</TD></TR>\n")
    
    for key in option :
        if key != "type" :
            dot_str = dot_str + \
                      f"\t\t <TR><TD><B>{key}:</B> {option[key]}</TD></TR>\n"
    
    dot_str = dot_str + "\t\t </TABLE>>];\n"

    return dot_str

def dot_data_reader(option : dict, count : int ) :
    
    data_reader_type = option["type"]
    
    dot_str = (f"\t dataReader{count} [\n"
               f"\t\t label=<<TABLE BGCOLOR=\"lightgrey\">\n"
               f"\t\t <TR><TD><B><U>Data Reader</U></B></TD></TR>\n"
               f"\t\t <TR><TD><B>type:</B> {data_reader_type}</TD></TR>\n")
    
    for key in option :
        if key == "type" :
            continue
        elif key == "connection_options" :
            
            conn_opt = option["connection_options"]
            
            for ckey in conn_opt :
                if 'api' not in ckey :
                    dot_str = dot_str + \
                    f"\t\t <TR><TD><B>{ckey}:</B> {conn_opt[ckey]}</TD></TR>\n"
        else :
            dot_str = dot_str + \
                      f"\t\t <TR><TD><B>{key}:</B> {option[key]}</TD></TR>\n"
        
    dot_str = dot_str + "\t\t </TABLE>>];\n"

    name_nodes = {option["signal"] : [f"dataReader{count}"] }

    return dot_str, name_nodes

def dot_pre_processor(option : dict, count : int = 0) :
    sub_graph_names = option["outnames"]
    
    sg_name = sub_graph_names[0]
    ii = 1
    while ii < len(sub_graph_names) : 
        sg_name = sg_name + '_' + sub_graph_names[ii]
        ii += 1
        
    dot_str = f"\t subgraph {sg_name} {{\n"
    
    names = []
    for opt in option["processors"] :
        pp_str, name = dot_processor(opt, "\t", count )
        dot_str = dot_str + pp_str + "\n"
        names.append(name)
        
    # Now add the arcs
    ii = 1
    while ii < len(names) :
        dot_str = dot_str + f"\t\t{names[ii - 1]} -> {names[ii]};\n"
        ii += 1
    
    dot_str = dot_str + "\n\t }"

    names_node ={}
    for sub_names in sub_graph_names :
        names_node[sub_names] = [names[0], names[-1]]
        
    return dot_str, names_node

def dot_processor(option : dict, indent : str = "", count = 0) :
    pp_type = option["type"]
    
    dot_str = (f"{indent}\t {pp_type}{count} [\n"
               f"{indent}\t\t label=<<TABLE BGCOLOR=\"yellow\">\n"
               f"{indent}\t\t <TR><TD><B><U>{pp_type}</U></B></TD></TR>\n")

    for key in option :
        if (key == "type") or (key == "signals"):
            continue
        else :
            if isinstance(option[key], list) :
                value = ""
                for element in option[key] :
                    value = value + str(element)
                    if element != option[key][-1]:
                        value = value + ", "
            else :
                value = str(option[key])
                
            dot_str = dot_str + \
                      f"{indent}\t\t <TR><TD><B>{key}:</B> {value}</TD></TR>\n"
        
    dot_str = dot_str + f"{indent}\t\t </TABLE>>];\n"
    
    name = pp_type + str(count)
    
    return dot_str, name
    
def get_pp_connection(opt : dict, name_nodes : dict, nodes : dict) -> str :
    
    # get the destination node
    sub_graph_names = opt["outnames"]
    sg_name = sub_graph_names[0]
 
    dest_node = nodes[sg_name][0]
    
    # get the origin node
    first_node = opt["processors"][0]
    
    dot_str = ""
    for signal in first_node["signals"] :
        origin_node = name_nodes[signal][-1]
        dot_str = dot_str + f"\t {origin_node} -> {dest_node};\n"

    return dot_str

def dot_marker_detector(option : dict, count : int = 0) :
    
    detector_type = option["type"]
    object_name = detector_type + str(count)
    object_name = object_name.replace("-", "_")
    
    dot_str = (f"\t {object_name} [\n"
               f"\t\t label=<<TABLE BGCOLOR=\"lightgreen\">\n"
               f"\t\t <TR><TD><B><U>{detector_type}</U></B></TD></TR>\n")
    
    for key in option :
        if ( key == "type") or ( key == "signals") :
            continue
        else :
            dot_str = dot_str + \
                      f"\t\t <TR><TD><B>{key}:</B> {option[key]}</TD></TR>\n"

    dot_str = dot_str + "\t\t</TABLE>>];\n"
    connections = {}
    for signal in option["signals"] :
        connections[signal] = object_name
    
    return dot_str, connections

def dot_data_displayer(option : dict, count : int = 0) :
    
    object_name = "data_displayer"
    
    dot_str = (f"\t {object_name} [\n"
               f"\t\t label=<<TABLE BGCOLOR=\"salmon\">\n"
               f"\t\t <TR><TD><B><U>Data Displayer</U></B></TD></TR>\n")
    
    for key in option :
        if ( key == "type") or ( key == "signals") :
            continue
        else :
            dot_str = dot_str + \
                      f"\t\t <TR><TD><B>{key}:</B> {option[key]}</TD></TR>\n"

    dot_str = dot_str + "\t\t</TABLE>>];\n"
    connections = {}
    for signal in option["signals"] :
        connections[signal] = object_name
    
    return dot_str, connections

def get_band_node(options, name_nodes, components) :
    
    node = None
    
    for opt in options :
        pro_list = opt["processors"]
        pro_compo = []
        
        for pro in pro_list :
            if "components" in pro :
                pro_compo = pro["components"]
                
        if pro_compo == components :
            node = name_nodes[opt["outnames"][0]][-1]
            
    return node
 

def generate_dot_diagram( options, outputFile ) :
    # write the header
    header =  ("digraph option_file {\n"
               "\t rankdir=LR;\n"
               "\t node [shape=record,width=.1,height=.1];\n\n")
            
    outputFile.write(header)

    # First process the parcel source 
    if "parcelSource" in options : 
        dot_str = dot_parcel_source(options["parcelSource"])
        outputFile.write(dot_str)
        
    outputFile.write("\n")

    name_nodes = {}
    
    if "dataReaders" in options :
        ii = 1
        for opt in options["dataReaders"] :
            dot_str, nodes = dot_data_reader(opt, ii)
            outputFile.write(dot_str)
            outputFile.write("\n")
            ii += 1
            name_nodes = {**name_nodes, **nodes}

    if "pre-processors" in options :
        ii = 1
        for opt in options["pre-processors"] :
            dot_str, nodes = dot_pre_processor(opt, ii)
            ii += 1
            outputFile.write(dot_str)
            outputFile.write("\n")
            dot_str = get_pp_connection(opt, name_nodes, nodes)
            outputFile.write(dot_str)
            outputFile.write("\n")
            name_nodes = {**name_nodes, **nodes}
                
    # add marker detectors
    detect_dict = {}
    if "marker-detectors" in options :
        ii = 0
        for opt in options["marker-detectors"] :
            dot_str, conn = dot_marker_detector(opt, ii)
            ii +=1
            outputFile.write(dot_str)
            outputFile.write("\n")
            
            for key in conn :
                dot_str = f"\t {name_nodes[key][-1]} -> {conn[key]};\n"
                outputFile.write(dot_str)
            
            outputFile.write("\n")
            detect_dict[conn[key]] = opt["signals"]

    # add the data displayer
    if "data-displayer" in options :
        dot_str, conn = dot_data_displayer(options["data-displayer"])
        outputFile.write(dot_str)
        outputFile.write("\n")
            
        for key in conn :
            dot_str = f"\t {name_nodes[key][-1]} -> {conn[key]};\n"
            outputFile.write(dot_str)
            
        outputFile.write("\n")
        
        for marker_dete in detect_dict :
            if len(set(conn.keys()) & set(detect_dict[marker_dete])) > 0 :
                dot_str = f"\t {marker_dete} -> {conn[key]};\n"        
                outputFile.write(dot_str)
            
        outputFile.write("\n")
        
        if 'bottom_bar_components' in options["data-displayer"] :
            components = options["data-displayer"]['bottom_bar_components']
            band_node = get_band_node(options["pre-processors"], name_nodes, components)
            
            if band_node is not None :
                dot_str = f"\t {band_node} -> {conn[key]};\n"
                outputFile.write(dot_str)
                outputFile.write("\n")
                
    outputFile.write("}")
    outputFile.close()

