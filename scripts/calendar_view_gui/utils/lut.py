#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Csaba Wirnhardt
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


from osgeo import gdal
import sys
    
def getCumulativeCutCountForOneBand(tifFileName, band, leftPercent, rightPercent):
    src_ds = gdal.Open( tifFileName )
    if src_ds is None:
        print("Unable to open:", tifFileName)
        sys.exit(1)

    srcband = src_ds.GetRasterBand(band)
    (min,max) = srcband.ComputeRasterMinMax(band)
    # srcband.SetNoDataValue(noData)
    # stats = band.GetStatistics(approx, 1)

    # print(min)
    # print(max)
    if min == max:
        lowerLimit = 0
        upperLimit = 0
        return(lowerLimit, upperLimit)
    else: 
        dfMin = float(0.5)
        dfMax = float(max+0.5)
        # print(dfMin, dfMax)
        nBuckets = int(dfMax-dfMin)

        #bIncludeOutOfRange : if TRUE values below the histogram range will mapped into panHistogram[0], 
        #and values above will be mapped into panHistogram[nBuckets-1] otherwise out of range values are discarded
        ioor = 0
        force = 1
        approxok = 0
        hist = srcband.GetHistogram( dfMin, dfMax, nBuckets, ioor, approxok )
        totalNumberOfPixels = sum(hist)
        leftTarget = int(round(totalNumberOfPixels * (leftPercent/100),0))
        rightTarget =int(round(totalNumberOfPixels - ( totalNumberOfPixels * (rightPercent/100)),0))

        # let's go through the list of histogram values from the right and see when we
        # reach left and right percentages
        i = 0
        cumulativeHist = 0
        for entry in hist:
            cumulativeHist += entry
            # print(i,cumulativeHist)    
            if leftTarget >= cumulativeHist - entry and  leftTarget < cumulativeHist:
                lowerLimit = i
            if rightTarget >= cumulativeHist - entry and rightTarget < cumulativeHist:
                upperLimit = i
            i += 1

        # print("totalNumberOfPixels:", totalNumberOfPixels)
        # print("leftTarget:",leftTarget)
        # print("rightTarget:",rightTarget)
        # print("lowerLimit:",lowerLimit)
        # print("upperLimit:",upperLimit)
        # print(leftPercent/100)
        return(lowerLimit, upperLimit)

def lutStretch(tifFileName, output, leftPercent, rightPercent, bands ):
    lutDict = {}
    for band in bands:
        (lowerLimit, upperLimit) = getCumulativeCutCountForOneBand(tifFileName,band, leftPercent, rightPercent)                    
        lutDict[band] = (lowerLimit, upperLimit)

    rmin = lutDict[bands[0]][0]
    rmax = lutDict[bands[0]][1]
    gmin = lutDict[bands[1]][0]
    gmax = lutDict[bands[1]][1]
    bmin = lutDict[bands[2]][0]
    bmax = lutDict[bands[2]][1]
    
    # scaleParams --- list of scale parameters, each of the form [src_min,src_max] or [src_min,src_max,dst_min,dst_max]
    ds = gdal.Open(tifFileName)
    # ds = gdal.Translate(output, ds, scaleParams = [[rmin, rmax, 0, 255], [gmin, gmax, 0, 255], [bmin, bmax, 0, 255]], bandList = [4,2,1], outputType = gdal.GDT_Byte)
    ds = gdal.Translate(output, ds, scaleParams = [[rmin, rmax, 0, 255], [gmin, gmax, 0, 255], [bmin, bmax, 0, 255]], bandList = bands, outputType = gdal.GDT_Byte)
    ds = None

def writeMinMaxToFile(tifFileName, acqDate, bands, leftPercent, rightPercent, lutTxtFile, tile_name):
    fout = open(lutTxtFile, 'a')
    lutDict = {}
    for band in bands:
        (lowerLimit, upperLimit) = getCumulativeCutCountForOneBand(tifFileName, band, leftPercent, rightPercent)                    
        lutDict[band] = (lowerLimit, upperLimit)

    rmin = lutDict[bands[0]][0]
    rmax = lutDict[bands[0]][1]
    gmin = lutDict[bands[1]][0]
    gmax = lutDict[bands[1]][1]
    bmin = lutDict[bands[2]][0]
    bmax = lutDict[bands[2]][1]
    print(acqDate, tile_name, leftPercent, rightPercent, rmin,rmax,gmin,gmax,bmin,bmax, file=fout)
    
def lutStretchMagicLut(tifFileName, output, bands ):
    #B08#1200#5700,
    #B11#800#4100,
    #B04#150#2800
    #  B08#1200#5700,B11#800#4100,B04#150#2800


    rmin = 1200
    rmax = 5700
    gmin = 800
    gmax = 4100
    bmin = 150
    bmax = 2800
    
    # # Lut specific to a parcel from spain Aragon, very bright throughout the season
    # rmin = 1500
    # rmax = 6700
    # gmin = 1500
    # gmax = 7000
    # bmin = 0
    # bmax = 6200
    
    # scaleParams --- list of scale parameters, each of the form [src_min,src_max] or [src_min,src_max,dst_min,dst_max]
    ds = gdal.Open(tifFileName)
    # ds = gdal.Translate(output, ds, scaleParams = [[rmin, rmax, 0, 255], [gmin, gmax, 0, 255], [bmin, bmax, 0, 255]], bandList = [4,2,1], outputType = gdal.GDT_Byte)
    ds = gdal.Translate(output, ds, scaleParams = [[rmin, rmax, 0, 255], [gmin, gmax, 0, 255], [bmin, bmax, 0, 255]], bandList = bands, outputType = gdal.GDT_Byte)
    ds = None    
    
