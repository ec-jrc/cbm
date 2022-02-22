import pandas as pd


def get_data_query(cursor):
    cursor.execute("""SELECT name, start_date, end_date, n, o, s, e 
                    FROM public.view_era5_download_parameters;""")
    query_result = cursor.fetchall()
    col = []
    for x in cursor.description:
        col.append(x[0])
    test_data = pd.DataFrame(data=query_result, columns=col)
    return query_result, test_data


def era5_grid_query(cursor, aoi):
    cursor.execute("""SELECT grid_id,x AS longs, y AS lats
                    FROM public.aois, public.era5_grid
                    WHERE st_intersects(wkb_geometry, geom_cell)
                    AND name = '{}';""".format(aoi['name']))
    test_data_db = cursor.fetchall()
    col = []
    for x in cursor.description:
        col.append(x[0])
    grid_era5 = pd.DataFrame(data=test_data_db, columns=col)
    return grid_era5



