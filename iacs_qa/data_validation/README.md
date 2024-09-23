# IACS Data Validation Tools

This repository provides tools for performing data consistency checks to help Member States improve the quality of their IACS data prior to submission on the QUAP platform. There are two sets of checks:  

1. **File/data validation performed by the QUAP platform**: Controls performed by the QUAP modules during the data submission process on the files (e.g. CSV, GPKG, SHP) sent by the Member States. The files are provided by the Member States in the delivery of November 1st every year as part of the IACS quality assessment exercise. These checks must be passed to complete the submission process. Running these scripts locally before submission is optional and is intended to simplify and speed up the data upload procedure. The checks are implemented using a Python script.
2. **Additional quality checks**: An additional series of data checks is carried out by the JRC once the submission has been successfully completed and data accepted. The purpose of these checks is to scrutinise the information provided for suspicious data and potential errors/inconsistencies. The results are usually communicated to the Member States as warnings to help improve the quality of the submitted data. These checks do not invalidate the submitted data (Member States may ignore them if they wish). The quality of the data submitted remains responsability of each Member State. These data screening procedures are implemented using SQL spatial queries (reference platform: PostgreSQL/POSTGIS).

## QUAP File/data Validations: Python Script 

The QUAP file/data validations are implemented in Python using the script `first_layer_file_validations.py`. This script performs basic consistency checks to ensure that the data meets the necessary quality standards to be accepted. The validations include:

- **Verifying data types**: Ensures that each column contains the expected data type (e.g., string, integer, boolean).
- **Checking for missing values**: Detects any missing or `null` values in the required columns where a value is required.
- **Identifying duplicate rows**: Identifies duplicate rows based on specific columns that must be unique (e.g., primary keys).
- **Validating area-related columns**: Checks if area-related columns (e.g., total area) are in hectares and have up to four decimal places, ensuring their validity.
- **Validating relationships between tables**: For the GSA/units amount claimed (ua) table, the script checks relational integrity by verifying that unique entries in the ua table exist in the interventions and GSA population tables.

These controls materialise the requirements of [data specifications](https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf) document published on the QUAP platform.

### How to Run File Validations

You can run the file validations via the command line using `argparse`. The command-line interface allows you to specify the input file, and the type of table being processed.

```bash
python first_layer_file_validations.py --input-file <path_to_file> --table-type <table_type>
```

#### Command-line Arguments:
- `--input-file`: The path to the file to be validated.
- `--table-type`: The type of table being validated. This is a required argument.
- `--interventions-file`: (Optional) Path to the interventions file. Required only when validating the `ua` table type.
- `--gsa-population-file`: (Optional) Path to the GSA population file. Required only when validating the `ua` table type.

#### Example Command
Here is an example of a command to execute the script on a LPIS population file:

```bash
python first_layer_file_validations.py --input-file ./data/lpis_data.csv --table-type lpis
```

This is an additional example for validating a `ua` table with the optional interventions and GSA population files:

```bash
python first_layer_file_validations.py --input-file ./data/ua_data.csv --table-type ua --interventions-file ./data/interventions_data.csv --gsa-population-file ./data/gsa_population_data.csv
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
The table with the information on the relationship between 

### Supported File Formats

- **CSV**: Currently, the script only supports CSV files. You must provide a `.csv` file for validation.
-  More file formats such as Parquet, GPKG (GeoPackage) and SHP (Shapefile) will be supported in future updates.

### Outputs

When you run the data validation script, several outputs are generated depending on the validation steps executed. These outputs are logged into files or displayed in the command-line interface. Here's a breakdown:

- **Log File**: Records validation details, including errors and execution time, in `<input_file_name>_log.txt`.
- **Duplicate Log**: Duplicates are logged in `<input_file_name>_duplicates_log.txt`.
- **Null Value Log**: Null values are noted in the main log file.
- **Area Validation Log**: Invalid area values are logged in `<input_file_name>_area_amount_log.txt`.
- **Relationship Validation Log**: If any relationship issues are detected (e.g., missing entries in the `ua` table that do not exist in the interventions or GSA population tables), they are logged in `<input_file_name>_relation_<column>_log.txt`.

Progress updates and errors are also printed in the terminal during execution for real-time feedback.

### Future Developments

There is an ongoing investigation to replace `pandas` with newer Python libraries, such as `Polaris`, or other alternatives that may offer better performance for large datasets. This could improve the efficiency of file validations.

For more information on the Python script, refer to [first_layer_file_validations.py in the repository](https://github.com/ec-jrc/cbm/tree/main/iacs_qa/data_validation).

## Additional Quality Checks: SQL Scripts

In addition to the compulsory validation checks that must be successfully passed to complete the data submission procedure, other data screening scripts are run to detect potential issues. These quality controls do not prevent MS from submitting their data and must be considered as tools to help improving the overall quality of the data submitted. These quality checks are implemented as SQL scripts in a database where submitted (and accepted) data are stored in the same structure as specified in the
In addition to the mandatory validation checks that must be successfully passed to complete the data submission process, other data screening scripts are run to identify potential problems. These quality checks do not prevent Member States from submitting their data and should only be considered as optional tools to help improve the overall quality of the submitted data. These quality checks are implemented as SQL scripts. These must be run in a database where the submitted (and accepted) data are stored in the same structure specified in the [data specifications](https://lpis.jrc.ec.europa.eu/assets/images/dataspecifications/specs_data_submission_nov_2023.pdf). The SQL is developed on a **PostgreSQL database** with **PostGIS** enabled. The scripts will checks:

- if geometries of the LPIS and GSA parcels are well-formed and valid according to OGC standards
- if LPIS and GSA parcels have missing geometries, namely null values of the geometric attribute
- if LPIS and GSA parcels have empty geometries, namely parcels where the geometry is present but it is empty, having a zero value area
- if LPIS and GSA parcels have duplicated geometries. The queries return the number of parcels sharing the same geometry
- if LPIS and GSA parcels have geometries that overlap with surrounding geometries
- if area attributes declared in LPIS population have valid values, i.e. between zero and the declared total area value
- if LPIS parcels have invalid (e.g. negative or zero) values of the total area attribute
- if LPIS parcels have values of the total area attribute equal or bigger than the sum of arable land, permanent crop and permanent grassland areas
- if the LPIS total area value declared is bigger than the geometric area calculated from the given LPIS polygon
- if the GSA claimed area attribute presents invalid (e.g. negative or zero) values
- if the GSA claimed area attribute is bigger than the geometric area calculated from the given GSA polygon
- if there are unit amounts that are not claimed in any GSA parcel
- the 10 largest and smallest parcels for both GSA and LPIS to identify possible ouliers

### How to Run the SQL scripts

We provide a possible implementation using SQL code, but member States can easily adapt them to other languages if they like. We also include some SQL code to help data exploration. To run the scripts provided:
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

You can find the full list of checks in the SQL file.

### References

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
