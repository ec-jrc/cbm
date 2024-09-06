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
        self, input_file_path: str, relationship_table: Optional[str], table_type: str
    ):
        self.INPUT_FILE_FULLPATH = input_file_path
        self.relationship_table = relationship_table
        self.TABLE_TYPE = table_type
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
        self.statistics = {}
        self.errors = 0
        self.area_tolerance = 0.20
        self.errors_limit = 2000

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

    def validate_dtypes_columns(self, ddf: dd.DataFrame, columns_types: dict) -> None:
        self.logger.info("Validating datatypes...")
        invalid_columns = []
        actual_dtypes = (
            ddf.dtypes.compute() if isinstance(ddf.dtypes, dd.Series) else ddf.dtypes
        )

        total_columns = len(columns_types)
        progress = 0

        for column, metadata in columns_types.items():
            expected_dtypes = metadata["type"]

            if column not in actual_dtypes:
                if column in ["lpis_geom", "gsa_geom"] and "geometry" in actual_dtypes:
                    pass
                else:
                    invalid_columns.append(f"{column} (Missing)")
            elif expected_dtypes == ["string"]:
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

            progress += 1
            progressbar(
                total=total_columns, progress=progress, label="Validating datatypes:"
            )

        if invalid_columns:
            self.errors += 1
            message = f"{colors('FAIL')}Error: The following columns are missing or have invalid data types: {', '.join(invalid_columns)}{colors('ENDC')}"
            print(f"\n{message}")
            self.logger.info(message)
            raise Exception(f"{colors('FAIL')}!Validation FAILED! {self.errors} error(s) found.{colors('ENDC')}")
        else:
            message = f"Datatypes are correct. Finished in {round((time.time() - self.start_time), 1)} sec."
            print(f"{message}")
            self.logger.info(message)

    def check_for_duplicates(self, ddf: dd.DataFrame, columns: List[str]) -> None:
        self.logger.info("Validating duplicates...")
        ddf.columns = list(map(str.lower, ddf.columns))
        required_columns = all(c in ddf.columns for c in columns)

        progress = 0
        total_progress_steps = 1  # Since the progress bar was set for a length of 1, we will just track it manually

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

            if not duplicates.empty:
                self.errors += 1
                num_duplicates = len(duplicates)
                message = f"{colors('FAIL')}Error: {num_duplicates} Duplicates found based on: {', '.join(map(str, columns))}{colors('ENDC')}"

                log_file_path = f"{os.path.splitext(self.INPUT_FILE_FULLPATH)[0]}_duplicates_log.txt"
                with open(log_file_path, "w") as log_file:
                    log_file.write(message)
                    duplicates.to_csv(log_file, sep=";", index=False)

                print(f"{message}")
            else:
                message = f"No duplicates found. Finished in {round((time.time() - self.start_time), 1)} sec."
                print(f"{message}")
            self.logger.info(message)
        else:
            missing_columns = [c for c in columns if c not in ddf.columns]
            message = f"Error: Missing required columns: {', '.join(missing_columns)}"
            print(f"{message}")
            self.logger.error(message)

    def check_for_nulls(self, ddf: dd.DataFrame, columns: List[str]) -> None:
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

        # Check for nulls and log results
        if null_columns:
            self.errors += 1
            message = f"Error: Null values in: {', '.join([f'{col} ({count})' for col, count in null_columns.items()])}"
            print(f"\n{message}")
        else:
            message = f"No nulls found. Finished in {round((time.time() - self.start_time), 1)} sec."
            print(f"{message}")

        self.logger.info(message)

    def validate_area_format(self, ddf: dd.DataFrame) -> None:
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
                # Check if the values in the column are in hectares with 4 decimal places
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

            print(f"\n{message}")
        else:
            message = f"Area format is correct. Finished in {round((time.time() - self.start_time), 1)} sec."
            print(f"{message}")

        self.logger.info(message)

    def validate_area_amount(self, ddf: dd.DataFrame, pkey: str, column: str) -> None:
        self.logger.info("Validating area amount...")
        ddf.columns = list(map(str.lower, ddf.columns))
        ddf = ddf[
            [pkey, column]
        ]  # Filter the DataFrame for primary keys and the area column

        progress = 0
        progressbar(total=1, progress=progress, label="Validating area amount:")

        # Query for parcels with zero or negative area
        invalid_area_df = ddf.query(f"{column} <= 0").compute()
        invalid_area_count = len(invalid_area_df)

        progress += 1
        progressbar(total=1, progress=progress, label="Validating area amount:")

        if invalid_area_count > 0:
            self.errors += 1
            message = (
                f"Error: Found {invalid_area_count} parcels with zero/negative area"
            )

            print(f"\n{message}")

            log_file_path = (
                f"{os.path.splitext(self.INPUT_FILE_FULLPATH)[0]}_area_amount_log.txt"
            )
            with open(log_file_path, "w") as log_file:
                log_file.write(message)
                invalid_area_df.to_csv(log_file, sep=";", index=False)

            self.logger.info(message)
        else:
            message = f"No parcels with zero/negative area. Finished in {round((time.time() - self.start_time), 1)} sec."
            print(f"{message}")
            self.logger.info(message)

    def validate_relation(
        self,
        df1: dd.DataFrame,
        df2: dd.DataFrame,
        column1: str,
        column2: str = None,
        tname: str = "second",
    ) -> None:
        self.logger.info(
            f"Validating if entries exist in both {self.TABLE_TYPE} and {tname} tables..."
        )
        message = None

        try:
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

                # Handle missing entries
                if num_missing_entries > 0:
                    self.errors += 1
                    message = f"Error: {num_missing_entries} unique entrie(s) of '{column1}' from '{self.TABLE_TYPE}' table do not exist in '{tname}' table."
                    print(f"\n{message}")

                    log_file_path = f"{os.path.splitext(self.INPUT_FILE_FULLPATH)[0]}_relation_{column1}_log.txt"
                    with open(log_file_path, "w") as log_file:
                        log_file.write(message + "\n")
                        for entry in missing_entries:
                            log_file.write(f"{entry}\n")

                    self.logger.info(message)
                else:
                    message = f"All unique entries in '{column1}' from '{self.TABLE_TYPE}' table exist in '{tname}' table. Finished in {round((time.time() - self.start_time), 1)} sec."
                    print(f"\n{message}")
                    self.logger.info(message)

            else:
                self.errors += 1
                message = f"Error: Column '{column1}' or '{column2}' not found in their respective tables."
                print(f"\n{message}")
                self.logger.error(message)

        except Exception as e:
            message = f"Fatal Error: Failed to validate entries in both tables. {e}"
            self.logger.error(message)
            print(f"\n{message}")
            raise Exception(f"Error: Fatal error during relation validation: {e}")

        finally:
            del (
                unique_df1,
                unique_df2,
                set_df1,
                set_df2,
                missing_entries,
                num_missing_entries,
            )
            gc.collect()

    def process(self, tables_columns: dict) -> None:
        try:
            self.logger.info("Starting data validation...")
            print("Starting validation...")
            self.logger.info(f"INPUT FILE: {self.INPUT_FILE_FULLPATH}")
            filename, _ = os.path.splitext(self.INPUT_FILE_FULLPATH)

            file_reader = FileReader(self.INPUT_FILE_FULLPATH, self.TABLE_TYPE)
            ddf = file_reader.read_file()

            self.validate_dtypes_columns(ddf, tables_columns[self.TABLE_TYPE])
            self.check_for_duplicates(
                ddf, tables_columns["primary_keys"][self.TABLE_TYPE]
            )
            self.check_for_nulls(ddf, list(tables_columns[self.TABLE_TYPE].keys()))

            if self.TABLE_TYPE == "lpis":
                self.validate_area_format(ddf)
                self.validate_area_amount(
                    ddf, tables_columns["primary_keys"][self.TABLE_TYPE][0], "tot_area"
                )

            if self.errors > 0:
                final_err_msg = f"{colors('FAIL')}There were {self.errors} errors in the validation, please check logs for ditails.{colors('ENDC')}"
                print(final_err_msg)
                self.logger.info(final_err_msg)
                raise Exception(final_err_msg)

            total_time = f"{round((time.time() - self.start_time), 1)} sec."
            final_msg = f"Finished validation successfully in {total_time}."
            self.logger.info(final_msg)
            print(final_msg)
        except Exception as e:
            self.logger.error(e)
        finally:
            self.clean_tmp_folder()
            self.logger.info("Cleaned up temporary files.")


def run_processor(
    input_file: Optional[str] = None,
    table_type: Optional[str] = None,
    relationship_table: Optional[str] = None,
):
    try:
        if input_file is None:
            input_file = input("Please provide the input file path: ")

        if table_type is None:
            table_type = input("Please provide the table type: ")

        if table_type in ["gsa_lpis", "gsa_ua_claimed"]:
            if not relationship_table:
                relationship_table = input(
                    "Please provide the relationship table path: "
                )

        tables_columns_path = "./tables.json"
        with open(tables_columns_path, "r") as f:
            tables_columns = json.load(f)

        data_processor = DataProcessor(input_file, relationship_table, table_type)
        data_processor.process(tables_columns)

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
        "--relationship-table",
        type=str,
        help="Path to the relationship table (optional)",
    )

    args = parser.parse_args()

    run_processor(
        input_file=args.input_file,
        table_type=args.table_type,
        relationship_table=args.relationship_table,
    )
