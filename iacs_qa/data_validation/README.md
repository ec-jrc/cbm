# Data Validation Tools

This repository provides tools for performing data consistency checks with two methods:

1. **File Validations**: Basic checks on data files (e.g., CSV, GPKG, SHP) using a Python script.
2. **Database Validations**: Spatial and database integrity checks using SQL queries on a PostgreSQL database with PostGIS enabled.

## File Validations: Python Script

The file validations are implemented in Python using the script `file_validations.py`. It focuses on basic consistency checks, including:
- Validating data types
- Checking for missing values
- Identifying duplicate rows
- Validating area-related columns
- Table relations

### How to Run File Validations

You can run the file validations via the command line using `typer`.

```bash
python file_validations.py run-processor --input-file <path_to_file> --table-type <table_type>
```

- `input-file`: The path to the file to be validated (e.g., CSV, GPKG, SHP).
- `table-type`: The type of table being validated (e.g., `lpis`, `gsa`, etc.).

Example:

```bash
python file_validations.py run-processor --input-file ./data/lpis_data.csv --table-type lpis
```

For more information on the Python script, refer to [file_validations.py in the repository](https://github.com/ec-jrc/cbm/tree/main/iacs_qa/data_validation).

## Database Validations: SQL Script

The database validations are SQL-based and performed on a **PostgreSQL database** with **PostGIS** enabled. These checks include:
- Geometry validity (well-formed and non-overlapping geometries)
- Missing or empty geometries
- Overlapping and duplicate geometries
- Spatial relationships between LPIS and GSA parcels
- Area consistency between declared and calculated values

### How to Run Database Validations

1. Ensure you have a **PostgreSQL** database with the **PostGIS** extension enabled.
2. Create the required tables using the structure defined in the [specifications](https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf).
3. Run the SQL queries provided in `database_validations.sql` to perform the checks.

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
- **ANASTASAKIS Konstantinos** – Python script (File validations)
- **ISOARDI Paolo** – SQL script (Database validations)

## License

This project is licensed under the [3-Clause BSD](https://opensource.org/licenses/BSD-3-Clause) license

---

Copyright (c) 2024, [European Commission](https://ec.europa.eu/), Joint Research Centre. All rights reserved.
