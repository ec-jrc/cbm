# Data Validation Tools

This repository provides tools for performing data consistency checks with two methods:

1. **File Validations**: Basic checks on data files (e.g., CSV, GPKG, SHP) using a Python script.
2. **Database Validations**: Spatial and database integrity checks using SQL queries on a PostgreSQL database with PostGIS enabled.

## File Validations: Python Script

The file validations are implemented in Python using the script `first_layer_file_validations.py`. This script performs basic consistency checks to ensure that the data meets the necessary quality standards. The validations include:

- **Validating data types**: Ensures that each column contains the expected data type (e.g., string, integer, boolean).
- **Checking for missing values**: Detects any missing or `null` values in the required columns.
- **Identifying duplicate rows**: Identifies duplicate rows based on the specified columns (e.g., primary keys).
- **Validating area-related columns**: Checks if area-related columns (e.g., total area) are in hectares and have up to four decimal places, ensuring their validity.

Please see table specifications details in the [specifications](https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf) document.

### How to Run File Validations

You can run the file validations via the command line using `argparse`. The command-line interface allows you to specify the input file, and the type of table being processed.

```bash
python first_layer_file_validations.py --input-file <path_to_file> --table-type <table_type>
```

#### Command-line Arguments:
- `--input-file`: The path to the file to be validated (currently supports only CSV format).
- `--table-type`: The type of table being validated. This is a required argument.

#### Example Command

Here’s an example command for running the script on a dataset from an LPIS population file:

```bash
python first_layer_file_validations.py --input-file ./data/lpis_data.csv --table-type lpis
```

### Available Table Types

The `--table-type` argument determines the specific validation rules applied to the data. Below are the available options for table types:

| Table Type   | Description                     |
|--------------|---------------------------------|
| `gsa`        | GSA population                  |
| `lpis`       | LPIS population                 |
| `inter`      | List of interventions           |
| `ua`         | GSA/units amount claimed        |

Each table type has its own set of validation rules based on the structure and requirements of the data. Be sure to select the correct `table-type` for the dataset you are validating.

### Supported File Formats

- **CSV**: Currently, the script only supports CSV files. You must provide a `.csv` file for validation.

  *Note*: More file formats such as Parquet, GPKG (GeoPackage) and SHP (Shapefile) will be supported in future updates.

### Notes:
- Make sure the `input-file` is in the supported format (currently only CSV) and contains the expected columns.
- All validation results will be logged into separate log files, which will be created in the same directory as the input file.

### Future Development

There is an ongoing investigation to replace `pandas` with newer Python libraries, such as `Polaris`, or other alternatives that may offer better performance for large datasets. This could improve the efficiency of file validations.

For more information on the Python script, refer to [first_layer_file_validations.py in the repository](https://github.com/ec-jrc/cbm/tree/main/iacs_qa/data_validation).

## Database Validations: SQL Script

The database validations are SQL-based and performed on a **PostgreSQL database** with **PostGIS** enabled. These checks include:

- if geometries of the LPIS and GSA parcels are well-formed and valid according to OGC standards.
- if LPIS and GSA parcels have missing geometries, namely null values of the geometric attribute.
- if LPIS and GSA parcels have empty geometries, namely parcels where the geometry is present but it is empty, having a zero value area.
- if LPIS and GSA parcels have duplicated geometries. The queries return the number of parcels sharing the same geometry.
- if LPIS and GSA parcels have geometries that overlap with surrounding geometries.
- if area attributes declared in LPIS population have valid values, i.e. between zero and the declared total area value.
- if LPIS parcels have invalid negative values of the total area attribute.
- if LPIS parcels have invalid zero values of the total area attribute.
- if LPIS parcels have values of the total area attribute equal or bigger than the sum of arable land, permanent crop and permanent grassland areas.
- if the LPIS total area value declared is bigger than the geometric area calculated from the given LPIS polygon.
- if the GSA claimed area attribute presents invalid negative or zero values.
- if the GSA claimed area attribute is bigger than the geometric area calculated from the given GSA polygon.
- for Unit Amounts declared but not claimed.
- basic statistics (minimum, maximum, average values) on the number of Unit Amounts declared per Group of Unit Amounts.
- basic statistics (minimum, maximum, average values) on the number of Groups of Unit Amounts declared per Interventions.


### How to Run Database Validations

1. Ensure you have a **PostgreSQL** database with the **PostGIS** extension enabled.
2. Create the required tables using the structure defined in the [specifications](https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf).
3. Run the SQL queries provided in `second_layer_database_validations.sql` to perform the checks.

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
