/* **********************************************

ASSUMPTIONS

- Data structure is based on specifications defined in file specs_data_submission_nov_2023.pdf
available on QUAP at https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf

- Data is stored in a PostgreSQL database having spatial PostGIS extension enabled.

- Required set of 5 tables:

CREATE TABLE lpis_population_2023 (
    gsa_code TEXT NOT NULL,
    lpis_code TEXT NOT NULL,
    lpis_rp_id TEXT NOT NULL,
    tot_area NUMERIC,
    al_area NUMERIC,
    pc_area NUMERIC,
    pg_area NUMERIC,
    na_area NUMERIC,
    af_area NUMERIC,
    n2000_area NUMERIC,
    pw_area NUMERIC,
    lf_area NUMERIC,
    anc_area NUMERIC,
    avail_area BOOLEAN,
    geom_4326 GEOMETRY(MultiPolygon, 4326),
    geom_3035 GEOMETRY(MultiPolygon, 3035),
    CONSTRAINT lpis_population_2023_pkey PRIMARY KEY (gsa_code, lpis_code, lpis_rp_id)
);

CREATE TABLE gsa_population_2023 (
    gsa_code TEXT NOT NULL,
    gsa_par_id TEXT NOT NULL,
    gsa_hol_id TEXT,
    gsa_col_id TEXT,
    main_crop TEXT,
    catch_crop TEXT,
    organic BOOLEAN,
    geom_4326 GEOMETRY(MultiPolygon, 4326),
    geom_3035 GEOMETRY(MultiPolygon, 3035),
    CONSTRAINT gsa_population_2023_pkey PRIMARY KEY (gsa_code, gsa_par_id)
);

CREATE TABLE gsa_lpis_relationship_2023 (
    gsa_code TEXT NOT NULL,
    lpis_code TEXT NOT NULL,
    lpis_rp_id TEXT NOT NULL,
    gsa_par_id TEXT NOT NULL,
    CONSTRAINT gsa_lpis_relationship_2023_pkey PRIMARY KEY (gsa_code, lpis_code, lpis_rp_id, gsa_par_id)
);

CREATE TABLE gsa_ua_claimed_2023 (
    gsa_code TEXT NOT NULL,
    gsa_par_id TEXT NOT NULL,
    ua TEXT NOT NULL,
    claim_area NUMERIC NOT NULL,
    CONSTRAINT gsa_ua_claimed_2023_pkey PRIMARY KEY (gsa_code, gsa_par_id, ua)
);

CREATE TABLE interventions_2023 (
    gsa_code TEXT NOT NULL,
    ua TEXT NOT NULL,
    ua_grp TEXT NOT NULL,
    interv TEXT NOT NULL,
    interv_lev TEXT NOT NULL,
    interv_typ TEXT NOT NULL,
    ua_grp_id INTEGER,
    CONSTRAINT interventions_2023_pkey PRIMARY KEY (gsa_code, ua)
);

********************************************** */


-- check if geometries are well-formed and valid according to the OGC Simple Features Implementation Specification for SQL 1.1
SELECT count(*) AS lpis_notvalid_geom_cnt
FROM lpis_population_2023
WHERE NOT ST_IsValid(geom_4326);

SELECT count(*) AS gsa_notvalid_geom_cnt
FROM gsa_population_2023
WHERE NOT ST_IsValid(geom_4326)


-- check for missing geometries
SELECT count(*) AS lpis_missing_geom_cnt
FROM lpis_population_2023
WHERE geom_4326 IS NULL

SELECT count(*) AS gsa_missing_geom_cnt
FROM gsa_population_2023
WHERE geom_4326 IS NULL


-- check for empty geometries
SELECT count(*) AS lpis_empty_geom_cnt
FROM lpis_population_2023
WHERE ST_IsEmpty(geom_4326)

SELECT count(*) AS gsa_empty_geom_cnt
FROM gsa_population_2023
WHERE ST_IsEmpty(geom_4326)


-- check for duplicated geometries
SELECT lpis_code, geom_4326, count(*) AS lpis_dup_geom_cnt, string_agg(lpis_rp_id, ', ') AS dup_id_list
FROM lpis_population_2023
GROUP BY lpis_code, geom_4326
HAVING count(*) > 1

SELECT geom_4326, count(*) AS gsa_dup_geom_cnt, string_agg(gsa_par_id, ', ') AS dup_id_list
FROM gsa_population_2023
GROUP BY geom_4326
HAVING count(*) > 1


-- check for overlapping geometries
SELECT ST_Collect(a.geom_4326, b.geom_4326), count(*) AS lpis_overlap_geom_cnt, string_agg(a.lpis_rp_id || ', ' || b.lpis_rp_id, '') AS overlap_id_list
FROM lpis_population_2023 a, lpis_population_2023 b 
WHERE a.geom_4326 && b.geom_4326
AND ST_Overlaps(a.geom_4326, b.geom_4326)
AND a.ctid != b.ctid
AND a.lpis_rp_id < b.lpis_rp_id
GROUP BY ST_Collect(a.geom_4326, b.geom_4326)

