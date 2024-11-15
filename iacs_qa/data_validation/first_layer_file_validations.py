"""
This script runs consistency data validations on large datasets using Dask DataFrames. It performs various
validations such as datatype checks, null value identification, duplicate detection, area format validation,
and relational integrity checks between different tables. The script is designed for flexibility, allowing
the user to specify input files, table types, and relationship tables.

Modules and Functions:
----------------------
1. setup_logging(log_file: str) -> logging.Logger:
- Configures logging for the application, writing logs to a file and the console with different log levels.

2. DataProcessor:
- Class for handling data validation and processing.
- __init__(self, input_file_path: str, table_type: str), interventions_file: Optional[str], gsa_population_file: Optional[str]:
    Initializes the DataProcessor with the input file, relationship table, and table type.
- validate_boolean_column(self, df: dd.DataFrame, column: str) -> bool:
    Validates if a column contains only boolean values.
- validate_dtypes_columns(self, ddf: dd.DataFrame, columns_types: dict) -> None:
    Validates the data types of columns against expected types.
- check_for_duplicates(self, ddf: dd.DataFrame, columns: List[str]) -> None:
    Checks for duplicate rows in the specified columns.
- check_for_nulls(self, ddf: dd.DataFrame, columns: List[str]) -> None:
    Identifies null values in the specified columns.
- validate_area_format(self, ddf: dd.DataFrame) -> None:
    Validates if the area columns are in hectares with 4 decimal precision.
- process(self, tables_columns: dict) -> None:
    Orchestrates the full data validation process.

3. run_processor(input_file: Optional[str], table_type: Optional[str]) -> None:
- Entry point for running the data processor. It loads column configurations from a JSON file,
    creates a DataProcessor instance, and runs the data validation process.

Command-line Interface:
-----------------------
The script supports command-line arguments for specifying the input file, table type, and an optional
relationship table. It uses `argparse` for handling the arguments.

Usage:
------
    python script.py --input-file /path/to/input.csv --table-type lpis

    --input-file: Path to the input data file to be processed.
    --table-type: The type of the table being processed (gsa, lpis, inter or ua).
"""

import gc
import os
import time
import json
import shutil
import logging
import argparse
import pandas as pd
from typing import List, Optional
import dask.dataframe as dd
from utils import FileReader, progressbar, colors


TMP_DIR = "./tmp/"
os.makedirs(TMP_DIR, exist_ok=True)  # Create a temporary folder if not exists


