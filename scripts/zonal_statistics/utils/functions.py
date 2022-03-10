from osgeo import gdal
import numpy as np


# slope WITH DEMProcessing
def calculateSlope(dem):
    gdal.DEMProcessing('temp/slope.tif', dem, 'slope', computeEdges=True)
    return gdal.Open('temp/slope.tif')


# aspect WITH DEMProcessing
def calculateAspect(dem):
    gdal.DEMProcessing('temp/aspect.tif', dem, 'aspect', computeEdges=True)
    return gdal.Open('temp/aspect.tif')


# CUSTOM FUNCTIONS
def boundingBoxToOffsets(bbox, geot):
    """This function returns starting and ending rows and columns
    of a bounding box inside a bigger raster dataset based on his geotransform attributes.
    format [start_row, end_row, start_col, end_col"""

    #  the +1 is for taking an extra row and column
    #  to have an offset in the raster and reduce errors in zstats
    col1 = int((bbox[0] - geot[0]) / geot[1])
    col2 = int((bbox[1] - geot[0]) / geot[1]) + 1
    row1 = int((bbox[3] - geot[3]) / geot[5])
    row2 = int((bbox[2] - geot[3]) / geot[5]) + 1
    return [row1, row2, col1, col2]


def geotFromOffsets(row_offset, col_offset, geot):
    """
    This function return a new geotransform
    :param row_offset: starting row of the offset
    :param col_offset: starting col of the offset
    :param geot: original geotransform
    :return: new geotransform based on the given parameters
    """

    new_geot = [
        geot[0] + (col_offset * geot[1]),
        geot[1],
        0.0,
        geot[3] + (row_offset * geot[5]),
        0.0,
        geot[5]
    ]
    return new_geot


def setFeatureStats(fid, **kwargs):
    """this functions populates a dictionary with the feature statistics"""
    feature_stats = {'pid':fid}

    for key, value in kwargs.items():
        feature_stats[key] = value

    return feature_stats


def getCircularMean(angles):
    n = len(angles)
    sineMean = np.divide(np.sum(np.sin(np.radians(angles))), n)
    cosineMean = np.divide(np.sum(np.cos(np.radians(angles))), n)
    vectorMean = np.arctan2(sineMean, cosineMean)
    return np.degrees(vectorMean)


def dsmListParser(x_range, y_range):
    dsmList = []
    with open('utils/Cop_DSM_content.txt', 'r') as file:
        lines = file.readlines()
        for x in x_range:
            for y in y_range:
                substring = f"Copernicus_DSM_10_N{y}_00_E0{x}_00"
                dsm_file = f"/DEM/Copernicus_DSM_10_N{y}_00_E0{x}_00_DEM.dt2"
                for line in lines:
                    if substring in line:
                        CopernicusString = line.strip() + dsm_file
                        dsmList.append(CopernicusString)
    return dsmList


# QUERIES:
def get_data_query(cursor):
    cursor.execute("""SELECT ogc_fid, wkb_geometry
                    FROM hu.parcels_2020;""")
    return cursor.fetchall()