def lutStretchMagicLut_2022(tifFileName, output, bands ):
    #B08#1200#5700,
    #B11#800#4100,
    #B04#150#2800
    
    # B08#2200#6700,B11#1800#5100,B04#1150#3800


    rmin = 2200
    rmax = 6700
    gmin = 1800
    gmax = 5100
    bmin = 1150
    bmax = 3800
    
    # scaleParams --- list of scale parameters, each of the form [src_min,src_max] or [src_min,src_max,dst_min,dst_max]
    ds = gdal.Open(tifFileName)
    # ds = gdal.Translate(output, ds, scaleParams = [[rmin, rmax, 0, 255], [gmin, gmax, 0, 255], [bmin, bmax, 0, 255]], bandList = [4,2,1], outputType = gdal.GDT_Byte)
    ds = gdal.Translate(output, ds, scaleParams = [[rmin, rmax, 0, 255], [gmin, gmax, 0, 255], [bmin, bmax, 0, 255]], bandList = bands, outputType = gdal.GDT_Byte)
    ds = None        

def get_cumulative_cut_count_for_one_band_float(tifFileName, leftPercent, rightPercent):
    src_ds = gdal.Open( tifFileName )
    if src_ds is None:
        print("Unable to open:", tifFileName)
        sys.exit(1)

    srcband = src_ds.GetRasterBand(1)
    # print(srcband)
    (min,max) = srcband.ComputeRasterMinMax(1)
    # srcband.SetNoDataValue(noData)
    # stats = band.GetStatistics(approx, 1)

    # print(min)
    # print(max)
    dfMin = float(0.5)
    dfMax = float(max+0.5)
    # print(dfMin, dfMax)
    nBuckets = int(dfMax-dfMin)

	#bIncludeOutOfRange : if TRUE values below the histogram range will mapped into panHistogram[0], 
	#and values above will be mapped into panHistogram[nBuckets-1] otherwise out of range values are discarded
    ioor = 0
    force = 1
    approxok = 0
    # hist = srcband.GetHistogram( dfMin, dfMax, nBuckets, ioor, approxok )

    hist = srcband.GetHistogram()
    # print(hist)
    totalNumberOfPixels = sum(hist)
    leftTarget = int(round(totalNumberOfPixels * (leftPercent/100),0))
    rightTarget =int(round(totalNumberOfPixels - ( totalNumberOfPixels * (rightPercent/100)),0))

    # let's go through the list of histogram values from the right and see when we
    # reach left and right percentages
    i = 0
    cumulativeHist = 0
    for entry in hist:
        cumulativeHist += entry
        # print(i,cumulativeHist)    
        if leftTarget >= cumulativeHist - entry and  leftTarget < cumulativeHist:
            lowerLimit = i
        if rightTarget >= cumulativeHist - entry and rightTarget < cumulativeHist:
            upperLimit = i
        i += 1

    # print("totalNumberOfPixels:", totalNumberOfPixels)
    # print("leftTarget:",leftTarget)
    # print("rightTarget:",rightTarget)
    # print("lowerLimit:",lowerLimit)
    # print("upperLimit:",upperLimit)
    # print(leftPercent/100)
    return(lowerLimit, upperLimit)
    
def lut_stretch_one_band_s1_bs(tifFileName, output, leftPercent, rightPercent):
    band = 1
    # (lowerLimit, upperLimit) = get_cumulative_cut_count_for_one_band_float(tifFileName, leftPercent, rightPercent)   
    (lowerLimit, upperLimit) = getCumulativeCutCountForOneBand(tifFileName, band, leftPercent, rightPercent)
    if lowerLimit == 0 and upperLimit ==0:
        print("no data in image file:", tifFileName)
        return
    else:
        # print(lowerLimit, upperLimit)
        
        # scaleParams --- list of scale parameters, each of the form [src_min,src_max] or [src_min,src_max,dst_min,dst_max]
        ds = gdal.Open(tifFileName)
        # ds = gdal.Translate(output, ds, scaleParams = [[rmin, rmax, 0, 255], [gmin, gmax, 0, 255], [bmin, bmax, 0, 255]], bandList = [4,2,1], outputType = gdal.GDT_Byte)
        ds = gdal.Translate(output, ds, scaleParams = [[lowerLimit, upperLimit, 0, 255]], bandList = [1,], outputType = gdal.GDT_Byte)
        ds = None
    

# tifFileName = "e:/chips/be_fl_for_s1_comparison_07/1__/s1_bs/20200402T055753_VH_x10000.tif"
# output = "e:/chips/be_fl_for_s1_comparison_07/1__/s1_bs/20200402T055753_VH_x10000_lut.tif"

# leftPercent = 1
# rightPercent = 4

# lut_stretch_one_band_s1_bs(tifFileName, output, leftPercent, rightPercent)

# tifFileName = "e:/MS/ES/Catalunia2019/raster/chips/343130_wheat_merged/s2_2019-05-06.tif"
# output = "e:/MS/ES/Catalunia2019/raster/chips/343130_wheat_merged_lut/s2_2019-05-06.tif"


# bands=[1,2,3]
# acqDate = "2019-05-06"

# lutTxtFile = "e:/MS/ES/Catalunia2019/raster/chips/lutTxt/lut.txt"

# writeMinMaxToFile(tifFileName, acqDate, bands, leftPercent, rightPercent, lutTxtFile)
# # lutStretch(tifFileName, output, leftPercent, rightPercent, bands )