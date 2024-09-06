import io
import os
import sys
import csv
import json
import zipfile
import pandas as pd
import dask.dataframe as dd


tables_columns_json_path = "./tables.json"


# Load the TABLES_COLUMNS dictionary from the JSON file
def load_tables_columns(json_path):
    with open(json_path, "r") as f:
        return json.load(f)


TABLES_COLUMNS = load_tables_columns(tables_columns_json_path)


class FileReader:
    def __init__(self, file_fullpath, table_type="geometry"):
        self.file_fullpath = file_fullpath
        self.table_type = table_type
        self.valid_extensions = [".zip", ".csv", ".gpkg", ".parquet", ".shp"]

    def validate_file_extension(self):
        """Validate that the file has a supported extension."""
        _, file_extension = os.path.splitext(self.file_fullpath)
        if file_extension.lower() not in self.valid_extensions:
            raise Exception(
                f"Invalid file format (supported files: {', '.join(self.valid_extensions)})"
            )

    def get_first_valid_file_from_zip(self, zip_ref):
        """Get the first valid file from a ZIP archive."""
        valid_files = [
            f
            for f in zip_ref.namelist()
            if any(f.lower().endswith(ext) for ext in self.valid_extensions)
        ]
        if not valid_files:
            raise Exception("No valid file found in ZIP")
        return valid_files[0]

    def read_file(self) -> dd.DataFrame:
        """Read the input file and return a Dask DataFrame."""
        self.validate_file_extension()
        filename, file_extension = os.path.splitext(self.file_fullpath)

        if file_extension.lower() == ".zip":
            with zipfile.ZipFile(self.file_fullpath, "r") as zip_ref:
                first_valid_file = self.get_first_valid_file_from_zip(zip_ref)
                extracted_file_path = os.path.join(
                    os.path.dirname(self.file_fullpath), filename, first_valid_file
                )
                zip_ref.extract(
                    first_valid_file, path=os.path.dirname(extracted_file_path)
                )
                return self.load_data_dask(extracted_file_path)
        else:
            return self.load_data_dask(self.file_fullpath)

    def load_data_dask(self, datafile):
        """Load the data into a Dask DataFrame based on file extension."""
        file_extension = os.path.splitext(datafile)[-1].lower()
        if file_extension == ".csv":
            return self.read_csv_dask(datafile)
        elif file_extension == ".parquet":
            return dd.read_parquet(datafile)
        elif file_extension == ".shp":
            return self.read_shapefile(datafile)
        elif file_extension == ".gpkg":
            return self.read_geopackage(datafile)
        else:
            raise Exception(f"Unsupported file format: {file_extension}")

    def read_csv_dask(self, datafile) -> dd.DataFrame:
        """Read a CSV file into a Dask DataFrame."""
        try:
            with open(datafile, "r") as f:
                sample = f.read(1024)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            if delimiter != ";":
                raise Exception(
                    f"Error: CSV file should use a semicolon (;) as delimiter. Detected: {delimiter}"
                )
            header = [col.lower() for col in sample.splitlines()[0].split(delimiter)]

            if "geometry" in header:
                header = [
                    f"{self.table_type}_geom" if col == "geometry" else col
                    for col in header
                ]

            dtype_dict = self.get_csv_dtype_dict()
            return dd.read_csv(
                datafile,
                blocksize=10e6,
                delimiter=delimiter,
                assume_missing=True,
                dtype=dtype_dict,
                names=header,
                header=0,
            )
        except Exception as e:
            raise Exception(f"Failed to read CSV: {str(e)}")

    def get_csv_dtype_dict(self):
        """Get the dtype dictionary for reading CSV files."""
        pkeys = TABLES_COLUMNS["primary_keys"][self.table_type]
        dtype_dict = {pk: "object" for pk in pkeys}
        if self.table_type == "gsa":
            dtype_dict.update(
                {"gsa_hol_id": "object", "main_crop": "object", "catch_crop": "object"}
            )
        return dtype_dict

    def read_shapefile(self, datafile) -> dd.DataFrame:
        """Read a shapefile into a Dask DataFrame."""
        gdf = gpd.read_file(datafile)
        gdf[f"{self.table_type}_geom"] = gdf["geometry"].apply(
            lambda x: x.wkt if x is not None else None
        )
        return dd.from_pandas(gdf.drop(columns=["geometry"]), chunksize=1000)

    def read_geopackage(self, datafile) -> dd.DataFrame:
        """Read a GeoPackage file into a Dask DataFrame."""
        gdf = gpd.read_file(datafile)
        return dd.from_pandas(gdf, chunksize=1000)


def colors(color="ENDC"):
    """Returns ANSI escape code for the given color name.

    Parameters
    ----------
    color : str, optional
        The name of the color to retrieve. Defaults to 'ENDC'.

    Returns
    -------
    str
        The ANSI escape code for the requested color.
    """
    colors_dict = {
        "HEADER": "\033[95m",
        "OKBLUE": "\033[94m",
        "OKCYAN": "\033[96m",
        "OKGREEN": "\033[92m",
        "WARNING": "\033[93m",
        "FAIL": "\033[91m",
        "ENDC": "\033[0m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
    }
    return colors_dict.get(color.upper(), colors_dict["ENDC"])


def progressbar(total, progress, label="", length=20, color="WARNING"):
    """Displays a progress bar in the terminal.

    Parameters
    ----------
    total : int or float
        The total value indicating completion.
    progress : int or float
        The current progress value.
    label : str, optional
        Additional label to display at the end of the progress bar. Defaults to ''.
    length : int, optional
        The length of the progress bar in characters. Defaults to 20.
    color : str, optional
        The color of the progress bar. Defaults to 'WARNING'.
    """
    try:
        if total == 0:
            raise ValueError("Total value must be greater than 0.")

        percent = int(100 * (progress / total))
        bar_length = int(percent / (100 / length))
        bar = "░" * bar_length + "▭" * (length - bar_length)
        print(f"\r{colors(color)}|{bar}| {percent}% {label}{colors('ENDC')}", end="\r")

        if progress >= total:
            sys.stdout.write("\033[K")  # Clear the line
            print(
                f"\r{colors('OKGREEN')}|{bar}| {percent}% - {label} Process Completed. {colors('ENDC')}"
            )

    except Exception as err:
        print(f"\r{colors('FAIL')}|░░░| 00% Error: {err}{colors('ENDC')}", end="\r")