SELECT ST_Collect(a.geom_4326, b.geom_4326), count(*) AS gsa_overlap_geom_cnt, string_agg(a.gsa_par_id || ', ' || b.gsa_par_id, '') AS overlap_id_list
FROM gsa_population_2023 a, gsa_population_2023 b 
WHERE a.geom_4326 && b.geom_4326
AND ST_Overlaps(a.geom_4326, b.geom_4326)
AND a.ctid != b.ctid
AND a.gsa_par_id < b.gsa_par_id
GROUP BY ST_Collect(a.geom_4326, b.geom_4326)


-- check for GSA parcels that are completely outside their related LPIS parcel
SELECT count(*) AS gsa_outside_lpis_cnt
FROM gsa_lpis_relationship_2023 ab
JOIN lpis_population_2023 a ON (a.lpis_rp_id=ab.lpis_rp_id AND a.lpis_code=ab.lpis_code)
JOIN gsa_population_2023 b ON (b.gsa_par_id=ab.gsa_par_id)
WHERE ST_Disjoint(a.geom_4326, b.geom_4326)


-- check for GSA parcels having area bigger than their related LPIS parcel
SELECT count(*) AS gsa_bigger_than_lpis_cnt
FROM gsa_lpis_relationship_2023 ab
JOIN gsa_population_2023 a ON (a.gsa_par_id=ab.gsa_par_id)
JOIN lpis_population_2023 b ON (b.lpis_rp_id=ab.lpis_rp_id AND b.lpis_code=ab.lpis_code)
WHERE round(ST_Area(a.geom_3035)::NUMERIC, 0) > round(ST_Area(b.geom_3035)::NUMERIC, 0)


-- check for GSA parcels that are not fully contained inside the related LPIS parcel
SELECT count(*) AS gsa_not_fully_inside_lpis_cnt
FROM gsa_lpis_relationship_2023 ab
JOIN lpis_population_2023 a ON (a.lpis_rp_id=ab.lpis_rp_id AND a.lpis_code=ab.lpis_code)
JOIN gsa_population_2023 b ON (b.gsa_par_id=ab.gsa_par_id)
WHERE NOT ST_Disjoint(a.geom_4326, b.geom_4326)
	AND NOT ST_Covers(a.geom_4326, b.geom_4326)
	AND round(ST_Area(b.geom_3035)::NUMERIC, 0) <= round(ST_Area(a.geom_3035)::NUMERIC, 0)
	AND round(((100/ST_Area(b.geom_3035))*ST_Area(ST_Intersection(a.geom_3035, b.geom_3035)))::NUMERIC, 0) < 90


-- check for number of GSA parcels (centroids) inside LPIS parcel and their occurrence
WITH gsa_cnt AS (
	SELECT ab.lpis_rp_id, count(*) AS gsa_centroids_per_lpis_cnt
	FROM gsa_lpis_relationship_2023 ab
	JOIN lpis_population_2023 a ON (a.lpis_rp_id=ab.lpis_rp_id AND a.lpis_code=ab.lpis_code)
	JOIN gsa_population_2023 b ON (b.gsa_par_id=ab.gsa_par_id)
	WHERE ST_Covers(a.geom_3035, ST_PointOnSurface(b.geom_3035))
	GROUP BY ab.lpis_rp_id
)
SELECT gsa_centroids_per_lpis_cnt, count(*) AS occurrence
FROM gsa_cnt
GROUP BY gsa_centroids_per_lpis_cnt
ORDER BY gsa_centroids_per_lpis_cnt DESC


-- check statistics of GSA parcels (centroids) inside LPIS parcel
WITH list AS (
	WITH gsa_cnt AS (
		SELECT ab.lpis_rp_id, count(*) AS gsa_centroids_per_lpis_cnt
		FROM gsa_lpis_relationship_2023 ab
		JOIN lpis_population_2023 a ON (a.lpis_rp_id=ab.lpis_rp_id AND a.lpis_code=ab.lpis_code)
		JOIN gsa_population_2023 b ON (b.gsa_par_id=ab.gsa_par_id)
		WHERE ST_Covers(a.geom_3035, ST_PointOnSurface(b.geom_3035))
		GROUP BY ab.lpis_rp_id
	)
	SELECT gsa_centroids_per_lpis_cnt, count(*) AS occurrence
	FROM gsa_cnt
	GROUP BY gsa_centroids_per_lpis_cnt
	ORDER BY gsa_centroids_per_lpis_cnt DESC
)
SELECT
	max(gsa_centroids_per_lpis_cnt) AS max_gsa_in_lpis,
	min(gsa_centroids_per_lpis_cnt) AS min_gsa_in_lpis,
	sum(gsa_centroids_per_lpis_cnt*occurrence) AS gsa_tot_parcels,
	sum(occurrence) AS lpis_tot_parcels,
	round(sum(occurrence)/sum(gsa_centroids_per_lpis_cnt*occurrence), 2) AS avg_gsa_in_lpis
