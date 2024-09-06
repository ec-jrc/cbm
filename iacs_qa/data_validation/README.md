# Data Validation Tool: First and Second Layer Checks

This repository provides tools for performing data consistency checks across two layers:

1. **First Layer**: Basic data checks (data types, null values, duplicates, etc.) using a Python script.
2. **Second Layer**: Spatial and database integrity checks using SQL queries on a PostgreSQL database with PostGIS enabled.

## First Layer Checks: Python Script

The first layer of checks is implemented in Python using the script `validator.py`. It focuses on basic consistency checks such as:
- Validating data types
- Checking for missing values
- Identifying duplicate rows
- Validating area-related columns

### How to Run the First Layer Checks

You can run the first layer checks via the command line using `typer`.

```bash
python validator.py run-processor --input-file <path_to_file> --table-type <table_type>
```

- `input-file`: The path to the file to be validated (e.g., CSV, Excel).
- `table-type`: The type of table being validated (e.g., `lpis`, `gsa`, etc.).

Example:

```bash
python validator.py run-processor --input-file ./data/lpis_data.csv --table-type lpis
```

For more information on the Python script, refer to [validator.py in the repository](https://github.com/ec-jrc/cbm/tree/main/scripts/data_validation).

## Second Layer Checks: SQL Script

The second layer checks are SQL-based and performed on a **PostgreSQL database** with **PostGIS** enabled. This script checks for:
- Geometry validity (well-formed and non-overlapping geometries)
- Missing or empty geometries
- Overlapping and duplicate geometries
- Spatial relationships between LPIS and GSA parcels
- Area consistency between declared and calculated values

### How to Run the Second Layer Checks

1. Ensure you have a **PostgreSQL** database with the **PostGIS** extension enabled.
2. Create the required tables using the structure defined in the [specifications](https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf).
3. Run the SQL queries provided in `second_layer_checks.sql` to perform the checks.

To execute the SQL checks:

```sql
-- Example to check for invalid geometries in LPIS data
SELECT count(*) AS lpis_notvalid_geom_cnt
FROM lpis_population_2023
WHERE NOT ST_IsValid(geom_4326);
```

You can find the full list of checks in the provided SQL file.

## References

- [Data Submission Specifications (November 2023)](https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Documentation](https://postgis.net/documentation/)


## Authors
- **ANASTASAKIS Konstantinos** – Python script (First layer checks)
- **ISOARDI Paolo** – SQL script (Second layer checks)

## License

This project is licensed under the [3-Clause BSD](https://opensource.org/licenses/BSD-3-Clause) license

---

Copyright (c) 2024, [European Commission](https://ec.europa.eu/), Joint Research Centre. All rights reserved.

