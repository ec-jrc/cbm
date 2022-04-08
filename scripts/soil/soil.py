import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio
import rasterstats
import psycopg2
import psycopg2.extras as extras
from sqlalchemy import create_engine
from osgeo import gdal
from utils import config
from utils.connector import connect

ref_link = "https://www.isric.org/explore/world-soil-distribution"

# TODO add creation of download folder

db = connect(config.dbname)
cur = db.cursor()
cur.execute("""SELECT st_srid(wkb_geometry) FROM public.dk2021 LIMIT 1;""")
query_result = cur.fetchall()
cur.close()
db.close()

st_srid = query_result[0][0]

# TODO extract bounding box from postgres
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

bb = (x_min, y_max, x_max, y_min)
print(bb)
exit()
bb = (7.0, 58.0, 16.0, 54.0) # WNES


igh = "+proj=longlat +datum=WGS84 +no_defs"
res = 250
folders_filenames = {
    "clay": {"https://files.isric.org/soilgrids/latest/data/clay/": "clay_0-5cm_mean.vrt"},  # clay -> g/Kg
    "sand": {"https://files.isric.org/soilgrids/latest/data/sand/": "sand_0-5cm_mean.vrt"},  # sand -> g/Kg
    "silt": {"https://files.isric.org/soilgrids/latest/data/silt/": "silt_0-5cm_mean.vrt"},  # silt -> g/Kg
    "ph_water": {"https://files.isric.org/soilgrids/latest/data/phh2o/": "phh2o_0-5cm_mean.vrt"},  # ph_water -> pH * 10
    "c_exc_cap": {"https://files.isric.org/soilgrids/latest/data/cec/": "cec_0-5cm_mean.vrt"},  # cec -> mmol(c)/kg
    "oc_stock": {"https://files.isric.org/soilgrids/latest/data/ocs/": "ocs_0-30cm_mean.vrt"},  # ocs -> dg/kg
    "oc_dens": {"https://files.isric.org/soilgrids/latest/data/ocd/": "ocd_0-5cm_mean.vrt"},  # ocd -> g/dm3
    "bulk_dens": {"https://files.isric.org/soilgrids/latest/data/bdod/": "bdod_0-5cm_mean.vrt"},  # bulk_dens -> cg/cm3
    "soil_class": {"https://files.isric.org/soilgrids/latest/data/wrb/": "MostProbable_152160.vrt"},
    }

db_url = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.dbname}"

