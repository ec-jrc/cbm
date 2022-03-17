import os
import utils.queries as q
from utils.connector import connect
from utils.get_era5_function import get_era5
import psycopg2
import psycopg2.extras as extras
import netCDF4 as nc
import xarray as xr
import pandas as pd
from datetime import datetime, timedelta

# COLLECTING DATA FROM POSTGRESQL
db = connect('postgres')
cur = db.cursor()
query_result = q.get_data_query(cur)
cur.close()
db.close()

aois = []
for row in query_result:
    aoi = {
        'name': row[0],
        'start_date': row[1],
        'end_date': row[2],
        'area': [row[3], row[4], row[5], row[6]]
    }
    aois.append(aoi)

print(aoi['end_date'])

# CREATE DOWNLOAD DIRECTORY
download_dir = "download/"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)


def last_day_of_month(day):
    """this function calculates the last day of a month in a given datetime format"""
    next_month = day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


# DOWNLOADING DATA FROM CDS
for aoi in aois:
    print("=========================================================")
    date_range = pd.date_range(start=aoi['start_date'], end=last_day_of_month(aoi['end_date']), freq='M')
    dates = {str(d): [('' if m.month >= 10 else '0') + str(m.month) for m in date_range if m.year == d]
             for d in date_range.year}

    for year in dates.keys():
        months = dates[year]
        date_range = []
        longitudes = []
        latitudes = []
        tmax = []
        tmin = []
        tmean = []
        rain = []

        for month in range(len(months)):
            filename = f"{aoi['name']}-{year}-{months[month]}"
            print(f"Downloading {filename} - {aoi['area']}")

            get_era5(
                dataset_name='reanalysis-era5-single-levels',
                var=['2m_temperature', 'total_precipitation'],
                year=year,
                month=months[month],
                grid=[0.25, 0.25],
                area=aoi['area'],
                download_file=f"download/{filename}.nc"
            )

            # READ DATA WITH XARRAY AND REMOVE EXPVER DIMENSION IF PRESENT
            # some cds data comes with an expver values, if they're from different sources, for more info see:
            # https://confluence.ecmwf.int/display/CUSF/ERA5+CDS+requests+which+return+a+mixture+of+ERA5+and+ERA5T+data
            # expver==5 is the one we need (expver==1 is Null)
            print(f"Reading and resampling data for {filename}")
            ds = xr.open_dataset(f"{download_dir}{filename}.nc")
            if 'expver' in ds.dims:
                ds = ds.drop_sel(expver=[1])

            # RESAMPLING TO DAILY DATA AND CONVERT UNITS (from K to °C and from m to mm)
            t2m = ds['t2m']
            tmax_daily = t2m.resample(time='D').max('time') - 273.15
            tmin_daily = t2m.resample(time='D').min('time') - 273.15
            tmean_daily = t2m.resample(time='D').mean('time') - 273.15
            tp = ds['tp']
            tp_daily = tp.resample(time='D').sum('time') * 1000

            # CREATE COORDINATES LIST (for time, long, lat)
            times = ds.time.resample(time='D').min()
            daily = ds.resample(time='1D').min('time')
            daily.to_netcdf('temp/daily.nc')
            daily_data = nc.Dataset('temp/daily.nc', 'r')
            times = daily_data.variables['time'][:]
            time_unit = daily_data.variables['time'].units
            longs = daily_data.variables['longitude'][:]
            lats = daily_data.variables['latitude'][:]
            daily_data.close()
            longlat = [[long, lat] for long in longs for lat in lats]

            # CREATE TIME SERIES
            print("Creating time series")

            ref_date = datetime(int(time_unit[11:15]), int(time_unit[16:18]), int(time_unit[19:21]))

            for coords in longlat:
                lon = coords[0]
                lat = coords[1]

                for time in times:
                    date_time = ref_date + timedelta(days=int(time))
                    date_range.append(date_time)
                    longitudes.append(lon)
                    latitudes.append(lat)
                    tmax.append(
                        round(float(tmax_daily.sel(longitude=lon, latitude=lat, time=date_time)),
                              1))
                    tmin.append(
                        round(float(tmin_daily.sel(longitude=lon, latitude=lat, time=date_time)),
                              1))
                    tmean.append(
                        round(float(tmean_daily.sel(longitude=lon, latitude=lat, time=date_time)),
                              1))
                    rain.append(
                        round(float(tp_daily.sel(longitude=lon, latitude=lat, time=date_time)),
                              1))

        # CREATE DATA FRAME
        print("CREATING DATA FRAME")
        df = pd.DataFrame(date_range, columns=['meteo_date'])
        df['longs'] = longitudes
        df['lats'] = latitudes
        df['meteo_date'] = date_range
        df['tmin'] = tmin
        df['tmax'] = tmax
        df['tmean'] = tmean
        df['prec'] = rain

        # # SAVING DF TO .CSV FILE
        # ts_dir = 'Time_Series/'
        # if not os.path.exists(ts_dir):
        #     os.makedirs(ts_dir)
        # print(f"Saving {aoi['name']}")
        # df.to_csv(os.path.join(ts_dir, f"{aoi['name']}.csv"), index=True)
        # print('Saving complete')

        # GATHER ERA5_GRID DATA TO JOIN
        db = connect('postgres')
        cur = db.cursor()
        grid_era5 = q.era5_grid_query(cur, aoi)
        cur.close()
        db.close()

        df2 = pd.merge(grid_era5, df, on=['longs', 'lats']).drop('longs', axis=1).drop('lats', axis=1)

        # SAVING DF TO POSTGRESQL
        print("Saving to POSTGRESQL")

        tpls = [tuple(x) for x in df2.to_numpy()]
        cols = ','.join(list(df2.columns))
        conn = None

        db = connect('postgres')
        db.autocommit = True
        sql = """INSERT INTO %s(%s) VALUES %%s 
                ON CONFLICT ON CONSTRAINT era5_data_pkey 
                DO UPDATE SET 
                tmin = excluded.tmin,
                tmax = excluded.tmax,
                tmean = excluded.tmean,
                prec = excluded.prec;""" % ('public.era5_data', cols)
        cur = db.cursor()
        psycopg2.extras.execute_values(cur, sql, tpls)
        cur.close()
        db.close()
        print("Saving complete")

print("====== PROCESS COMPLETE ======")
