from osgeo import gdal
import numpy as np
import rasterio


# slope WITH DEMProcessing
def calculateSlope(dem):
    gdal.DEMProcessing('temp/slope.tif', dem, 'slope', computeEdges=True, options='-p')
    return rasterio.open('temp/slope.tif')


# aspect WITH DEMProcessing
def calculateAspect(dem):
    gdal.DEMProcessing('temp/aspect.tif', dem, 'aspect', computeEdges=True)
    return rasterio.open('temp/aspect.tif')


def getMean(x):
    return round(float(np.ma.mean(x)),2)


def getCircularMean(angles):
    n = len(angles)
    sineMean = np.divide(np.sum(np.sin(np.radians(angles))), n)
    cosineMean = np.divide(np.sum(np.cos(np.radians(angles))), n)
    vectorMean = np.arctan2(sineMean, cosineMean)
    if vectorMean:
        return round(float(np.degrees(vectorMean)),2) if np.degrees(vectorMean) > 0 \
            else round(float(np.degrees(vectorMean)),2) + 360
    elif vectorMean == 0:
        return vectorMean
    else:
        return None


def dsmListParser(x_range, y_range):
    dsmList = []
    with open('utils/Cop_DSM_content.txt', 'r') as file:
        lines = file.readlines()
        for x in x_range:
            for y in y_range:
                substring = f"Copernicus_DSM_10_N{str(y).zfill(2)}_00_E0{str(x).zfill(2)}_00"
                dsm_file = f"/DEM/Copernicus_DSM_10_N{str(y).zfill(2)}_00_E0{str(x).zfill(2)}_00_DEM.dt2"
                for line in lines:
                    if substring in line:
                        CopernicusString = line.strip() + dsm_file
                        dsmList.append(CopernicusString)
                        break
    return dsmList
