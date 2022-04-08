import geopandas as gpd
import pandas as pd
import rasterio
import rasterstats
import psycopg2
import psycopg2.extras as extras
from osgeo import gdal
from sqlalchemy import create_engine
from utils.connector import connect
from utils import config
from utils import functions as f
# from datetime import datetime


db = connect(config.dbname)
cur = db.cursor()
db.autocommit = True
sql = """CREATE TABLE IF NOT EXISTS public.env
        (
            pid integer NOT NULL,
            grid_id integer,
            elevmean integer,
            elevrange integer,
            elevcount integer,
            slopemean double precision,
            aspectmean double precision,
            aspectcount integer,
            CONSTRAINT env_pkey PRIMARY KEY (pid),
            CONSTRAINT env_era5_grid_fkey FOREIGN KEY (grid_id)
                REFERENCES public.era5_grid (grid_id),
            CONSTRAINT env_dk2021_fkey FOREIGN KEY (pid)
                REFERENCES public.dk2021 (ogc_fid)
        );"""
cur.execute(sql)

# sql2 = """INSERT into public.env (pid)
#             SELECT ogc_fid FROM public.dk2021;"""
#
# cur.execute(sql2)

sql3 = """UPDATE public.env
        SET grid_id = a.grid_id
        FROM
            (SELECT grid_id, ogc_fid
            FROM public.dk2021, public.era5_grid
            WHERE st_intersects(geom_cell, st_centroid(st_transform(wkb_geometry,4326)))) AS a
        WHERE pid = ogc_fid AND env.grid_id IS NULL;"""
cur.execute(sql3)
cur.close()
db.close()


# RETRIEVING PARCELS' EPSG FROM POSTGRES
db = connect(config.dbname)
cur = db.cursor()
cur.execute("""SELECT st_srid(wkb_geometry) FROM public.dk2021 LIMIT 1;""")
query_result = cur.fetchall()
cur.close()
db.close()

st_srid = query_result[0][0]


# ======================= RASTERS =======================

# SELECT AOI BOUNDING BOX FROM POSTGRESQL
db = connect(config.dbname)
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

aoi = data[data['name'] == 'dk2021']
x_min, x_max = int(aoi.iloc[0]['xmin']), int(aoi.iloc[0]['xmax'])
y_min, y_max = int(aoi.iloc[0]['ymin']), int(aoi.iloc[0]['ymax'])


# CREATE .VRT BASED ON BOUNDING BOX
dsmList = f.dsmListParser(range(x_min, x_max), range(y_min, y_max))
vrt = gdal.BuildVRT('temp/merged.vrt', dsmList)

#  GeoTransform Reference: [0]/[3] upper left long/lat, [1]/[5] cell width/height [5] negative in N emisphere
geotransform_0 = vrt.GetGeoTransform()
proj_0 = vrt.GetProjection()
print('====== BEFORE PROJECTION ======')
print(geotransform_0)
print(proj_0)

# Reproject to national metric projection and Resampling grid to 30m
dsReproj = gdal.Warp("temp/vrt_reproj.tif",
                     vrt,
                     dstSRS=f"EPSG:{st_srid}",
                     xRes=30,
                     yRes=30,
                     )

# CHECK PROJECTION CHANGE
print('====== AFTER PROJECTION ======')
geotransform = dsReproj.GetGeoTransform()
proj = dsReproj.GetProjection()
print(geotransform)
print(proj)

elev = rasterio.open(r'temp/vrt_reproj.tif', mode='r')

# APPLYING FUNCTION TO CALCULATE SLOPE AND ASPECT FROM DSM, RETRIEVING BANDS
print('====== CREATING SLOPE ======')
slope = f.calculateSlope('temp/vrt_reproj.tif')

print('====== CREATING ASPECT ======')
aspect = f.calculateAspect('temp/vrt_reproj.tif')

# ASSIGN VALUES TO NUMPY ARRAY AND CALCULATE GEOTRANSFORM/AFFINE
elev_array = elev.read(1)
slope_array = slope.read(1)
aspect_array = aspect.read(1)
affine = elev.transform

# READING PARCELS FROM POSTGRES WITH GEOPANDAS
db_url = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.dbname}"
sql = """SELECT ogc_fid, wkb_geometry 
            FROM public.dk2021 
            INNER JOIN public.env 
            ON ogc_fid = pid 
            WHERE elevmean IS null"""

engine = create_engine(db_url)
conn = engine.connect().execution_options(stream_results=True)

chunk = 1
for chunk_df in gpd.read_postgis(sql, conn, geom_col='wkb_geometry', chunksize=1000):
    print(f"====== EXECUTING RASTERSTATS {chunk} ======")
    print("Elevation")
    zstats_elev = rasterstats.zonal_stats(chunk_df,
                                          elev_array,
                                          affine=affine,
                                          all_touched=True,
                                          nodata=-9999,
                                          stats=['range', 'count'],
                                          add_stats={'mean': f.getMean},
                                          prefix='elev',
                                          geojson_out=True)

    print("Slope")
    zstats_slope = rasterstats.zonal_stats(chunk_df,
                                           slope_array,
                                           affine=affine,
                                           all_touched=True,
                                           nodata=-9999,
                                           stats=['mean'],
                                           add_stats={'mean': f.getMean},
                                           prefix='slope',
                                           geojson_out=True)

    print("Aspect")
    zstats_aspect = rasterstats.zonal_stats(chunk_df,
                                            aspect_array,
                                            affine=affine,
                                            all_touched=True,
                                            nodata=-9999,
                                            stats=['count'],
                                            add_stats={'mean': f.getCircularMean},
                                            prefix='aspect',
                                            geojson_out=True)

    print("====== CREATING DATAFRAME ======")
    zstats_elev_list = [item['properties'] for item in zstats_elev]
    elev_df = pd.DataFrame(zstats_elev_list)

    zstats_slope_list = [item['properties'] for item in zstats_slope]
    slope_df = pd.DataFrame(zstats_slope_list)

    zstats_aspect_list = [item['properties'] for item in zstats_aspect]
    aspect_df = pd.DataFrame(zstats_aspect_list)

    first_merge_parcel_list = pd.merge(elev_df, slope_df, on='ogc_fid', how='inner', )
    parcel_list = pd.merge(first_merge_parcel_list, aspect_df, on='ogc_fid', how='inner', )
    df = parcel_list.rename(columns={'ogc_fid': 'pid'})

    # WRITING DATA TO POSTGRES
    # df.to_sql(con=engine, schema='public', name='env', if_exists='fail', index=False)
    db = connect(config.dbname)
    db.autocommit = True
    cur = db.cursor()

    print("Saving to POSTGRESQL")

    tpls = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(list(df.columns))

    sql = """INSERT INTO %s(%s) VALUES %%s
                    ON CONFLICT ON CONSTRAINT env_pkey
                    DO UPDATE SET
                    elevmean = excluded.elevmean,
                    elevrange = excluded.elevrange,
                    elevcount = excluded.elevcount,
                    slopemean = excluded.slopemean,
                    aspectmean = excluded.aspectmean,
                    aspectcount = excluded.aspectcount;""" \
          % ('public.env', cols)
    cur = db.cursor()
    psycopg2.extras.execute_values(cur, sql, tpls)

    cur.close()
    db.close()
    chunk += 1
    print("Saving complete")

conn.close()