for k, v in folders_filenames.items():
    prop = k
    for k2, v2 in v.items():
        location = k2
        filename = v2
        outname = filename[:-4]
    print(f'{prop} - {location}{filename}')

    sg_url = f"/vsicurl?max_retry=3&retry_delay=1&list_dir=no&url={location}{filename}"
    kwargs = {'format': 'GTiff', 'projWin': bb, 'projWinSRS': igh, 'xRes': res, 'yRes': res}

    ds = gdal.Translate(f'download/{filename}',
                        f'{sg_url}',
                        **kwargs)

    dstNodata = 255 if prop == 'soil_class' else -999

    ds = gdal.Warp(f'download/{outname}_{st_srid}.vrt',
                   f'download/{filename}',
                   dstNodata=dstNodata,
                   dstSRS=f'EPSG:{st_srid}',)

    soil = rasterio.open(f'download/{outname}_{st_srid}.vrt', mode='r')
    soil_array = soil.read(1, masked=True)
    affine = soil.transform

    sql = f"""SELECT ogc_fid, wkb_geometry 
                FROM public.dk2021
                INNER JOIN public.env
                ON ogc_fid = pid
                WHERE {prop} is Null"""

    engine = create_engine(db_url)
    conn = engine.connect().execution_options(stream_results=True)

    if prop == "soil_class":
        print('calculating rasterstats for soil classification')
        chunk = 0
        for chunk_df in gpd.read_postgis(sql, conn, geom_col='wkb_geometry', chunksize=5000):

            zstats_soil = rasterstats.zonal_stats(chunk_df,
                                                  soil_array,
                                                  affine=affine,
                                                  nodata=255,
                                                  all_touched=True,
                                                  stats=['majority'],
                                                  geojson_out=True)

            zstats_soil_list = [item['properties'] for item in zstats_soil]

            soil_classes = {0: 'Acrisols', 1: 'Albeluvisols', 2: 'Alisols', 3: 'Andosols', 4: 'Arenosols',
                            5: 'Calcisols', 6: 'Cambisols', 7: 'Chernozems', 8: 'Cryosols', 9: 'Durisols',
                            10: 'Ferralsols', 11: 'Fluvisols', 12: 'Gleysols', 13: 'Gypsisols', 14: 'Histosols',
                            15: 'Kastanozems', 16: 'Leptosols', 17: 'Lixisols', 18: 'Luvisols', 19: 'Nitisols',
                            20: 'Phaeozems', 21: 'Planosols', 22: 'Plinthosols', 23: 'Podzols', 24: 'Regosols',
                            25: 'Solonchaks', 26: 'Solonetz', 27: 'Stagnosols', 28: 'Umbrisols', 29: 'Vertisols',
                            255: None,
                            None: None}

            soil_df = pd.DataFrame(zstats_soil_list)
            soil_df = soil_df.replace({np.nan:None})
            soil_df['soil_class'] = soil_df['majority'].map(soil_classes)
            soil_df.drop('majority', inplace=True, axis=1)

            df = soil_df.rename(columns={'ogc_fid': 'pid'})

            db = connect(config.dbname)
            db.autocommit = True
            cur = db.cursor()

            print(f"Saving to POSTGRESQL {chunk}")

            tpls = [tuple(x) for x in df.to_numpy()]
            cols = ','.join(list(df.columns))

            sql = f"""INSERT INTO %s(%s) VALUES %%s
                                ON CONFLICT ON CONSTRAINT env_pkey
                                DO UPDATE SET
                                {prop} = excluded.{prop};""" \
                  % ('public.env', cols)
            cur = db.cursor()
            psycopg2.extras.execute_values(cur, sql, tpls)

            cur.close()
            db.close()
            chunk += 5000

        conn.close()

    elif prop == "ph_water":
        print('calculating rasterstats for pH water')
        chunk = 0
        for chunk_df in gpd.read_postgis(sql, conn, geom_col='wkb_geometry', chunksize=5000):

            zstats_soil = rasterstats.zonal_stats(chunk_df,
                                                  soil_array,
                                                  affine=affine,
                                                  nodata=-999,
                                                  all_touched=True,
                                                  stats=['mean'],
                                                  geojson_out=True)

            zstats_soil_list = [item['properties'] for item in zstats_soil]

            soil_df = pd.DataFrame(zstats_soil_list)
            soil_df['mean'] = soil_df['mean'] * 0.1
            soil_df = soil_df.replace({np.nan: None})
            df = soil_df.rename(columns={'ogc_fid': 'pid', 'mean': f'{prop}'})

            db = connect(config.dbname)
            db.autocommit = True
            cur = db.cursor()

            print(f"Saving to POSTGRESQL {chunk}")

            tpls = [tuple(x) for x in df.to_numpy()]
            cols = ','.join(list(df.columns))

            sql = f"""INSERT INTO %s(%s) VALUES %%s
                        ON CONFLICT ON CONSTRAINT env_pkey
                        DO UPDATE SET
                        {prop} = excluded.{prop};""" \
                  % ('public.env', cols)
            cur = db.cursor()
            psycopg2.extras.execute_values(cur, sql, tpls)

            cur.close()
            db.close()
            chunk += 5000

        conn.close()

    else:
        print(f'calculating rasterstats for {prop}')
        chunk = 0
        for chunk_df in gpd.read_postgis(sql, conn, geom_col='wkb_geometry', chunksize=5000):

            zstats_soil = rasterstats.zonal_stats(chunk_df,
                                                  soil_array,
                                                  affine=affine,
                                                  nodata=-999,
                                                  all_touched=True,
                                                  stats=['mean'],
                                                  geojson_out=True)

            zstats_soil_list = [item['properties'] for item in zstats_soil]

            soil_df = pd.DataFrame(zstats_soil_list)
            soil_df = soil_df.replace({np.nan: None})

            df = soil_df.rename(columns={'ogc_fid': 'pid', 'mean': f'{prop}'})

            db = connect(config.dbname)
            db.autocommit = True
            cur = db.cursor()

            print(f"Saving to POSTGRESQL {chunk}")

            tpls = [tuple(x) for x in df.to_numpy()]
            cols = ','.join(list(df.columns))

            sql = f"""INSERT INTO %s(%s) VALUES %%s
                                ON CONFLICT ON CONSTRAINT env_pkey
                                DO UPDATE SET
                                {prop} = excluded.{prop};""" \
                  % ('public.env', cols)
            cur = db.cursor()
            psycopg2.extras.execute_values(cur, sql, tpls)

            cur.close()
            db.close()
            chunk += 5000

        conn.close()

print('process complete!')
