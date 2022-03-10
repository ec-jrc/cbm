query1 = """CREATE TABLE IF NOT EXISTS hu.env_2020
(
    pid integer NOT NULL,
    grid_id integer,
    elevmean integer,
    elevrange integer,
    elevcount integer,
	slopemean double precision,
    aspectmean double precision,
    aspectcount integer,
    CONSTRAINT env_2020_pkey PRIMARY KEY (pid),
    CONSTRAINT env_2020_era5_grid_fkey FOREIGN KEY (grid_id)
        REFERENCES public.era5_grid (grid_id),
    CONSTRAINT env_2020_parcels_fkey FOREIGN KEY (pid)
        REFERENCES hu.parcels_2020 (ogc_fid)
);
GRANT SELECT ON TABLE hu.env_2020 TO api_bot;
GRANT SELECT TABLE hu.env_2020 TO capland;"""

query2 = """INSERT into hu.env_2020 (pid)
SELECT ogc_fid FROM hu.parcels_2020;"""

query3 = """UPDATE hu.env_2020
SET grid_id = a.grid_id
FROM
 (SELECT grid_id, ogc_fid
    FROM hu.parcels_2020,public.era5_grid
    WHERE st_intersects(geom_cell, st_centroid(st_transform(wkb_geometry,4326)))) a
WHERE pid = ogc_fid AND env_2020.grid_id IS NULL;"""


# questa ultima ti serve per iterare per l'inizializzazione
query4 = """SELECT * FROM public.geometry_columns
where
f_table_name like 'parcels_%' and
f_table_name not like '%\_%\_%'
order by f_table_schema;"""