# Logging configuration
def setup_logging(log_file: str):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(
        logging.WARNING
    )  # Set this to WARNING or higher to avoid printing INFO logs

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class DataProcessor:

    def __init__(
        self,
        input_file_path: str,
        table_type: str,
        interventions_file: Optional[str],
        gsa_population_file: Optional[str],
        config: Optional[dict] = None,
    ):
        self.INPUT_FILE_FULLPATH = input_file_path
        self.TABLE_TYPE = table_type
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
        self.statistics = {}
        self.errors = 0
        self.area_tolerance = 0.20
        self.errors_limit = 2000
        self.interventions_file = interventions_file
        self.gsa_population_file = gsa_population_file
        self.config = (
            config
            if config
            else {
                "validate_columns": {"enabled": True, "critical": True},
                "validate_dtypes": {"enabled": True, "critical": False},
                "check_duplicates": {"enabled": True, "critical": False},
                "check_nulls": {"enabled": True, "critical": False},
                "validate_area_format": {"enabled": True, "critical": False},
                "validate_relation_interventions": {"enabled": True, "critical": False},
                "validate_relation_gsa": {"enabled": True, "critical": False},
            }
        )

        # Log file creation
        log_file = os.path.splitext(self.INPUT_FILE_FULLPATH)[0] + "_log.txt"
        setup_logging(log_file)

    def clean_tmp_folder(self):
        tmpdir = TMP_DIR
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
            self.logger.info(f"Temporary folder cleaned: {tmpdir}")
        else:
            self.logger.info(f"Temporary folder not found: {tmpdir}")

    def validate_boolean_column(self, df: dd.DataFrame, column: str) -> bool:
        unique_vals_str = {
            str(uv).lower() for uv in df[column].unique().compute().tolist()
        }
        boolean_sets = [
            {"0", "1"},
            {"true", "false"},
            {"t", "f"},
            {"0.0", "1.0"},
            {0.0, 1.0},
            {0, 1},
        ]
        return any(unique_vals_str.issubset(b) for b in boolean_sets) or any(
            unique_vals_str == b for b in boolean_sets
        )

    def validate_columns(self, ddf: dd.DataFrame, expected_columns: list) -> tuple:
        """Validate if all expected columns are present in the DataFrame."""
        self.logger.info("Validating column presence...")
        missing_columns = []
        actual_columns = ddf.columns

        for column in expected_columns:
            if column not in actual_columns:
                missing_columns.append(column)

        duration = round((time.time() - self.start_time), 1)  # Calculate duration

        if missing_columns:
            self.errors += 1
            message = f"{colors('FAIL')}Error: The following columns are missing: {', '.join(missing_columns)}{colors('ENDC')}"
            self.logger.info(message)
            return (False, message, duration)
        else:
            message = "All expected columns are present."
            self.logger.info(message)
            return (True, message, duration)

    def file_check(self) -> tuple:
        """Check if the file can be read successfully."""
        self.logger.info("Checking file integrity...")
        try:
            file_reader = FileReader(self.INPUT_FILE_FULLPATH, self.TABLE_TYPE)
            file_reader.read_file()
            duration = round((time.time() - self.start_time), 1)
            message = "File integrity check passed."
            self.logger.info(message)
            return (True, message, duration)
        except Exception as e:
            self.errors += 1
            duration = round((time.time() - self.start_time), 1)
            message = f"File integrity check failed: {str(e)}"
            self.logger.error(message)
            return (False, message, duration)

    def validate_dtypes(self, ddf: dd.DataFrame, columns_types: dict) -> tuple:
        """Validate the data types of columns in the DataFrame."""
        self.logger.info("Validating column data types...")
        invalid_columns = []
        actual_dtypes = (
            ddf.dtypes.compute() if isinstance(ddf.dtypes, dd.Series) else ddf.dtypes
        )

        total_columns = len(columns_types)
        progress = 0

        for column, metadata in columns_types.items():
            expected_dtypes = metadata["type"]

            if column in actual_dtypes:
                if expected_dtypes == ["string"]:
                    pass
                elif expected_dtypes == ["bool"]:
                    if not self.validate_boolean_column(ddf, column):
                        invalid_columns.append(
                            f"{column} (Expected: boolean, Got: {actual_dtypes[column]})"
                        )
                elif actual_dtypes[column] not in expected_dtypes:
                    invalid_columns.append(
                        f"{column} (Expected: {expected_dtypes}, Got: {actual_dtypes[column]})"
                    )
            else:
                invalid_columns.append(f"{column} (Missing)")

            progress += 1
            progressbar(
                total=total_columns, progress=progress, label="Validating datatypes:"
            )

        duration = round((time.time() - self.start_time), 1)

        if invalid_columns:
            self.errors += 1
            message = f"{colors('FAIL')}Error: The following columns have invalid data types: {', '.join(invalid_columns)}{colors('ENDC')}"
            self.logger.info(message)
            return (False, message, duration)
        else:
            message = f"Data types are correct. Finished in {duration} sec."
            self.logger.info(message)
            return (True, message, duration)

    def check_for_duplicates(self, ddf: dd.DataFrame, columns: List[str]) -> tuple:
        """Check for duplicate rows based on the specified columns."""
        self.logger.info("Validating duplicates...")
        ddf.columns = list(map(str.lower, ddf.columns))
        required_columns = all(c in ddf.columns for c in columns)

        progress = 0
        total_progress_steps = 1

        if required_columns:
            grouped = ddf.groupby(columns).size().reset_index().compute()
            grouped.columns = list(columns) + ["duplicate_count"]
            duplicates = grouped[grouped["duplicate_count"] > 1]

            progress += 1
            progressbar(
                total=total_progress_steps,
                progress=progress,
                label="Validating duplicates:",
            )

            duration = round((time.time() - self.start_time), 1)

            if not duplicates.empty:
                self.errors += 1
                num_duplicates = len(duplicates)
                message = f"{colors('FAIL')}Error: {num_duplicates} Duplicates found based on: {', '.join(map(str, columns))}{colors('ENDC')}"
                log_file_path = f"{os.path.splitext(self.INPUT_FILE_FULLPATH)[0]}_duplicates_log.txt"
                with open(log_file_path, "w") as log_file:
                    log_file.write(message)
                    duplicates.to_csv(log_file, sep=";", index=False)

                self.logger.info(message)
                return (False, message, duration)
            else:
                message = f"No duplicates found. Finished in {duration} sec."
                self.logger.info(message)
                return (True, message, duration)
        else:
            missing_columns = [c for c in columns if c not in ddf.columns]
            message = f"Error: Missing required columns: {', '.join(missing_columns)}"
            self.logger.error(message)
            return (False, message, 0)

    def check_for_nulls(self, ddf: dd.DataFrame, columns: List[str]) -> tuple:
        """Check for null values in the specified columns."""
        self.logger.info("Validating nulls...")
        ddf.columns = list(map(str.lower, ddf.columns))
        exclude = ["gsa_col_id", "catch_crop"]
        columns_to_check = [col for col in columns if col not in exclude]

        progress = 0
        null_columns = {}
        custom_nulls = ["NA", "Null", "NULL", "Inf", "-Inf", ""]

        for column in columns_to_check:
            if column in ddf.columns:
                null_count = ddf[column].isnull().sum().compute()
                custom_null_count = (
                    ddf[ddf[column].isin(custom_nulls)].shape[0].compute()
                )
                total_null_count = null_count + custom_null_count

                if total_null_count > 0:
                    null_columns[column] = total_null_count

                progress += 1
                progressbar(
                    total=len(columns_to_check),
                    progress=progress,
                    label="Validating nulls:",
                )

        duration = round((time.time() - self.start_time), 1)

        if null_columns:
            self.errors += 1
            message = f"Error: Null values in: {', '.join([f'{col} ({count})' for col, count in null_columns.items()])}"
            self.logger.info(message)
            return (False, message, duration)
        else:
            message = f"No nulls found. Finished in {duration} sec."
            self.logger.info(message)
            return (True, message, duration)

    def validate_area_format(self, ddf: dd.DataFrame) -> tuple:
        """Validate if the area columns are in hectares with 4 decimal precision."""
        area_columns = [
            "tot_area",
            "al_area",
            "pc_area",
            "pg_area",
            "na_area",
            "af_area",
            "n2000_area",
            "pw_area",
            "lf_area",
            "anc_area",
        ]
        self.logger.info("Validating area format...")
        ddf.columns = list(map(str.lower, ddf.columns))  # Ensure columns are lowercase
        validation_errors = []

        progress = 0
        for column in area_columns:
            if column in ddf.columns:
                invalid_area = (
                    ddf[column]
                    .map_partitions(
                        lambda s: ~s.apply(
                            lambda x: isinstance(x, (float, int)) and round(x, 4) == x
                        ),
                        meta=(None, "bool"),
                    )
                    .compute()
                    .any()
                )

                if invalid_area:
                    validation_errors.append(
                        f"{column} should be in hectares and with 4 decimal places."
                    )

            progress += 1
            progressbar(
                total=len(area_columns),
                progress=progress,
                label="Validating area format:",
            )

        duration = round((time.time() - self.start_time), 1)

        if validation_errors:
            self.errors += 1
            message = "Error: " + "; ".join(validation_errors)
            log_file_path = (
                f"{os.path.splitext(self.INPUT_FILE_FULLPATH)[0]}_area_format_log.txt"
            )
            with open(log_file_path, "w") as log_file:
                log_file.write(message)
                for err in validation_errors:
                    log_file.write(f"\n{err}")

            self.logger.info(message)
            return (False, message, duration)
        else:
            message = f"Area format is correct. Finished in {duration} sec."
            self.logger.info(message)
            return (True, message, duration)

    def validate_relation(
        self,
        df1: dd.DataFrame,
        df2: dd.DataFrame,
        column1: str,
        column2: str = None,
        tname: str = "second",
    ) -> tuple:
        """Validate that entries in `column1` of `df1` exist in `column2` of `df2`."""
        self.logger.info(
            f"Validating if entries exist in both {self.TABLE_TYPE} and {tname} tables..."
        )

        df1.columns = list(map(str.lower, df1.columns))
        df2.columns = list(map(str.lower, df2.columns))

        # Set column2 to column1 if not provided
        if not column2:
            column2 = column1

        progress = 0
        total_steps = 1  # Set total steps to 1 since it's a single operation

        # Ensure both columns exist in their respective DataFrames
        if column1 in df1.columns and column2 in df2.columns:

            # Normalize df1[column1] to strings
            if pd.api.types.is_numeric_dtype(df1[column1].dtype):
                df1[column1] = df1[column1].apply(
                    lambda x: (
                        str(int(x)) if pd.notnull(x) and x == x // 1 else str(x)
                    ),
                    meta=("x", "object"),
                )
            else:
                df1[column1] = df1[column1].astype(str)

            # Normalize df2[column2] to strings
            if pd.api.types.is_numeric_dtype(df2[column2].dtype):
                df2[column2] = df2[column2].apply(
                    lambda x: (
                        str(int(x)) if pd.notnull(x) and x == x // 1 else str(x)
                    ),
                    meta=("x", "object"),
                )
            else:
                df2[column2] = df2[column2].astype(str)

            # Get unique entries from both DataFrames
            unique_df1 = df1[column1].unique().compute().tolist()
            unique_df2 = df2[column2].unique().compute().tolist()

            # Find missing entries
            set_df1 = set(unique_df1)
            set_df2 = set(unique_df2)
            missing_entries = set_df1 - set_df2
            num_missing_entries = len(missing_entries)

            progress += 1
            progressbar(
                total=total_steps,
                progress=progress,
                label=f"Validating relation for {column1}:",
            )

            duration = round((time.time() - self.start_time), 1)

            # Handle missing entries
            if num_missing_entries > 0:
                self.errors += 1
                message = f"Error: {num_missing_entries} unique entrie(s) of '{column1}' from '{self.TABLE_TYPE}' table do not exist in '{tname}' table."

                log_file_path = f"{os.path.splitext(self.INPUT_FILE_FULLPATH)[0]}_relation_{column1}_log.txt"
                with open(log_file_path, "w") as log_file:
                    log_file.write(message + "\n")
                    for entry in missing_entries:
                        log_file.write(f"{entry}\n")

                self.logger.info(message)
                return (False, message, duration)
            else:
                message = f"All unique entries in '{column1}' from '{self.TABLE_TYPE}' table exist in '{tname}' table. Finished in {duration} sec."
                self.logger.info(message)
                return (True, message, duration)
        else:
            self.errors += 1
            message = f"Error: Column '{column1}' or '{column2}' not found in their respective tables."
            self.logger.error(message)
            return (False, message, 0)

    def process(self, tables_columns: dict):
        """Orchestrates the full data validation process, yielding results at each step."""
        try:
            self.logger.info("Starting data validation...")
            print("Starting validation...")
            self.logger.info(f"INPUT FILE: {self.INPUT_FILE_FULLPATH}")

            try:
                # File check is always true, so no need for conditional logic here
                file_reader = FileReader(self.INPUT_FILE_FULLPATH, self.TABLE_TYPE)
                ddf = file_reader.read_file()  # Read the file to produce the ddf
                yield (True, "File check passed", 0)
            except Exception as e:
                error_message = f"Error during file reading: {str(e)}"
                self.logger.error(error_message)
                yield (False, error_message, 0)
                return

            # Define the steps with critical and enabled properties from config
            steps = [
                (
                    "validate_columns",
                    self.validate_columns,
                    [ddf, tables_columns[self.TABLE_TYPE]],
                ),
                (
                    "validate_dtypes",
                    self.validate_dtypes,
                    [ddf, tables_columns[self.TABLE_TYPE]],
                ),
                (
                    "check_duplicates",
                    self.check_for_duplicates,
                    [ddf, tables_columns["primary_keys"][self.TABLE_TYPE]],
                ),
                (
                    "check_nulls",
                    self.check_for_nulls,
                    [ddf, list(tables_columns[self.TABLE_TYPE].keys())],
                ),
            ]

            # LPIS Specific Validations
            if self.TABLE_TYPE == "lpis":
                steps.append(("validate_area_format", self.validate_area_format, [ddf]))

            # GSA_UA_CLAIMED Specific Validations
            if self.TABLE_TYPE == "ua_claimed":
                if (
                    self.config.get("validate_relation_interventions", {}).get(
                        "enabled", True
                    )
                    and self.interventions_file
                ):
                    file_reader_inter = FileReader(
                        self.interventions_file, "interventions"
                    )
                    ddf_inter = file_reader_inter.read_file()
                    steps.append(
                        (
                            "validate_relation_interventions",
                            self.validate_relation,
                            [ddf, ddf_inter, "ua", None, "interventions"],
                        )
                    )

                if (
                    self.config.get("validate_relation_gsa", {}).get("enabled", True)
                    and self.gsa_population_file
                ):
                    file_reader_gsa = FileReader(self.gsa_population_file, "gsa")
                    ddf_gsa = file_reader_gsa.read_file()
                    steps.append(
                        (
                            "validate_relation_gsa",
                            self.validate_relation,
                            [ddf, ddf_gsa, "gsa_par_id", None, "gsa"],
                        )
                    )

            # Execute each step and yield the results
            for step_name, step_function, args in steps:
                step_config = self.config.get(
                    step_name, {"enabled": True, "critical": False}
                )
                if step_config.get("enabled", True):
                    try:
                        result = step_function(*args)
                        success, message, duration = result
                        message = f"[{step_name.upper()}]: {'Success' if success else 'Failure'} - {message} (Duration: {duration}s)"
                        yield (success, message, duration)

                        if not success and step_config.get("critical", False):
                            # Stop the process if the step fails and is marked as critical
                            break
                    except Exception as e:
                        error_message = f"[{step_name.upper()}]: Error - {str(e)}"
                        self.logger.error(error_message)
                        yield (False, error_message, 0)
                        return

            # Final message after all steps
            if self.errors > 0:
                final_err_msg = f"{colors('FAIL')}There were {self.errors} errors in the validation, please check logs for details.{colors('ENDC')}"
                self.logger.info(final_err_msg)
                yield (False, final_err_msg, 0)
            else:
                total_time = round((time.time() - self.start_time), 1)
                final_msg = f"Finished validation successfully in {total_time} sec."
                self.logger.info(final_msg)
                yield (True, final_msg, total_time)

        except Exception as e:
            error_msg = f"Fatal error occurred: {str(e)}"
            self.logger.error(error_msg)
            yield (False, error_msg, 0)
        finally:
            self.clean_tmp_folder()
            self.logger.info("Cleaned up temporary files.")


