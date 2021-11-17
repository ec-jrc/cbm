#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Daniele Borio
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD
# Created on Wed Oct 13 13:42:42 2021

import json
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import options_to_dot as otd


##################### Option File #############################################
optionFilePath = "./option files/optionFile_coh_only.json"
# optionFilePath = "./option files/optionFileRestFul_ndvi_ndwi.json"
# optionFilePath = "./optionFile.json"

optionFile = open(optionFilePath)
options = json.load(optionFile)


# open the output file
outputFilePath = optionFilePath[:optionFilePath.rfind(".")] + ".gv"
outputFile = open(outputFilePath, 'w')

# generate the output dot file
otd.generate_dot_diagram(options, outputFile)

# compile the png file
outputPngPath = optionFilePath[:optionFilePath.rfind(".")] + ".png"
os.system(f"dot -Tpng \"{outputFilePath}\" -o \"{outputPngPath}\"")

img = mpimg.imread(outputPngPath)
imgplot = plt.imshow(img)    
               
                

