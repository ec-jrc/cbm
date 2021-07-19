#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Csaba Wirnhardt
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import requests
import rasterio
import numpy as np
import matplotlib.pyplot as plt

tiles = ["S2B_MSIL2A_20190617T104029_N0212_R008_T31UFU_20190617T131553",
            "S2A_MSIL2A_20190625T105031_N0212_R051_T31UFU_20190625T134744",
            "S2B_MSIL2A_20190620T105039_N0212_R051_T31UFU_20190620T140845"]
            
cmap = plt.get_cmap('RdYlGn')

for t in tiles:
    with rasterio.open(t + '.NDVI_scaled.tif') as src:
        data = src.read(1)
        nbins = 99
        N, bins, patches = plt.hist(data.astype(np.float32)/255.0, nbins, range=[0.01, 1.0], ec="k")
        for p in patches:
            for i in range(len(p)):
                p[i].set_color(cmap(float(i)/nbins))        
                
        plt.xlabel("NDVI", fontsize=16)
        plt.ylabel("Pixels per bin", fontsize=16)
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)        
        plt.gca().spines["top"].set_visible(False)
        plt.gca().spines["right"].set_visible(False)        
        plt.show()