/* ********************************************************************************************

REQUIREMENTS

- Data structure is based on data specifications defined in document "IACS quality assessment data exchange in November 2023: Technical Specifications"
available on QUAP at https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf

- Data is organized in a PostgreSQL database having spatial PostGIS extension enabled.

- The SQL queries are based on the following set of 5 tables:

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

- NOTE: the additional field geom_3035, not described in the data specifications document, can be calculated from geom_4326 as geom_3035 = ST_Transform(geom_4326, 3035)

******************************************************************************************** */


-- The following queries check if geometries of the LPIS and GSA parcels are well-formed and valid according to the OGC Simple Features Implementation Specification for SQL 1.1
-- (for a list of possible issues see https://postgis.net/docs/using_postgis_dbmanagement.html#OGC_Validity).
SELECT count(*) AS lpis_notvalid_geom_cnt
FROM lpis_population_2023
WHERE NOT ST_IsValid(geom_4326);

SELECT count(*) AS gsa_notvalid_geom_cnt
FROM gsa_population_2023
WHERE NOT ST_IsValid(geom_4326);

	-- If the count of invalid geometries is positive, you can run the next queries to list the IDs of the LPIS and GSA parcels having invalid geometry, together with the reason of the invalidity.
	SELECT lpis_rp_id, geom_4326, ST_IsValidReason(geom_4326)
	FROM lpis_population_2023
	WHERE NOT ST_IsValid(geom_4326);
	
	SELECT gsa_par_id, geom_4326, ST_IsValidReason(geom_4326)
	FROM gsa_population_2023
	WHERE NOT ST_IsValid(geom_4326);


-- The following queries check LPIS and GSA parcels for missing geometries, namely null values of the geometric attribute.
SELECT count(*) AS lpis_missing_geom_cnt
FROM lpis_population_2023
WHERE geom_4326 IS NULL;

SELECT count(*) AS gsa_missing_geom_cnt
FROM gsa_population_2023
WHERE geom_4326 IS NULL;

	-- If the count of missing geometries is positive, you can run the next queries to list the IDs of the LPIS and GSA parcels with no geometry.
	SELECT lpis_rp_id
	FROM lpis_population_2023
	WHERE geom_4326 IS NULL;

	SELECT gsa_par_id
	FROM gsa_population_2023
	WHERE geom_4326 IS NULL;


-- The following queries check LPIS and GSA parcels for empty geometries, namely parcels where the geometry is present but it is empty, having a zero value area.
SELECT count(*) AS lpis_empty_geom_cnt
FROM lpis_population_2023
WHERE ST_IsEmpty(geom_4326);

SELECT count(*) AS gsa_empty_geom_cnt
FROM gsa_population_2023
WHERE ST_IsEmpty(geom_4326);

	-- If the count of empty geometries is positive, you can run the next queries to list the IDs of the LPIS and GSA parcels having zero area geometry.
	SELECT lpis_rp_id, ST_Area(geom_3035) AS area, ST_AsText(geom_4326) AS descr
	FROM lpis_population_2023
	WHERE ST_IsEmpty(geom_4326);
	
	SELECT gsa_par_id, ST_Area(geom_3035) AS area, ST_AsText(geom_4326) AS descr
	FROM gsa_population_2023
	WHERE ST_IsEmpty(geom_4326);


-- The following queries check LPIS and GSA parcels for duplicated geometries. The queries return the number of parcels sharing the same geometry.
WITH dc AS (
	SELECT geom_4326, count(*)
	FROM lpis_population_2023
	GROUP BY geom_4326
	HAVING count(*) > 1
)
SELECT count(*) AS lpis_dupl_geom_cnt
FROM dc;

WITH dc AS (
	SELECT geom_4326, count(*)
	FROM gsa_population_2023
	GROUP BY geom_4326
	HAVING count(*) > 1
)
SELECT count(*) AS gsa_dupl_geom_cnt
FROM dc;

	-- If the count of duplicated geometries is positive, you can run the next queries to list the IDs of the LPIS and GSA parcels sharing the same geometry.
	SELECT geom_4326,
		count(*) AS geom_cnt,
		string_agg(lpis_rp_id, ', ') AS lpis_dupl_id_list
	FROM lpis_population_2023
	GROUP BY geom_4326
	HAVING count(*) > 1;

	SELECT geom_4326,
		count(*) AS geom_cnt,
		string_agg(gsa_par_id, ', ') AS gsa_dupl_id_list
	FROM gsa_population_2023
	GROUP BY geom_4326
	HAVING count(*) > 1;


-- The following queries check LPIS and GSA parcels for overlapping geometries. The queries select only the cases where the overlap between two valid polygons is also a polygon, and exclude the overlaps with area < 10 square meters (this threshold can be adapted according to needs).
-- Please note that these queries may take a very long time to process.
SELECT count(*) AS lpis_overlap_cnt
FROM lpis_population_2023 a, lpis_population_2023 b 
WHERE a.geom_3035 && b.geom_3035
AND ST_Overlaps(a.geom_3035, b.geom_3035)
AND a.ctid != b.ctid
AND a.lpis_rp_id < b.lpis_rp_id
AND ST_GeometryType(ST_Intersection(a.geom_3035, b.geom_3035)) = 'ST_Polygon'
AND ST_Area(ST_Intersection(a.geom_3035, b.geom_3035)) > 10
AND ST_IsValid(a.geom_3035)
AND ST_IsValid(b.geom_3035);

SELECT count(*) AS gsa_overlap_cnt
FROM gsa_population_2023 a, gsa_population_2023 b 
WHERE a.geom_3035 && b.geom_3035
AND ST_Overlaps(a.geom_3035, b.geom_3035)
AND a.ctid != b.ctid
AND a.gsa_par_id < b.gsa_par_id
AND ST_GeometryType(ST_Intersection(a.geom_3035, b.geom_3035)) = 'ST_Polygon'
AND ST_Area(ST_Intersection(a.geom_3035, b.geom_3035)) > 10
AND ST_IsValid(a.geom_3035)
AND ST_IsValid(b.geom_3035);

	-- If the count of overlapping geometries is positive, you can run the next queries to list the IDs of the LPIS and GSA parcels sharing part of the geometry.
	SELECT ST_Collect(ARRAY[a.geom_3035, b.geom_3035, ST_Intersection(a.geom_3035, b.geom_3035)]), string_agg(a.lpis_rp_id || ', ' || b.lpis_rp_id, '') AS overlap_id_list
	FROM lpis_population_2023 a, lpis_population_2023 b 
	WHERE a.geom_3035 && b.geom_3035
	AND ST_Overlaps(a.geom_3035, b.geom_3035)
	AND a.ctid != b.ctid
	AND a.lpis_rp_id < b.lpis_rp_id
	AND ST_GeometryType(ST_Intersection(a.geom_3035, b.geom_3035)) = 'ST_Polygon'
	AND ST_Area(ST_Intersection(a.geom_3035, b.geom_3035)) > 10
	AND ST_IsValid(a.geom_3035)
	AND ST_IsValid(b.geom_3035)
	GROUP BY ST_Collect(ARRAY[a.geom_3035, b.geom_3035, ST_Intersection(a.geom_3035, b.geom_3035)]);

	SELECT ST_Collect(ARRAY[a.geom_3035, b.geom_3035, ST_Intersection(a.geom_3035, b.geom_3035)]), string_agg(a.gsa_par_id || ', ' || b.gsa_par_id, '') AS overlap_id_list
	FROM gsa_population_2023 a, gsa_population_2023 b 
	WHERE a.geom_3035 && b.geom_3035
	AND ST_Overlaps(a.geom_3035, b.geom_3035)
	AND a.ctid != b.ctid
	AND a.gsa_par_id < b.gsa_par_id
	AND ST_GeometryType(ST_Intersection(a.geom_3035, b.geom_3035)) = 'ST_Polygon'
	AND ST_Area(ST_Intersection(a.geom_3035, b.geom_3035)) > 10
	AND ST_IsValid(a.geom_3035)
	AND ST_IsValid(b.geom_3035)
	GROUP BY ST_Collect(ARRAY[a.geom_3035, b.geom_3035, ST_Intersection(a.geom_3035, b.geom_3035)]);


-- The following query checks if area attributes declared in LPIS population (al_area, pc_area, pg_area, na_area, af_area, n2000_area, pw_area, lf_area, anc_area) have valid values, i.e. between zero and the declared total area value.
-- All values are rounded to 3 decimals and area differences less than 10 square meters are excluded (this threshold can be adapted according to needs).
SELECT
	SUM(CASE WHEN ((al_area < 0 OR round((al_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3)) AND (round((al_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_al_area,
	SUM(CASE WHEN ((pc_area < 0 OR round((pc_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3)) AND (round((pc_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_pc_area,
	SUM(CASE WHEN ((pg_area < 0 OR round((pg_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))  AND (round((pg_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_pg_area,
	SUM(CASE WHEN ((na_area < 0 OR round((na_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))  AND (round((na_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_na_area,
	SUM(CASE WHEN ((af_area < 0 OR round((af_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))  AND (round((af_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_af_area,
	SUM(CASE WHEN ((n2000_area < 0 OR round((n2000_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))  AND (round((n2000_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_n2000_area,
	SUM(CASE WHEN ((pw_area < 0 OR round((pw_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))  AND (round((pw_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_pw_area,
	SUM(CASE WHEN ((lf_area < 0 OR round((lf_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))  AND (round((lf_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_lf_area,
	SUM(CASE WHEN ((anc_area < 0 OR round((anc_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))  AND (round((anc_area - tot_area)::NUMERIC, 3) > 0.001)) THEN 1 ELSE 0 END) AS invalid_anc_area
FROM lpis_population_2023
WHERE tot_area > 0;
	
	-- If the count of invalid area is positive, you can run the next queries to list the IDs of the LPIS parcels with supposed invalid area.
	-- The area values and their difference are also listed aside IDs. The results are finally sorted so that the cases where the area difference is largest are listed first.
	
	-- List of LPIS parcels with invalid_al_area.
	SELECT lpis_rp_id,
		round((al_area)::NUMERIC, 3) AS al_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((al_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (al_area < 0 OR round((al_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((al_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;

	-- List of LPIS parcels with invalid_pc_area.
	SELECT lpis_rp_id,
		round((pc_area)::NUMERIC, 3) AS pc_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((pc_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (pc_area < 0 OR round((pc_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((pc_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;

	-- List of LPIS parcels with invalid_pg_area.
	SELECT lpis_rp_id,
		round((pg_area)::NUMERIC, 3) AS pg_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((pg_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (pg_area < 0 OR round((pg_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((pg_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;

	-- List of LPIS parcels with invalid_na_area.
	SELECT lpis_rp_id,
		round((na_area)::NUMERIC, 3) AS na_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((na_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (na_area < 0 OR round((na_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((na_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;

	-- List of LPIS parcels with invalid_af_area.
	SELECT lpis_rp_id,
		round((af_area)::NUMERIC, 3) AS af_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((af_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (af_area < 0 OR round((af_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((af_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;

	-- List of LPIS parcels with invalid_n2000_area.
	SELECT lpis_rp_id,
		round((n2000_area)::NUMERIC, 3) AS n2000_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((n2000_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (n2000_area < 0 OR round((n2000_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((n2000_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;

	-- List of LPIS parcels with invalid_pw_area.
	SELECT lpis_rp_id,
		round((pw_area)::NUMERIC, 3) AS pw_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((pw_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (pw_area < 0 OR round((pw_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((pw_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;

	-- List of LPIS parcels with invalid_lf_area.
	SELECT lpis_rp_id,
		round((lf_area)::NUMERIC, 3) AS lf_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((lf_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (lf_area < 0 OR round((lf_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((lf_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;

	-- List of LPIS parcels with invalid_anc_area.
	SELECT lpis_rp_id,
		round((anc_area)::NUMERIC, 3) AS anc_area,
		round((tot_area)::NUMERIC, 3) AS tot_area,
		round((anc_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE (anc_area < 0 OR round((anc_area)::NUMERIC, 3) > round((tot_area)::NUMERIC, 3))
	AND round((anc_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;


-- The following query checks if LPIS parcels have invalid negative values of the tot_area attribute.
SELECT count(*) AS invalid_negative_tot_area
FROM lpis_population_2023
WHERE tot_area < 0;

	-- If the count of parcels with invalid_negative_tot_area is positive, you can run the next query to list the IDs of the LPIS parcels with negative area.
	SELECT lpis_rp_id,
		tot_area
	FROM lpis_population_2023
	WHERE tot_area < 0;


-- The following query checks if LPIS parcels have invalid zero values of the tot_area attribute. The total area attribute can equal zero only when the value of non-agricultural eligible area is bigger than zero.
SELECT count(*) AS invalid_zero_tot_area
FROM lpis_population_2023
WHERE tot_area = 0
AND na_area <= 0;

	-- If the count of parcels with invalid_zero_tot_area is positive, you can run the next query to list the IDs of the LPIS parcels with invalid zero values of the tot_area attribute.
	SELECT lpis_rp_id,
		tot_area,
		na_area
	FROM lpis_population_2023
	WHERE tot_area = 0
	AND na_area <= 0;


-- The following query checks if LPIS parcels have values of the tot_area attribute equal or bigger than the sum of al_area, pc_area and pg_area. Values are rounded to 3 decimals and area differences less than 10 square meters are excluded (this threshold can be adapted according to needs).
SELECT count(*) AS invalid_alpcpg_area
FROM lpis_population_2023
WHERE round(tot_area::NUMERIC, 3) < round((al_area + pc_area + pg_area)::NUMERIC, 3)
AND tot_area > 0
AND round((al_area + pc_area + pg_area - tot_area)::NUMERIC, 3) > 0.001;

	-- If the count of parcels with invalid_alpcpg_area is positive, you can run the next query to list the IDs of the LPIS parcels where the sum of al_area, pc_area and pg_area is bigger than the tot_area.
	-- The area values and their difference are also listed aside IDs. The results are finally sorted so that the cases where the area difference is largest are listed first.
	SELECT lpis_rp_id,
		round((al_area + pc_area + pg_area)::NUMERIC, 3) AS alpcpg_area,
		round(tot_area::NUMERIC, 3) AS tot_area,
		round((al_area + pc_area + pg_area - tot_area)::NUMERIC, 3) AS area_diff
	FROM lpis_population_2023
	WHERE round(tot_area::NUMERIC, 3) < round((al_area + pc_area + pg_area)::NUMERIC, 3)
	AND round((al_area + pc_area + pg_area - tot_area)::NUMERIC, 3) > 0.001
	AND tot_area > 0
	ORDER BY area_diff DESC;


--  The following query checks if the LPIS tot_area value declared is bigger than the geometric area calculated from the given LPIS polygon.
SELECT count(*) AS invalid_tot_area
FROM lpis_population_2023
WHERE tot_area > round(ST_Area(geom_3035)::NUMERIC, 4)
AND tot_area > 0;

	-- If the count of parcels with invalid_tot_area is positive, you can run the next query to list the IDs of the LPIS parcels where the tot_area is bigger than the geometric area.
	SELECT lpis_rp_id,
		tot_area,
		round(ST_Area(geom_3035)::NUMERIC, 4) AS geom_area,
		round((tot_area - ST_Area(geom_3035))::NUMERIC, 4) AS area_diff
	FROM lpis_population_2023
	WHERE tot_area > round(ST_Area(geom_3035)::NUMERIC, 4)
	AND tot_area > 0
	ORDER BY area_diff DESC;


--  The following query checks if the GSA claimed area attribute presents invalid negative or zero values.
SELECT count(*) AS invalid_zero_claim_area
FROM gsa_ua_claimed_2023
WHERE claim_area <= 0;

	-- If the count of GSA parcels with invalid_zero_claim_area is positive, you can run the next query to list the IDs of the parcels where the claim_area is less or equal to zero.
	SELECT gsa_par_id,
		claim_area
	FROM gsa_ua_claimed_2023
	WHERE claim_area <= 0;


--  The following query checks if the GSA claimed area attribute is bigger than the geometric area calculated from the given GSA polygon.
SELECT count(*) AS invalid_claim_area
FROM gsa_ua_claimed_2023 ua
JOIN gsa_population_2023 gp ON (ua.gsa_par_id = gp.gsa_par_id)
WHERE ua.claim_area > round(ST_Area(gp.geom_3035)::NUMERIC, 4)
AND ua.claim_area > 0
AND round(ST_Area(gp.geom_3035)::NUMERIC, 4) > 0;

	-- If the count of GSA parcels with invalid_claim_area is positive, you can run the next query to list the IDs of the parcels where the claim_area is bigger than the geometric area.
	SELECT ua.gsa_par_id,
		ua.claim_area,
		round(ST_Area(gp.geom_3035)::NUMERIC, 4) AS geom_area,
		round((claim_area - ST_Area(gp.geom_3035))::NUMERIC, 4) AS area_diff
	FROM gsa_ua_claimed_2023 ua
	JOIN gsa_population_2023 gp ON (ua.gsa_par_id = gp.gsa_par_id)
	WHERE ua.claim_area > round(ST_Area(gp.geom_3035)::NUMERIC, 4)
	AND ua.claim_area > 0
	AND round(ST_Area(gp.geom_3035)::NUMERIC, 4) > 0
	ORDER BY area_diff DESC;


--  The following query checks for Unit Amounts declared but not claimed, namely the Unit Amounts declared in the interventions table but then not listed in the list of units amount/interventions claimed for each GSA parcel.
SELECT count(*) AS unclaimed_ua_cnt
FROM interventions_2023 a
LEFT JOIN gsa_ua_claimed_2023 b ON (a.ua = b.ua)
WHERE b.ua IS NULL;

	-- If the count of unclaimed Unit Amounts is positive, you can run the next query to list them.
	SELECT a.ua
	FROM interventions_2023 a
	LEFT JOIN gsa_ua_claimed_2023 b ON (a.ua = b.ua)
	WHERE b.ua IS NULL;


--  The following query performs some basic statistics (minimum, maximum, average values) on the number of Unit Amounts declared per Group of Unit Amounts.
WITH uagrp AS (
	SELECT ua_grp, count(*) AS ua_per_group
	FROM interventions_2023
	GROUP BY ua_grp
	ORDER BY ua_per_group DESC
)
SELECT count(*) AS ua_grp_cnt, max(ua_per_group) AS max_ua_per_group, min(ua_per_group) AS min_ua_per_group, round(avg(ua_per_group), 2) AS avg_ua_per_group
FROM uagrp;


--  The following query runs some basic statistics (minimum, maximum, average values) on the number of Groups of Unit Amounts declared per Interventions.
WITH intgrp AS (
	WITH uagrp AS (
		SELECT interv, ua_grp, count(*) AS ua_grp_cnt
		FROM interventions_2023
		GROUP BY interv, ua_grp
		ORDER BY interv DESC, ua_grp_cnt DESC
	)
	SELECT interv, sum(ua_grp_cnt) AS ua_grp_per_interv
	FROM uagrp
	GROUP BY interv
	ORDER BY ua_grp_per_interv DESC
)
SELECT count(*) AS interv_cnt, max(ua_grp_per_interv) AS max_ua_grp_per_interv, min(ua_grp_per_interv) AS min_ua_grp_per_interv, round(avg(ua_grp_per_interv), 2) AS avg_ua_grp_per_interv
FROM intgrp;
