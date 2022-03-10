import os, shutil
import csv
import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio
import rasterstats
import utils.functions as f
import psycopg2
import psycopg2.extras as extras
from utils.connector import connect
from utils import config
from osgeo import gdal, ogr
import warnings
# ONLY IN TEST ENV
# import glob
warnings.filterwarnings('ignore')


# SELECT AOI BOUNDING BOX FROM POSTGRESQL
db = connect('outreach')
cur = db.cursor()
cur.execute("""SELECT name, 
                st_srid(wkb_geometry),
                substr(name,length(name)-3,length(name)) yearx,
                substr(name,0,length(name)-4) name_pa,
                floor(st_xmin(wkb_geometry)) AS xmin,
                ceil(st_xmax(wkb_geometry)) AS xmax,
                floor(st_ymin(wkb_geometry)) AS ymin,
                ceil(st_ymax(wkb_geometry)) AS ymax
                FROM public.aois;""")
query_result = cur.fetchall()
col = []
for x in cur.description:
    col.append(x[0])
data = pd.DataFrame(data=query_result, columns=col)

cur.close()
db.close()

aoi = data[data['name'] == 'hu_2020']

x_min = int(aoi.iloc[0]['xmin'])
x_max = int(aoi.iloc[0]['xmax'])
y_min = int(aoi.iloc[0]['ymin'])
y_max = int(aoi.iloc[0]['ymax'])

# RETRIEVING PARCELS' EPSG FROM POSTGRES
db = connect('outreach')
cur = db.cursor()
cur.execute("""SELECT st_srid(wkb_geometry) FROM hu.parcels_2020 LIMIT 1;""")
query_result = cur.fetchall()

cur.close()
db.close()

st_srid = query_result[0][0]

# CREATE .VRT IN PRODUCTION ENV
dsmList = f.dsmListParser(range(x_min, x_max+1), range(y_min, y_max+1))

# CREATE .VRT IN TEST ENV
# dsmList = glob.glob("dem/Copernicus_DSM_10_N*_00_E0*_00_DEM.dt2")

vrt = gdal.BuildVRT('temp/merged.vrt', dsmList)

# UNCOMMENT IF YOU WANT TO CREATE A LOCAL .TIF FILE
# gdal.Translate("dem/mergedDEM.tif", vrt_file)

mem_driver = ogr.GetDriverByName("Memory")
mem_driver_gdal = gdal.GetDriverByName("MEM")
shp_name = 'temp'

# SELECT PARCELS GEOMETRIES FROM POSTGIS
conn_string = f"PG:host={config.host} " \
              f"dbname={config.dbname} " \
              f"user={config.user} " \
              f"password={config.password} " \
              f"port={config.port}"

query = "SELECT ogc_fid, gid, st_astext(wkb_geometry) FROM hu.parcels_2020 LIMIT 200"
ds = gdal.OpenEx(conn_string, gdal.OF_VECTOR)
gdal.VectorTranslate(
    'parcels/parcels.shp',
    ds,
    options=gdal.VectorTranslateOptions(
        SQLStatement=query,
        srcSRS=f"EPSG:{st_srid}",
        dstSRS=f"EPSG:{st_srid}",
        layerName='parcels',
        format='ESRI Shapefile'
    )
)

fn_parcels = 'parcels/parcels.shp'

# UNCOMMENT BELOW IF YOU NEED TO MASK YOUR DATA
# fn_mask = 'mask/mask.shp'

#  READING FILES WITH GDAL/OGR
parcels_ds = ogr.Open(fn_parcels)
lyr = parcels_ds.GetLayer()

#  GeoTransform Reference: [0]/[3] upper left long/lat, [1]/[5] cell width/height [5] negative in N emisphere
geotransform_0 = vrt.GetGeoTransform()
proj_0 = vrt.GetProjection()

print('====== BEFORE PROJECTION ======')
print(geotransform_0)
print(proj_0)

# Clipping by mask, Reproject to national metric projection and Resampling grid to 30m
# Mask parameters only if needed
dsReproj = gdal.Warp("temp/vrt_reproj.tif",
                     vrt,
                     dstSRS=f"EPSG:{st_srid}",
                     xRes=30,
                     yRes=30,
                     # UNCOMMENT BELOW IF YOU NEED TO MASK YOUR DATA
                     # cutlineDSName=fn_mask,
                     # cropToCutline=True
                     )

# CHECK PROJECTION CHANGE
geotransform = dsReproj.GetGeoTransform()
proj = dsReproj.GetProjection()
nodata_dsm = dsReproj.GetRasterBand(1).GetNoDataValue()