FROM list


-- check if LPIS area values (al_area, pc_area, pg_area, na_area, af_area, n2000_area, pw_area, lf_area, anc_area) >= 0 AND <= tot_area
SELECT count(*) AS invalid_al_area
FROM lpis_population_2023
WHERE (al_area < 0 OR round((al_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((al_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0

SELECT count(*) AS invalid_pc_area
FROM lpis_population_2023
WHERE (pc_area < 0 OR round((pc_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((pc_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0

SELECT count(*) AS invalid_pg_area
FROM lpis_population_2023
WHERE (pg_area < 0 OR round((pg_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((pg_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0

SELECT count(*) AS invalid_na_area
FROM lpis_population_2023
WHERE (na_area < 0 OR round((na_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((na_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0

SELECT count(*) AS invalid_af_area
FROM lpis_population_2023
WHERE (af_area < 0 OR round((af_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((af_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0

SELECT count(*) AS invalid_n2000_area
FROM lpis_population_2023
WHERE (n2000_area < 0 OR round((n2000_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((n2000_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0

SELECT count(*) AS invalid_pw_area
FROM lpis_population_2023
WHERE (pw_area < 0 OR round((pw_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((pw_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0

SELECT count(*) AS invalid_lf_area
FROM lpis_population_2023
WHERE (lf_area < 0 OR round((lf_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((lf_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0

SELECT count(*) AS invalid_anc_area
FROM lpis_population_2023
WHERE (anc_area < 0 OR round((anc_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
AND round((anc_area - tot_area)::NUMERIC, 3) > 0.001
AND tot_area > 0


-- check if LPIS tot_area < 0
SELECT count(*) AS invalid_negative_tot_area
FROM lpis_population_2023
WHERE tot_area < 0


-- check if LPIS tot_area = 0 (it can be 0 only when na_area > 0) 
SELECT count(*) AS invalid_zero_tot_area
FROM lpis_population_2023
WHERE tot_area = 0
AND na_area <= 0


-- check if LPIS tot_area >= (al_area + pc_area + pg_area)
SELECT count(*) AS invalid_alpcpg_area
FROM lpis_population_2023
WHERE round(tot_area::NUMERIC, 3) < round((al_area + pc_area + pg_area)::NUMERIC, 3)
AND tot_area > 0
AND round((al_area + pc_area + pg_area - tot_area)::NUMERIC, 3) > 0.001


-- check if LPIS tot_area > lpis_geom.area (area calculated from given polygon)
SELECT count(*) AS invalid_tot_area
FROM lpis_population_2023
WHERE tot_area > round(ST_Area(geom_3035)::NUMERIC, 4)
AND tot_area > 0


-- check if GSA claim_area <= 0
SELECT count(*) AS invalid_claim_area
FROM gsa_ua_claimed_2023
WHERE claim_area <= 0


-- check if GSA claim_area > gsa_geom.area (area calculated from given polygon)
SELECT count(*) AS invalid_claim_area
FROM gsa_ua_claimed_2023 ua
JOIN gsa_population_2023 gp USING (gsa_code, gsa_par_id)
WHERE ua.claim_area > round(ST_Area(gp.geom_3035)::NUMERIC, 4)
AND ua.claim_area > 0
AND round(ST_Area(gp.geom_3035)::NUMERIC, 4) > 0


-- check for Unit Amount declared but not claimed
SELECT count(*) AS unclaimed_ua_cnt
FROM interventions_2023 a
LEFT JOIN gsa_ua_claimed_2023 b USING (gsa_code, ua)
WHERE b.ua IS NULL


-- check the number of UA per group of UA
WITH uagrp AS (
	SELECT ua_grp, count(*) AS ua_per_group
	FROM interventions_2023
	GROUP BY ua_grp
	ORDER BY ua_per_group DESC
)
SELECT count(*) AS ua_grp_cnt, max(ua_per_group) AS max_ua_per_group, min(ua_per_group) AS min_ua_per_group, round(avg(ua_per_group), 2) AS avg_ua_per_group
FROM uagrp


-- check the number of Group of UA per Interventions
WITH intgrp AS (
	WITH uagrp AS (
		SELECT interv, ua_grp, count(*) AS ua_grp_cnt
		FROM sampling_2024.interventions_2023_lu
		GROUP BY interv, ua_grp
		ORDER BY interv DESC, ua_grp_cnt DESC
	)
	SELECT interv, sum(ua_grp_cnt) AS ua_grp_per_interv
	FROM uagrp
	GROUP BY interv
	ORDER BY ua_grp_per_interv DESC
)
SELECT count(*) AS interv_cnt, max(ua_grp_per_interv) AS max_ua_grp_per_interv, min(ua_grp_per_interv) AS min_ua_grp_per_interv, round(avg(ua_grp_per_interv), 2) AS avg_ua_grp_per_interv
FROM intgrp