def run_processor(
    input_file: Optional[str] = None,
    table_type: Optional[str] = None,
    interventions_file: Optional[str] = None,
    gsa_population_file: Optional[str] = None,
):
    try:
        if input_file is None:
            input_file = input("Please provide the input file path: ")

        if table_type is None:
            table_type = input("Please provide the table type: ")

        if "inter" in table_type:
            table_type = "interventions"
        elif "ua" in table_type:
            table_type = "ua_claimed"
            # Ask for interventions and GSA population files
            if interventions_file is None:
                interventions_file = input(
                    "Please provide the interventions file path: "
                )
            if gsa_population_file is None:
                gsa_population_file = input(
                    "Please provide the GSA population file path: "
                )

        tables_columns_path = "./tables.json"
        with open(tables_columns_path, "r") as f:
            tables_columns = json.load(f)

        data_processor = DataProcessor(
            input_file, table_type, interventions_file, gsa_population_file
        )

        # Iterate over the generator returned by process to print results to the terminal
        for success, message, duration in data_processor.process(tables_columns):
            print(message)

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the data processor")
    parser.add_argument("--input-file", type=str, help="Path to the input file")
    parser.add_argument(
        "--table-type",
        type=str,
        required=True,
        help="The type of table being processed",
    )
    parser.add_argument(
        "--interventions-file",
        type=str,
        help="Path to the interventions file (required for 'ua' table type)",
    )
    parser.add_argument(
        "--gsa-population-file",
        type=str,
        help="Path to the GSA population file (required for 'ua' table type)",
    )

    args = parser.parse_args()

    run_processor(
        input_file=args.input_file,
        table_type=args.table_type,
        interventions_file=args.interventions_file,
        gsa_population_file=args.gsa_population_file,
    )