print('====== AFTER PROJECTION ======')
print(geotransform)
print(proj)

# APPLYING FUNCTION TO CALCULATE SLOPE AND ASPECT FROM DSM, RETRIEVING BANDS
slope = f.calculateSlope(dsReproj)
nodata_slope = slope.GetRasterBand(1).GetNoDataValue()

aspect = f.calculateAspect(dsReproj)
nodata_aspect = aspect.GetRasterBand(1).GetNoDataValue()

#  GATHERING DATA (for each polygon feature in the layer creates a temporary layer to be rasterized)
zstats_dsm = []
zstats_slope = []
zstats_aspect = []
p_feat = lyr.GetNextFeature()

while p_feat:
    if p_feat.GetGeometryRef():
        if os.path.exists(shp_name):
            mem_driver.DeleteDataSource(shp_name)

        temp_ds = mem_driver.CreateDataSource(shp_name)
        temp_lyr = temp_ds.CreateLayer('polygons', None, ogr.wkbPolygon)
        temp_lyr.CreateFeature(p_feat.Clone())
        offsets = f.boundingBoxToOffsets(p_feat.GetGeometryRef().GetEnvelope(), geotransform)

        # Creating a new geotransform for the offset
        new_geot = f.geotFromOffsets(offsets[0], offsets[2], geotransform)

        # Creating temporary raster dataset with, parameters: ('filename', cols, rows, bands, datatype)
        temp_raster_ds = mem_driver_gdal.Create('',
                                                offsets[3] - offsets[2],
                                                offsets[1] - offsets[0],
                                                1,
                                                gdal.GDT_Byte)
        temp_raster_ds.SetGeoTransform(new_geot)

        # Rasterize the layer
        gdal.RasterizeLayer(temp_raster_ds, [1], temp_lyr, burn_values=[1])
        temp_raster_array = temp_raster_ds.ReadAsArray()

        # Read data source as array based on parameters: start_x, start_y, number_of_columns, number_of_rows
        raster_array_dsm = dsReproj.GetRasterBand(1).ReadAsArray(offsets[2],
                                                                 offsets[0],
                                                                 offsets[3] - offsets[2],
                                                                 offsets[1] - offsets[0]
                                                                 )

        raster_array_slope = slope.GetRasterBand(1).ReadAsArray(offsets[2],
                                                                offsets[0],
                                                                offsets[3] - offsets[2],
                                                                offsets[1] - offsets[0]
                                                                )

        raster_array_aspect = aspect.GetRasterBand(1).ReadAsArray(offsets[2],
                                                                  offsets[0],
                                                                  offsets[3] - offsets[2],
                                                                  offsets[1] - offsets[0]
                                                                  )

        # exclude anywhere we have a nodata value, and anywhere we don't have a value for our polygon arrays
        # then appending proper data to zstats list both for DSM, aspect, slope
        id = p_feat.GetFID() + 1
        print(f'====== ZONAL STATS FOR: {id} ======')

        # CALCULATE ZONAL STATISTICS FOR ELEVATION / DSM
        if raster_array_dsm is not None:
            maskarray = np.ma.MaskedArray(raster_array_dsm,
                                          mask=np.logical_or(raster_array_dsm == nodata_dsm,
                                                             np.logical_not(temp_raster_array)),
                                          )
            if maskarray is not None:
                print("MASKARRAY DSM")
                zstats_dsm.append(f.setFeatureStats(
                    id,
                    # elevmin=round(float(maskarray.min()),1),
                    # elevmax=round(float(maskarray.max()),1),
                    elevmean=round(float(maskarray.mean()), 2),
                    elevrange=round(float(maskarray.max()),1) - round(float(maskarray.min()),1),
                    elevcount=maskarray.count(),
                ))
            else:
                print("MASKARRAY DSM NODATA")
                zstats_dsm.append(f.setFeatureStats(
                    id,
                    # elevmin=nodata_dsm,
                    # elevmax=nodata_dsm,
                    elevmean=nodata_dsm,
                    elevrange=nodata_dsm,
                    elevcount=nodata_dsm,
                ))

        #  CALCULATE ZONAL STATISTICS FOR SLOPE
        if raster_array_slope is not None:
            maskarray = np.ma.MaskedArray(raster_array_slope,
                                          mask=np.logical_or(raster_array_slope == nodata_slope,
                                                             np.logical_not(temp_raster_array)),
                                          )
            if maskarray is not None:
                print("MASKARRAY SLOPE")
                zstats_slope.append(f.setFeatureStats(
                    id,
                    # slopemin=round(float(maskarray.min()),1),
                    # slopemax=round(float(maskarray.max()),1),
                    slopemean=round(float(maskarray.mean()),2),
                    # slopestdev=round(float(maskarray.std()),2),
                ))
            else:
                print("MASKARRAY SLOPE NODATA")
                zstats_slope.append(f.setFeatureStats(
                    id,
                    # slopemin=nodata_slope,
                    # slopemax=nodata_slope,
                    slopemean=nodata_slope,
                    # slopestdev=nodata_slope,
                ))

        # CALCULATE ZONAL STATISTICS FOR ASPECT
        if raster_array_aspect is not None:
            maskarray = np.ma.MaskedArray(raster_array_aspect,
                                          mask=np.logical_or(raster_array_aspect == nodata_aspect,
                                                             np.logical_not(temp_raster_array)),
                                          )
            if maskarray is not None:
                print("MASKARRAY ASPECT")
                zstats_aspect.append(f.setFeatureStats(
                    id,
                    # aspectmin=round(float(maskarray.min()),1),
                    # aspectmax=round(float(maskarray.max()),1),
                    # .compressed() eliminates masked values and .tolist() converts list of lists in a list
                    aspectmean=round(abs(f.getCircularMean(maskarray.compressed().tolist())),2),
                    aspectcount=maskarray.count(),
                    # aspectstdev=round(float(maskarray.std()),2),
                ))

        # MANAGING MISSING VALUES
        else:
            print("NODATA")
            zstats_dsm.append(f.setFeatureStats(
                id,
                # elevmin=nodata_dsm,
                # elevmax=nodata_dsm,
                elevmean=nodata_dsm,
                elevrange=nodata_dsm,
                elevcount=nodata_dsm,
            ))

        #  get rid of the temporary files
        temp_ds = None
        temp_lyr = None
        temp_raster_ds = None

        # go to next feature in the loop
        p_feat = lyr.GetNextFeature()

#  UNCOMMENT BELOW IF YOU WANT TO WRITE ZSTATS IN .CSV
# fn_out = 'output/zstats_dsm.csv'
# col_names_dsm = zstats_dsm[0].keys()
# with open(fn_out, 'w', newline='') as csvfile:
#     writer = csv.DictWriter(csvfile, col_names_dsm)
#     writer.writeheader()
#     writer.writerows(zstats_dsm)
#
# fn_out = 'output/zstats_slope.csv'
# col_names_slope = zstats_slope[0].keys()
# with open(fn_out, 'w', newline='') as csvfile:
#     writer = csv.DictWriter(csvfile, col_names_slope)
#     writer.writeheader()
#     writer.writerows(zstats_slope)
#
# fn_out = 'output/zstats_aspect.csv'
# col_names_aspect = zstats_aspect[0].keys()
# with open(fn_out, 'w', newline='') as csvfile:
#     writer = csv.DictWriter(csvfile, col_names_aspect)
#     writer.writeheader()
#     writer.writerows(zstats_aspect)


# WRITING DATA TO POSTGRES
print("Creating Postgres Table")
db = connect('outreach')
db.autocommit = True
cur = db.cursor()

print("Saving to POSTGRESQL")

df_dsm = pd.DataFrame(zstats_dsm, dtype=np.float64)
df_slope = pd.DataFrame(zstats_slope, dtype=np.float64)
df_aspect = pd.DataFrame(zstats_aspect, dtype=np.float64)
first_merge_df = pd.merge(df_dsm, df_slope, on='pid', how='inner')
df = pd.merge(first_merge_df, df_aspect, on='pid', how='inner')
df = df.replace(np.nan, None)

tpls = [tuple(x) for x in df.to_numpy()]
cols = ','.join(list(df.columns))

sql = """INSERT INTO %s(%s) VALUES %%s 
                ON CONFLICT ON CONSTRAINT env_2020_pkey 
                DO UPDATE SET
                elevmean = excluded.elevmean,
                elevrange = excluded.elevrange,
                elevcount = excluded.elevcount,
                slopemean = excluded.slopemean,
                aspectmean = excluded.aspectmean,
                aspectcount = excluded.aspectcount;"""\
      % ('hu.env_2020', cols)
cur = db.cursor()
psycopg2.extras.execute_values(cur, sql, tpls)

cur.close()
db.close()
print("Saving complete")

# DELETE TEMPORARY FILES, COMMENT IF YOU WANT TO KEEP THEM
folders = ['temp', 'parcels']
for folder in folders:
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

print('===== PROCESS COMPLETE =====')
