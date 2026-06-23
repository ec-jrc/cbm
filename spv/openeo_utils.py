# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 09:41:40 2026

@authors: Gilbert Voican, Mateusz Dobrychlop and Daniele Borio
"""
#%% Import Libraries
import geopandas as gpd
import tempfile
import zipfile
from shapely.geometry import box, shape
import os
import shutil
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import time
import datetime as dt
from zoneinfo import ZoneInfo

import leafmap
from ipyleaflet import DrawControl, GeoJSON, Marker, DivIcon, LayerGroup, Popup, WidgetControl

import xarray as xr
import base64

import io
import hashlib
from IPython.display import display, clear_output, HTML

from openeo.extra.spectral_indices.spectral_indices import append_indices

import ipywidgets as widgets
from ipywidgets import HTML 

import uuid
from datetime import datetime


def load_vector_dataset(file_path):
    """
    Load a vector dataset from GeoJSON, GPKG, KML, Shapefile, or ZIP shapefile.
    Returns a GeoDataFrame.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".geojson", ".json", ".gpkg", ".shp"]:
        gdf = gpd.read_file(file_path)

    elif ext == ".kml":
        gdf = gpd.read_file(file_path, driver="KML")

    elif ext == ".zip":
        tmpdir = tempfile.mkdtemp(prefix="vector_upload_")
        with zipfile.ZipFile(file_path, "r") as zf:
            zf.extractall(tmpdir)

        shp_files = []
        for root, _, files in os.walk(tmpdir):
            for f in files:
                if f.lower().endswith(".shp"):
                    shp_files.append(os.path.join(root, f))

        if not shp_files:
            raise ValueError("ZIP file does not contain any .shp file.")

        if len(shp_files) > 1:
            raise ValueError(
                f"ZIP file contains multiple shapefiles: {shp_files}. "
                "Please upload a ZIP with only one shapefile."
            )

        gdf = gpd.read_file(shp_files[0])

    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if gdf.empty:
        raise ValueError("The uploaded dataset is empty.")

    if gdf.crs is None:
        raise ValueError("The uploaded dataset has no CRS defined.")

    return gdf


def _safe_stem(path_or_name: str) -> str:
    return os.path.splitext(os.path.basename(path_or_name))[0]


def _build_dataset_hash(content_bytes: bytes) -> str:
    return hashlib.md5(content_bytes).hexdigest()[:10]


def _build_dataset_tag(start_date: str, end_date: str, upload_hash: str | None = None) -> str:
    base = f"{start_date}_{end_date}"
    return f"{base}_{upload_hash}" if upload_hash else base


#%% Custom libraries
import netcdf_utils as nu
import csv_graphs_utils as cgu
import ncdf_graph_utils as ngu


#%% support functions
def split_extent(gdf : gpd.GeoDataFrame, max_size : int = 50000) -> list :
    """
    Split the original data frame in a list gdfs with with a specified maximum
    extent

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        DESCRIPTION.
    max_size : int, optional
        DESCRIPTION. The default is 10000.

    Returns
    -------
    list 
        List of gdfs 

    """
    # Get the total bounds of the GeoDataFrame (minx, miny, maxx, maxy)
    minx, miny, maxx, maxy = gdf.total_bounds

    # Calculate the width and height
    width = maxx - minx
    height = maxy - miny

    # Determine the number of splits required
    nx = int(np.ceil(width / max_size))  # Number of columns
    ny = int(np.ceil(height / max_size))  # Number of rows

    # Calculate the new subset sizes
    step_x = width / nx
    step_y = height / ny

    subsets = []
    for i in range(nx):
        for j in range(ny):
            # Define the new extent for each subset
            sub_minx = minx + i * step_x
            sub_maxx = minx + (i + 1) * step_x
            sub_miny = miny + j * step_y
            sub_maxy = miny + (j + 1) * step_y

            # Create a bounding box for the subset
            subset_bbox = gpd.GeoDataFrame(geometry=[box(sub_minx, sub_miny, sub_maxx, sub_maxy)], crs=gdf.crs)
            #print(subset_bbox)

            # Select features within subset
            #subset = gpd.overlay(gdf, subset_bbox, how='intersection')
            subset = gdf[gdf.geometry.centroid.within(subset_bbox.geometry[0])]

            # Only store non-empty subsets
            if not subset.empty:
                subsets.append(subset)

    return subsets

def get_spatial_extent(gdf : gpd.GeoDataFrame) -> dict : 
    """
    Generate the spatial extent of a gdf in the format required by openEO
    
    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Geopandas dataframe (gdf) with the geometries of the parcels to process

    Returns
    -------
    dict 
        the spatial extent of a gdf in the format required by openEO

    """
    # Get the total bounds of the geodataframe
    min_x, min_y, max_x, max_y = gdf.total_bounds
    
    # Create and return the spatial extent dictionary
    spatial_extent = {
        "west": min_x, 
        "south": min_y, 
        "east": max_x, 
        "north": max_y,
        "crs": gdf.crs.to_string()
    }
    
    return spatial_extent

def features_fc_to_gdf(features_fc, crs="EPSG:4326"):
    """
    Convert a GeoJSON FeatureCollection (as used by ipyleaflet) 
    into a GeoDataFrame while preserving properties (e.g. aoi_id).
    """

    records = []

    for f in features_fc["features"]:

        geom = shape(f["geometry"])
        props = f.get("properties", {}).copy()

        props["geometry"] = geom

        records.append(props)

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs=crs)

    return gdf

def normalize_parcel_id(value):
    """
    Convert parcel IDs to a stable string representation.

    Examples:
        123      -> "123"
        123.0    -> "123"
        "123"    -> "123"
        "123.0"  -> "123"
        "ABC01"  -> "ABC01"
        None     -> None
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, (int, np.integer)):
        return str(int(value))

    if isinstance(value, (float, np.floating)):
        if float(value).is_integer():
            return str(int(value))
        return str(value)

    s = str(value).strip()

    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
    except Exception:
        pass

    return s


def add_normalized_id_column(gdf, id_column, norm_column="_parcel_id_norm"):
    """
    Return a copy of the GeoDataFrame with a normalized parcel-id column.
    Keeps the original ID column unchanged.
    """
    out = gdf.copy()
    out[norm_column] = out[id_column].apply(normalize_parcel_id)
    return out

def make_gdf_json_safe(gdf):
    gdf = gdf.copy()

    for col in gdf.columns:
        if col == gdf.geometry.name:
            continue

        series = gdf[col]

        if pd.api.types.is_datetime64_any_dtype(series):
            gdf[col] = series.astype(str)
        elif series.dtype == "object":
            def convert_value(x):
                if x is None:
                    return None
                if hasattr(x, "isoformat"):
                    try:
                        return x.isoformat()
                    except Exception:
                        return str(x)
                return x
            gdf[col] = series.apply(convert_value)

    return gdf

def download_netcdf(polygons_gdf : gpd.GeoDataFrame, output_folder : str, id_column : str, \
                    start_date : str, end_date : str, connection ) :
    """
    Function that downloads the netcdf files through the openEO API
    """
    # Retry settings
    max_retries = 3
    wait_seconds = 60

    # Work on a copy and normalize the parcel IDs once
    polygons_gdf = add_normalized_id_column(polygons_gdf, id_column)

    # Reproject to EPSG:3035 in order to apply the buffer in meters
    polygons_gdf = polygons_gdf.to_crs("EPSG:3035")

    # Buffer by 50 meters
    buffer_value = 50
    gdf_buffered = polygons_gdf.copy()
    gdf_buffered["geometry"] = gdf_buffered.geometry.buffer(buffer_value)

    # Convert each buffered geometry to its bounding box
    gdf_extent = gdf_buffered.copy()
    gdf_extent["geometry"] = gdf_buffered.geometry.apply(lambda geom: box(*geom.bounds))

    # Use normalized IDs for file existence checks
    parcel_ids = polygons_gdf["_parcel_id_norm"].tolist()

    expected_files = [
        os.path.join(
            output_folder,
            f"S2_extract_{start_date}_{end_date}_parcelid_{pid}.nc"
        )
        for pid in parcel_ids
    ]

    missing_files = [f for f in expected_files if not os.path.exists(f)]

    if len(missing_files) == 0:
        print("✅ All NetCDF files already exist. Skipping job creation.")
        return

    # information for file naming
    filename_prefix = f"S2_extract_{start_date}_{end_date}_parcelid"

    subsets = split_extent(gdf_extent)
    total_subsets = len(subsets)
    print(f"Processing {total_subsets} subset(s)...")

    for subset_idx, subset in enumerate(subsets, start=1):

        print(f"\n▶ Processing subset {subset_idx}/{total_subsets} ({len(subset)} polygon(s))")

        # creating datacube - S2 bands
        subset = subset.to_crs(epsg=4326)
        spatial_extent = get_spatial_extent(subset)

        # list of bands to be extracted
        bands = ["B02", "B03", "B04", "B08", "B11", "SCL"]

        s2_bands = connection.load_collection(
            "SENTINEL2_L2A",
            temporal_extent=[start_date, end_date],
            spatial_extent=spatial_extent,
            bands=bands,
            max_cloud_cover=50
        )

        # cloud masking
        scl = s2_bands.band("SCL")
        cloud_mask = (
            (scl == 0) | (scl == 1) | (scl == 3) |
            (scl == 8) | (scl == 9) | (scl == 11)
        )

        cloud_mask = cloud_mask.resample_cube_spatial(s2_bands)
        s2_bands_masked = s2_bands.mask(cloud_mask)

        # loading the dataset to json - for the spatial filter
        subset = subset.copy()
        for col in subset.columns:
            if pd.api.types.is_datetime64_any_dtype(subset[col]):
                subset[col] = subset[col].astype(str)
        
        features = json.loads(subset.to_json())

        # spatial filter - using only the pixels intersecting the polygons
        s2_bands_masked = s2_bands_masked.filter_spatial(features)

        # adding NDVI index
        indices = append_indices(
            s2_bands_masked,
            indices=["NDVI"],
            platform="SENTINEL2"
        )

        # IMPORTANT:
        # Keep feature_id_property=id_column unchanged so openEO still uses the real source column.
        job = indices.create_job(
            title="S2 bands and NDVI",
            description="Sentinel-2 L2A bands and NDVI",
            out_format="netCDF",
            filename_prefix=filename_prefix,
            feature_id_property="_parcel_id_norm",
            sample_by_feature=True,
        )

        from rich.console import Console
        console = Console(force_jupyter=True)

        for attempt in range(1, max_retries + 1):
            last_message = {"value": None}

            try:
                print(f"   ↳ Attempt {attempt}/{max_retries}")

                with console.status(
                    f"Subset {subset_idx}/{total_subsets}: submitting job...",
                    spinner="dots"
                ) as status:

                    def custom_print(raw_message):
                        try:
                            elapsed_time = raw_message.split()[0]
                            job_id = raw_message.split()[2].replace(":", "")
                        except Exception:
                            elapsed_time = ""
                            job_id = "unknown"

                        if "start" in raw_message:
                            message = (
                                f"🚀 Subset {subset_idx}/{total_subsets}: "
                                f"job submitted and starting. ID: {job_id}."
                            )
                        elif "created" in raw_message:
                            message = (
                                f"🚀 Subset {subset_idx}/{total_subsets}: "
                                f"job created. ID: {job_id}."
                            )
                        elif "queued" in raw_message:
                            message = (
                                f"⏳ Subset {subset_idx}/{total_subsets} "
                                f"[{elapsed_time}] Job (ID: {job_id}) is waiting in the queue."
                            )
                        elif "running" in raw_message:
                            message = (
                                f"⚙️ Subset {subset_idx}/{total_subsets} "
                                f"[{elapsed_time}] Job (ID: {job_id}) is now running."
                            )
                        elif "finished" in raw_message:
                            message = (
                                f"✅ Subset {subset_idx}/{total_subsets} "
                                f"[{elapsed_time}] Job (ID: {job_id}) has successfully finished."
                            )
                        else:
                            message = f"Subset {subset_idx}/{total_subsets}: {raw_message}"

                        last_message["value"] = message
                        status.update(message)

                    job.start_and_wait(print=custom_print)

                if last_message["value"] is not None:
                    print(last_message["value"])

                job_status = job.status()
                if job_status == "finished":
                    job.get_results().download_files(output_folder)
                    remaining = total_subsets - subset_idx
                    print(f"✅ Finished subset {subset_idx}/{total_subsets}. Remaining: {remaining}")
                    break
                else:
                    raise RuntimeError(f"Job ended with status '{job_status}'")

            except Exception as e:
                print(f"❌ Subset {subset_idx}/{total_subsets} failed (attempt {attempt}/{max_retries}): {e}")

                if attempt < max_retries:
                    print(f"   ↳ Retrying in {wait_seconds} seconds...")
                    time.sleep(wait_seconds)
                else:
                    print(f"❌ Subset {subset_idx}/{total_subsets} permanently failed after {max_retries} retries.")

                    
def download_netcdf_ext(polygons_gdf : gpd.GeoDataFrame, output_folder : str, id_column : str, \
                        start_date : str, end_date : str, connection ) :
    """
    Function that downloads the netcdf files through the openEO API splitting
    the parcels in different subsets (maximum extent)

    Parameters
    ----------
    polygons_gdf : gpd.GeoDataFrame
        GeoDataFrame with the list of polygons to process
        
    output_folder : str
        String pointing to the output folder    
    
    id_column : str
        Identifier of the gdf column used to name the netcdf files

    start_date : str
        String defying the start date
        
    end_date : str
        String defying the stop date
        
    connection : openeo.rest.connection.Connection
        openeo connection

    Returns
    -------
    None.
    """
    # Reproject to EPSG:3035 in order to apply the buffer in meters
    polygons_gdf = polygons_gdf.to_crs("EPSG:3035")  # Example CRS, adjust as needed

    # Buffer by 50 meters
    buffer_value = 50
    gdf_buffered = polygons_gdf.copy()
    gdf_buffered["geometry"] = gdf_buffered.geometry.buffer(buffer_value)
    
    # Convert each buffered geometry to its bounding box
    gdf_extent = gdf_buffered.copy()
    gdf_extent["geometry"] = gdf_buffered.geometry.apply(lambda geom: box(*geom.bounds))

    # Split the gdf in different subsets
    subsets = split_extent(gdf_extent)
    
    max_retries = 3
    wait_seconds = 60
    
    # List of bands to process
    bands=["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12", "SCL"]
    
    # Get the dataset name
    dataset_name = output_folder.split("/")[-1].split(".")[0]
    
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for index, subset in enumerate(subsets):
        
        #creating datacube -  S2 bands
        subset = subset.to_crs(epsg=4326)
        spatial_extent = get_spatial_extent(subset)
        
        s2_bands = connection.load_collection(
            "SENTINEL2_L2A",
            temporal_extent=[start_date, end_date],
            spatial_extent=spatial_extent,
            bands = bands,
            max_cloud_cover=50
        )
            
        scl = s2_bands.band("SCL")
        cloud_mask = (scl == 0) | (scl == 1)
        #cloud_mask = (scl == 0) | (scl == 1) | (scl == 3) | (scl == 8) | (scl == 9) | (scl == 11)
        
        cloud_mask = cloud_mask.resample_cube_spatial(s2_bands)
        s2_bands_masked = s2_bands.mask(cloud_mask)
        
    
        #loading the dataset o json - for the spatial filter
        subset = subset.copy()
        for col in subset.columns:
            if pd.api.types.is_datetime64_any_dtype(subset[col]):
                subset[col] = subset[col].astype(str)
        
        features = json.loads(subset.to_json())    
    
        #spatial filter - using only the pixels intersecting the polygons
        s2_bands_masked = s2_bands.filter_spatial(features)
        
        #adding indices - using "awesome spectral indices" - a large number of indices available
        indices = append_indices(s2_bands_masked, indices=["NDVI", "NDWI"],
                                 platform="SENTINEL2")
        
        filename_prefix = f"S2_extract_{start_date}_{end_date}_parcelid"
        title =  f"S2_{dataset_name}_subset_{index}_{start_date}_{end_date}"
    
        #creating the job for server execution 
        job = indices.create_job(
            title="S2 bands and NDVI",
            description="Sentinel-2 L2A bands and NDVI",
            out_format="netCDF",
            filename_prefix=filename_prefix,
            feature_id_property="_parcel_id_norm",
            sample_by_feature=True,
        )
            
        for attempt in range(1, max_retries + 1):
            try:
                job.start_and_wait()
                status = job.status()
                if status == "finished":
                    print("job finished, downloading results")
                    job.get_results().download_files(output_folder)
                    break
                else:
                    raise RuntimeError(f"Job ended with status '{status}'")
            
            except Exception as e:
                print(f"job failed (attempt {attempt}): {e}")
                if attempt < max_retries:
                    time.sleep(wait_seconds)
                else:
                    print("job permanently failed after 3 retries.")
                    
       
    print("Processing of dataset completed")

#class for selecting interface modes: loading existing dataset or drawind polygons on the map
class ModeSelectorDashboard(widgets.VBox):

    def __init__(self, connection):

        super().__init__()

        self.connection = connection
        self.active_dashboard = None

        # Buttons
        self.btn_dataset = widgets.Button(
            description="Load existing dataset",
            button_style="primary",
            icon="folder-open",
            layout=widgets.Layout(width="260px", height="40px")
        )

        self.btn_draw = widgets.Button(
            description="Draw polygons on the map",
            button_style="success",
            icon="pencil",
            layout=widgets.Layout(width="260px", height="40px")
        )

        # container where the selected interface appears
        self.content = widgets.Output()

        # Layout
        self.children = [
            widgets.HTML("<h2>Sentinel-2 Processing Interface</h2>"),
            widgets.HBox([self.btn_dataset, self.btn_draw]),
            self.content
        ]

        # Bind events
        self.btn_dataset.on_click(self._show_dataset_interface)
        self.btn_draw.on_click(self._show_draw_interface)

    def set_mode_buttons_disabled(self, disabled=True):
        self.btn_dataset.disabled = disabled
        self.btn_draw.disabled = disabled

    def _show_dataset_interface(self, b):

        with self.content:
            clear_output()

            self.dataset_dashboard = OpenEODashboard(self.connection, mode_selector=self)
            self.active_dashboard = self.dataset_dashboard
            display(self.dataset_dashboard)

    def _show_draw_interface(self, b):

        with self.content:
            clear_output()

            self.draw_dashboard = DrawPolygonDashboard(self.connection, mode_selector=self)
            self.active_dashboard = self.draw_dashboard
            display(self.draw_dashboard)
    
class OpenEODashboard(widgets.VBox):
    """
    Class incapsulating the different functionalities for downloading Sentinel-2
    data
    """
    def __init__(self, connection, mode_selector=None):
        
        super().__init__()
        
        # 1. Store Members (The "State")
        self.connection = connection
        self.mode_selector = mode_selector
        self.gdf = None
        self.job_results = None
        self._is_running = False
        self.upload_filename = None
        self.upload_hash = None
        self.dataset_tag = None

        # 2. Initialize UI Components
        self.uploader = widgets.FileUpload(
            accept='.geojson,.json,.gpkg,.kml,.zip', 
            multiple=False, 
            description="Select dataset",
            layout=widgets.Layout(width='250px'),
            style={'description_width': 'initial'}
        )
        
        self.start_date = widgets.DatePicker(
            description='Start Date')
        
        self.end_date = widgets.DatePicker(
            description='End Date')
        
        self.col_dropdown = widgets.Dropdown(
            description="ID Column:", 
            disabled=True)
        
        self.run_button = widgets.Button(
            description='Run Process', 
            button_style='success', 
            icon='play'
        )

        self.choose_load = widgets.Button(
            description='Load dataset', 
            button_style='primary', 
            icon='check'
        )

        self.choose_draw = widgets.Button(
            description='Draw polygons', 
            button_style='primary', 
            icon='check'
        )

        # Parameters for verification
        # GeoJSON limits
        self.geojson_max_bytes = 100 * 1024 * 1024
        self.geojson_max_features = 20000

        # Date limits
        self.min_date = dt.date(2015, 1, 1)
        self.max_date_span_years = 3
        self.min_date_span_days = 3
        self.recent_date_threshold_days = 7

        # We disable the run button initially,
        # will be enabled once all selections are correct.
        self.run_button.disabled = True
        
        # Output for the "File Loaded" notification
        self.msg_output = widgets.Output()

        # Output for the date picker
        self.date_output = widgets.Output()

        # Output for the id column selector
        self.id_output = widgets.Output()

        # Output for the main process results (GDF, plots, etc.)
        self.main_output = widgets.Output()

        # Validity flags
        self._ok_upload = False
        self._ok_dates = False
        self._ok_id = False
        
        # 3. Setup Layout
        # We assign children to 'self' because 'self' IS a VBox
        self.children = [
            widgets.HTML("<h2>JRC OpenEO S2 Download</h2>"),
            widgets.VBox([widgets.Label("1. Upload your Polygon:"), self.uploader, self.msg_output]),
            widgets.VBox([widgets.Label("2. Select Time Range:"), widgets.HBox([self.start_date, self.end_date]), self.date_output]),
            widgets.VBox([widgets.Label("3. Select Parcel ID:"), self.col_dropdown, self.id_output]),
            widgets.VBox([widgets.Label("4. Execute:"), self.run_button]),
            self.main_output
        ]
        
        # 4. Bind Events
        self.uploader.observe(self._on_upload, names='value')
        self.start_date.observe(self._validate_start_date, names='value')
        self.end_date.observe(self._validate_end_date, names='value')
        self.col_dropdown.observe(self._validate_id_column, names='value')
        self.run_button.on_click(self._on_run_clicked)

    def _update_run_button(self):
        self.run_button.disabled = self._is_running or not (self._ok_upload and self._ok_id and self._ok_dates)

    def _set_running_state(self, is_running):
        self._is_running = is_running

        self.uploader.disabled = is_running
        self.start_date.disabled = is_running
        self.end_date.disabled = is_running
        self.col_dropdown.disabled = is_running or not self._ok_upload

        self._update_run_button()

        if self.mode_selector is not None:
            self.mode_selector.set_mode_buttons_disabled(is_running)

    def _read_upload_bytes(self):
        """Return (filename, content_bytes). Raise ValueError on basic issues."""
        if not self.uploader.value:
            raise ValueError("⚠️ Please upload a GeoJSON file.")

        file_info = self.uploader.value[0]
        filename = file_info.get("name", "uploaded.geojson")
        raw = file_info.get("content", b"")
        content = bytes(raw)

        if not content:
            raise ValueError("❌ Uploaded file is empty.")

        MAX_BYTES = self.geojson_max_bytes
        if len(content) > MAX_BYTES:
            raise ValueError(f"❌ File size exceeds the maximum limit of {MAX_BYTES/(1024*1024):.0f} MB.")

        #if not filename.lower().endswith(".geojson"):
        #    raise ValueError("❌ Invalid file format. Please upload a .geojson file.")

        return filename, content
    
    def _validate_geojson_text(self, content: bytes):
        """Decode + parse + basic structure checks. Return parsed JSON object."""
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("❌ File encoding error. Please ensure the file is UTF-8 encoded.")

        try:
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Invalid JSON: {e}")

        if obj.get("type") != "FeatureCollection":
            raise ValueError("❌ GeoJSON must be a FeatureCollection.")

        feats = obj.get("features")
        if not isinstance(feats, list) or len(feats) == 0:
            raise ValueError("❌ GeoJSON has no features.")

        MAX_FEATURES = self.geojson_max_features
        if len(feats) > MAX_FEATURES:
            raise ValueError(f"❌ Too many features ({len(feats)}). Limit is {MAX_FEATURES}.")
        
        # Geometry type check
        allowed = {"Polygon", "MultiPolygon"}
        for i, f in enumerate(feats):
            geom = (f or {}).get("geometry")
            if geom is None:
                raise ValueError(f"❌ Feature {i} has null geometry.")
            gtype = geom.get("type")
            if gtype not in allowed:
                raise ValueError(f"❌ Feature {i} has geometry type '{gtype}'. Allowed: {sorted(allowed)}")

        return obj

    def _validate_vector_dataset(self, file_name: str, content: bytes):
        """
        Validate an uploaded vector dataset and return it as a GeoDataFrame.
    
        Supported formats:
          - .geojson / .json
          - .gpkg
          - .kml
          - .zip   (ZIP containing exactly one shapefile)
          - .shp   (only if somehow already available as a complete file on disk; ZIP is preferred)
    
        Notes:
          - For shapefiles, prefer uploading a ZIP containing .shp, .shx, .dbf, and .prj.
          - Returns a GeoDataFrame instead of raw JSON.
        """
        ext = os.path.splitext(file_name)[1].lower()
    
        tmpdir = tempfile.mkdtemp(prefix="uploaded_vector_")
        input_path = os.path.join(tmpdir, file_name)
    
        # Save uploaded bytes to disk
        with open(input_path, "wb") as f:
            f.write(content)
    
        try:
            # ---- Load according to format ----
            if ext in {".geojson", ".json"}:
                # Optional: keep explicit JSON validation for clearer error messages
                try:
                    text = content.decode("utf-8")
                except UnicodeDecodeError:
                    raise ValueError("❌ File encoding error. Please ensure the file is UTF-8 encoded.")
    
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError as e:
                    raise ValueError(f"❌ Invalid JSON: {e}")
    
                if obj.get("type") != "FeatureCollection":
                    raise ValueError("❌ GeoJSON must be a FeatureCollection.")
    
                feats = obj.get("features")
                if not isinstance(feats, list) or len(feats) == 0:
                    raise ValueError("❌ GeoJSON has no features.")
    
                gdf = gpd.read_file(input_path)
    
            elif ext == ".gpkg":
                gdf = gpd.read_file(input_path)
    
            elif ext == ".kml":
                gdf = gpd.read_file(input_path, driver="KML")
    
            elif ext == ".zip":
                extract_dir = os.path.join(tmpdir, "unzipped")
                os.makedirs(extract_dir, exist_ok=True)
    
                try:
                    with zipfile.ZipFile(input_path, "r") as zf:
                        zf.extractall(extract_dir)
                except zipfile.BadZipFile:
                    raise ValueError("❌ Invalid ZIP file.")
    
                shp_files = []
                for root, _, files in os.walk(extract_dir):
                    for fn in files:
                        if fn.lower().endswith(".shp"):
                            shp_files.append(os.path.join(root, fn))
    
                if not shp_files:
                    raise ValueError("❌ ZIP file does not contain any .shp file.")
    
                if len(shp_files) > 1:
                    raise ValueError("❌ ZIP file contains multiple shapefiles. Please provide only one shapefile per ZIP.")
    
                gdf = gpd.read_file(shp_files[0])
    
            elif ext == ".shp":
                raise ValueError("❌ Please upload shapefiles as a ZIP containing .shp, .shx, .dbf, and .prj.")
    
            else:
                raise ValueError(f"❌ Unsupported file format '{ext}'. Allowed: .geojson, .json, .gpkg, .kml, .zip")
    
            # ---- Generic validation ----
            if gdf is None or gdf.empty:
                raise ValueError("❌ The uploaded dataset has no features.")
    
            if "geometry" not in gdf.columns:
                raise ValueError("❌ The uploaded dataset has no geometry column.")
    
            gdf = gdf[gdf.geometry.notnull()].copy()
            gdf = gdf[~gdf.geometry.is_empty].copy()
    
            if gdf.empty:
                raise ValueError("❌ All geometries are null or empty.")
    
            MAX_FEATURES = self.geojson_max_features
            if len(gdf) > MAX_FEATURES:
                raise ValueError(f"❌ Too many features ({len(gdf)}). Limit is {MAX_FEATURES}.")
    
            if gdf.crs is None:
                raise ValueError("❌ The uploaded dataset has no CRS defined.")
    
            allowed = {"Polygon", "MultiPolygon"}
            geom_types = gdf.geometry.geom_type
    
            invalid = [(i, gt) for i, gt in zip(gdf.index, geom_types) if gt not in allowed]
            if invalid:
                i, gt = invalid[0]
                raise ValueError(
                    f"❌ Feature {i} has geometry type '{gt}'. Allowed: {sorted(allowed)}"
                )
    
            return gdf
    
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"❌ Could not read the uploaded dataset: {e}")
    
    def _load_and_validate_gdf(self, content: bytes) -> gpd.GeoDataFrame:
        """Load with GeoPandas + minimal geometry/CRS sanity checks."""
        try:
            #gdf = gpd.read_file(io.BytesIO(content))
            gdf = load_vector_dataset(dataset_path)
        except Exception as e:
            raise ValueError(f"❌ Could not read GeoJSON with GeoPandas: {e}")

        if gdf.empty:
            raise ValueError("❌ No features loaded (GeoDataFrame is empty).")

        if "geometry" not in gdf.columns:
            raise ValueError("❌ No geometry column found.")

        # GeoPandas seems to default to EPSG:4326 if CRS is missing in the file,
        # so for example in case of our default file this leads to the CRS not matching the coordinates.
        # This should catch that.
        crs_str = str(gdf.crs)
        if "EPSG:4326" in crs_str:
            minx, miny, maxx, maxy = gdf.total_bounds
            # lon/lat bounds sanity
            if not (-180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90):
                raise ValueError(
                    "❌ CRS mismatch: GeoJSON was interpreted as EPSG:4326 (lon/lat), "
                    "but coordinates are outside valid lon/lat bounds. "
                    "Your GeoJSON is likely in a projected CRS (e.g., EPSG:3035). "
                    "Please re-export as EPSG:4326 or provide CRS explicitly."
                )

        # Just in case
        if gdf.crs is None:
            raise ValueError("❌ Missing CRS. Please export the GeoJSON with a defined CRS.")
        
        # GeoPandas-level geometry type check
        geom_types = set(gdf.geometry.geom_type.unique())
        allowed_types = {"Polygon", "MultiPolygon"}
        if not geom_types.issubset(allowed_types):
            raise ValueError(f"❌ Unsupported geometry types: {sorted(geom_types)}. Expected only Polygon/MultiPolygon.")

        # Geometry validity check
        invalid = ~gdf.geometry.is_valid
        if invalid.any():
            n_bad = int(invalid.sum())
            raise ValueError(
                f"❌ {n_bad} geometries are invalid (self-intersections, rings, etc.). "
                "Please fix them in GIS software (or we can auto-fix, if you want)."
            )

        return gdf


    def _on_upload(self, change):
        with self.msg_output:
            clear_output()
    
            self._ok_upload = False
            self.gdf = None
            self.upload_filename = None
            self.upload_hash = None
            self.dataset_tag = None
    
            try:
                filename, content = self._read_upload_bytes()
                self.upload_filename = filename
                self.upload_hash = _build_dataset_hash(content)
    
                # validate + load dataset
                gdf = self._validate_vector_dataset(filename, content)
    
                self.gdf = gdf
    
                # Populate ID dropdown (no validation yet)
                columns = [c for c in self.gdf.columns if c != "geometry"]
                if len(columns) == 0:
                    raise ValueError(
                        "❌ No attribute columns found (need at least one non-geometry column for Parcel ID)."
                    )
    
                self.col_dropdown.options = columns
                self.col_dropdown.disabled = False
    
                print(f"✅ Loaded {len(self.gdf)} parcels. Select time window and ID column to begin.")
                self._ok_upload = True
    
            except ValueError as e:
                print(str(e))
                self._ok_upload = False
    
            except Exception as e:
                print(f"❌ Error while processing upload: {e}")
                self._ok_upload = False
    
            finally:
                self._update_run_button()

    def _validate_id_column(self, change):
        with self.id_output:
            clear_output()
            val = self.col_dropdown.value

            if val is None:
                print("❌ Please select a valid ID column.")
                self._ok_id = False
                self._update_run_button()
                return
            
            self._ok_id = True

        self._update_run_button()

    def _validate_start_date(self, change):
        with self.date_output:
            clear_output()

            s = self.start_date.value
            e = self.end_date.value
            today = dt.date.today()

            if s is None or e is None:
                self._ok_dates = False
                print("⚠️ Please select both Start and End dates.")
                self._update_run_button()
                return

            if s > today:
                self._ok_dates = False
                print(f"❌ Start date ({s}) cannot be in the future.")
                self._update_run_button()
                return

            MIN_DATE = self.min_date
            if s < MIN_DATE:
                print("⚠️ Very early start date; Data availability may be limited.")

        # Validate end date manages the relationship between start and end date
        self._validate_end_date({"new": self.end_date.value})

    def _validate_end_date(self, change):
        with self.date_output:
            clear_output()

            s = self.start_date.value
            e = self.end_date.value
            today = dt.date.today()

            if s is None or e is None:
                self._ok_dates = False
                print("⚠️ Please select both Start and End dates.")
                self._update_run_button()
                return

            if s > today:
                self._ok_dates = False
                print(f"❌ Start date ({s}) cannot be in the future.")
                self._update_run_button()
                return

            if e < s:
                self._ok_dates = False
                print(f"❌ End date ({e}) cannot be earlier than Start date ({s}).")
                self._update_run_button()
                return

            span = (e - s).days

            MAX_SPAN_DAYS = self.max_date_span_years * 365
            MIN_SPAN_DAYS = self.min_date_span_days
            RECENT_THRESHOLD_DAYS = self.recent_date_threshold_days

            if s < self.min_date:
                print("⚠️ Very early start date; Data availability may be limited.")
            if e > today:
                print(f"⚠️ End date ({e}) is in the future. This is accepted, but the most recent data may not yet be available.")
            if span > MAX_SPAN_DAYS:
                print(f"⚠️ Large date range ({span} days); Processing may take longer.")
            if span < MIN_SPAN_DAYS:
                print(f"⚠️ Very short date range ({span} days); Data availability may be limited.")
            if e <= today and (today - e).days < RECENT_THRESHOLD_DAYS:
                print("⚠️ Recent end date; Data availability may be limited.")

            self._ok_dates = True

        self._update_run_button()                

    def _on_run_clicked(self, b):
        with self.main_output:
            clear_output()
            
            # Validation
            if not self.uploader.value:
                print("❌ Error: No file uploaded.")
                return
            if not self.start_date.value or not self.end_date.value:
                print("❌ Error: Please select both Start and End dates.")
                return
    
            if not self.col_dropdown.value :
                print("❌ Error: Please select the parcel ID.")
                return
            try:
                # Extract data from uploader
                file_info = self.uploader.value[0]
                filename = file_info['name']

                # Format dates to string
                start_str = self.start_date.value.strftime('%Y-%m-%d')
                end_str = self.end_date.value.strftime('%Y-%m-%d')

                # Build a dataset-specific folder.
                # This avoids cache collisions when a new file is uploaded with the same name.
                fname = _safe_stem(filename)
                upload_hash = self.upload_hash
                if upload_hash is None:
                    upload_hash = _build_dataset_hash(bytes(file_info.get('content', b'')))
                    self.upload_hash = upload_hash
                self.dataset_tag = _build_dataset_tag(start_str, end_str, upload_hash)
                output_folder = f"output/S2/{fname}__{upload_hash}"

                # Recover the parcel ID
                id_column = self.col_dropdown.value
                self.id_column = id_column
                self.output_folder = output_folder

                self.gdf = add_normalized_id_column(self.gdf, self.id_column)

                print(f"🗺️ Processing file: {filename}...")
                #print(f"Dataset hash: {upload_hash}")
                print(f"Date range: {start_str} → {end_str}")
                
                # Call your external function
                # Ensure your function signature is: process_data(gdf, filename, start_date, end_date)
                download_netcdf(self.gdf, output_folder, id_column, start_str, end_str, self.connection)
                
                print("Processing finished. Opening map viewer...")
                map_widget = MapAndPlotWidget(self)
                display(map_widget)
                
            except Exception as e:
                print(f"❌ Processing Error: {e}")

class DrawPolygonDashboard(widgets.VBox):
    """
    Dashboard for manually drawing polygons on a map, processing them with openEO,
    and then reusing the same map for parcel visualization.
    """

    def __init__(self, connection, mode_selector=None):

        super().__init__()

        self.connection = connection
        self.mode_selector = mode_selector
        self.session_id = self._generate_session_id()
        self._is_running = False
        self.upload_filename = None
        self.upload_hash = None
        self.dataset_tag = None

        # Attributes expected later by MapAndPlotWidget
        self.gdf = None
        self.id_column = "aoi_id"
        self.output_folder = None
        self.geojson_path = None

        # Date limits
        self.min_date = dt.date(2015, 1, 1)
        self.max_date_span_years = 3
        self.min_date_span_days = 3
        self.recent_date_threshold_days = 7

        self.norm_id_column = "_parcel_id_norm"

        # Validation flag
        self._ok_dates = False

        self.basemap_selector = widgets.Dropdown(
            options=[
                ("OpenStreetMap", "OpenStreetMap.Mapnik"),
                ("Esri World Imagery", "Esri.WorldImagery"),
                ("OpenTopoMap", "OpenTopoMap"),
                ("CartoDB Positron", "CartoDB.Positron"),
                ("CartoDB DarkMatter", "CartoDB.DarkMatter"),
            ],
            value="OpenStreetMap.Mapnik",
            description="Basemap:",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="270px")
        )
        self.basemap_selector.observe(self._on_basemap_change, names="value")

        self.basemap_box = widgets.VBox(
            [self.basemap_selector],
            layout=widgets.Layout(
                padding="6px",
                width="290px"
            )
        )

        # Date pickers
        self.start_date = widgets.DatePicker(
            description="Start date:",
            style={"description_width": "initial"}
        )

        self.end_date = widgets.DatePicker(
            description="End date:",
            style={"description_width": "initial"}
        )
        
        # Run button
        self.run_button = widgets.Button(
            description="Run Process",
            button_style="success",
            icon="play",
            disabled=True
        )

        # Output
        self.date_output = widgets.Output()
        self.output = widgets.Output()

        # Map
        self.m = leafmap.Map(center=(45.78, 8.62), zoom=15)

        # Make leaflet edit vertices more visible
        self._set_leaflet_vertex_size(px=8)

        # Setup drawing system
        self._setup_draw_control()

        self.basemap_control = WidgetControl(
            widget=self.basemap_box,
            position="topright"
        )
        self.m.add_control(self.basemap_control)

        # Layout
        self.controls_top = widgets.HBox([
            self.start_date,
            self.end_date,
            self.run_button
        ])

        self.controls_box = widgets.VBox([
            self.controls_top,
            self.date_output
        ])

        # dedicated area where visualisation controls/results will appear
        self.viewer_box = widgets.Output()
        self.viewer = None

        self.children = [
            self.m,
            self.controls_box,
            self.output,
            self.viewer_box
        ]

        # Events
        self.start_date.observe(self._validate_start_date, names="value")
        self.end_date.observe(self._validate_end_date, names="value")
        self.run_button.on_click(self._run_process)

    def _on_basemap_change(self, change):
        if change["name"] != "value":
            return
    
        basemap_name = change["new"]
    
        try:
            known_basemaps = {
                "OpenStreetMap.Mapnik",
                "Esri.WorldImagery",
                "OpenTopoMap",
                "CartoDB.Positron",
                "CartoDB.DarkMatter",
            }
    
            to_remove = []
            for layer in self.m.layers:
                layer_name = getattr(layer, "name", "")
                if layer_name in known_basemaps:
                    to_remove.append(layer)
    
            for layer in to_remove:
                self.m.remove_layer(layer)
    
            self.m.add_basemap(basemap_name)
    
        except Exception as e:
            with self.output:
                print(f"❌ Could not change basemap: {e}")

    def _generate_session_id(self):
        now = dt.datetime.now(ZoneInfo("Europe/Rome"))
        t = now.strftime("%Y%m%d_%H%M%S")
        u = str(uuid.uuid4())[:6]
        return f"{t}_{u}"

    def _build_run_tag(self, start_api, end_api):
        """
        Build a unique tag for the current run, based on dates + current polygons.
        This ensures that if polygons are edited and the user runs again,
        new outputs are produced and the viewer always points to the latest run.
        """
        payload = json.dumps(self.features_fc, sort_keys=True).encode("utf-8")
        draw_hash = hashlib.md5(payload).hexdigest()[:10]
        return f"{start_api}_{end_api}_{draw_hash}"

    def _update_run_button(self):
        self.run_button.disabled = self._is_running or not self._ok_dates

    def _set_running_state(self, is_running):
        self._is_running = is_running

        self.start_date.disabled = is_running
        self.end_date.disabled = is_running
        self.dc.edit = not is_running
        self.dc.remove = not is_running

        self._update_run_button()

        if self.mode_selector is not None:
            self.mode_selector.set_mode_buttons_disabled(is_running)

    def _validate_start_date(self, change):
        with self.date_output:
            clear_output()

            s = self.start_date.value
            e = self.end_date.value
            today = dt.date.today()

            if s is None or e is None:
                self._ok_dates = False
                print("⚠️ Please select both Start and End dates.")
                self._update_run_button()
                return

            if s > today:
                self._ok_dates = False
                print(f"❌ Start date ({s}) cannot be in the future.")
                self._update_run_button()
                return

            if s < self.min_date:
                print("⚠️ Very early start date; Data availability may be limited.")

        self._validate_end_date({"new": self.end_date.value})

    def _validate_end_date(self, change):
        with self.date_output:
            clear_output()

            s = self.start_date.value
            e = self.end_date.value
            today = dt.date.today()

            if s is None or e is None:
                self._ok_dates = False
                print("⚠️ Please select both Start and End dates.")
                self._update_run_button()
                return

            if s > today:
                self._ok_dates = False
                print(f"❌ Start date ({s}) cannot be in the future.")
                self._update_run_button()
                return

            if e < s:
                self._ok_dates = False
                print(f"❌ End date ({e}) cannot be earlier than Start date ({s}).")
                self._update_run_button()
                return

            span = (e - s).days

            MAX_SPAN_DAYS = self.max_date_span_years * 365
            MIN_SPAN_DAYS = self.min_date_span_days
            RECENT_THRESHOLD_DAYS = self.recent_date_threshold_days

            if s < self.min_date:
                print("⚠️ Very early start date; Data availability may be limited.")
            if e > today:
                print(f"⚠️ End date ({e}) is in the future. This is accepted, but the most recent data may not yet be available.")
            if span > MAX_SPAN_DAYS:
                print(f"⚠️ Large date range ({span} days); Processing may take longer.")
            if span < MIN_SPAN_DAYS:
                print(f"⚠️ Very short date range ({span} days); Data availability may be limited.")
            if e <= today and (today - e).days < RECENT_THRESHOLD_DAYS:
                print("⚠️ Recent end date; Data availability may be limited.")

            self._ok_dates = True

        self._update_run_button()
    
    def _set_leaflet_vertex_size(self, px=6, border_px=1):
        from IPython.display import display
        from ipywidgets import HTML

        half = px / 2
        display(HTML(f"""
        <style>
        .leaflet-div-icon.leaflet-editing-icon {{
          width: {px}px !important;
          height: {px}px !important;
          margin-left: -{half}px !important;
          margin-top: -{half}px !important;
          border-width: {border_px}px !important;
        }}
        </style>
        """))

    def _setup_draw_control(self):
        # Remove leafmap default draw control if present
        try:
            self.m.remove_control(self.m.draw_control)
        except Exception:
            pass

        self.dc = DrawControl(
            polygon={
                "shapeOptions": {
                    "color": "red",
                    "fillColor": "red",
                    "fillOpacity": 0.2,
                    "weight": 2,
                    "dashArray": "6,4"
                }
            },
            polyline={},
            rectangle={},
            circlemarker={},
            marker={},
            edit=True,
            remove=True,
        )

        self.m.add_control(self.dc)

        # Storage for polygons
        self.features_fc = {"type": "FeatureCollection", "features": []}
        self.next_id = {"val": 1}

        # Polygon layer
        self.polys_layer = GeoJSON(
            data=self.features_fc,
            style={
                "color": "red",
                "weight": 2,
                "fillColor": "red",
                "fillOpacity": 0.2
            },
            hover_style={
                "color": "yellow",
                "weight": 3,
                "fillOpacity": 0.3
            }
        )
        self.m.add_layer(self.polys_layer)

        # Dedicated label layer
        self.labels_group = LayerGroup(layers=[])
        self.m.add_layer(self.labels_group)

        # Bind draw callback
        self.dc.on_draw(self._on_draw)

    def _refresh_polygons_layer(self):
        self.polys_layer.data = {
            "type": "FeatureCollection",
            "features": list(self.features_fc["features"])
        }

    def add_plain_number_label(self, lat, lon, text):
        icon = DivIcon(
            html=f"""
            <div style="
                color: #000;
                font-size: 16px;
                font-weight: 700;
                line-height: 1;
                text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff,
                             -1px  1px 0 #fff, 1px  1px 0 #fff;
                pointer-events: none;
            ">{text}</div>
            """,
            icon_size=(0, 0),
            icon_anchor=(0, 0),
        )
        mk = Marker(location=(lat, lon), icon=icon)
        self.labels_group.layers = tuple(list(self.labels_group.layers) + [mk])

    def rebuild_labels(self):
        self.labels_group.layers = tuple()
    
        for f in self.features_fc["features"]:
            geom = shape(f["geometry"])
            if geom is None or geom.is_empty:
                continue
    
            c = geom.centroid
            aoi_id = f.get("properties", {}).get("aoi_id")
            if aoi_id is not None:
                self.add_plain_number_label(c.y, c.x, str(aoi_id))

    def _on_draw(self, target, action, geo_json):
        """
        Handles polygon create / delete / edit.
        """

        if action == "created":
            aoi_id = self.next_id["val"]
            self.next_id["val"] += 1

            geo_json.setdefault("properties", {})
            geo_json["properties"]["aoi_id"] = aoi_id

            self.features_fc["features"].append(geo_json)

            self._refresh_polygons_layer()
            self.rebuild_labels()

        elif action == "deleted":
            deleted_geom = shape(geo_json["geometry"])

            kept = []
            deleted = False

            for f in self.features_fc["features"]:
                geom = shape(f["geometry"])
                if (not deleted) and geom.equals(deleted_geom):
                    deleted = True
                    continue
                kept.append(f)

            self.features_fc["features"] = kept

            self._refresh_polygons_layer()
            self.rebuild_labels()

        elif action == "edited":
            edited_props = geo_json.get("properties", {})
            edited_id = edited_props.get("aoi_id")

            if edited_id is not None:
                for i, f in enumerate(self.features_fc["features"]):
                    if f.get("properties", {}).get("aoi_id") == edited_id:
                        self.features_fc["features"][i] = geo_json
                        break

            self._refresh_polygons_layer()
            self.rebuild_labels()

    def _run_process(self, b):
        with self.output:
            clear_output()

            if not self.features_fc["features"]:
                print("No polygons drawn.")
                return

            if self.start_date.value is None or self.end_date.value is None:
                print("Please select both start and end dates.")
                return

            if not self._ok_dates:
                print("Please correct the date selection before running.")
                return

            self._set_running_state(True)

            try:
                # Minimal fix: when the user edits polygons, self.features_fc can still
                # contain the pre-edit geometry. Right before processing, rebuild the
                # current features from the DrawControl state and preserve aoi_id when possible.
                current_features = self.features_fc
                try:
                    dc_data = getattr(self.dc, "data", None)
                    if dc_data:
                        rebuilt = []
                        previous_features = list(self.features_fc.get("features", []))

                        for idx, feat in enumerate(dc_data):
                            props = dict(feat.get("properties", {}) or {})
                            if "aoi_id" not in props and idx < len(previous_features):
                                prev_props = previous_features[idx].get("properties", {}) or {}
                                if "aoi_id" in prev_props:
                                    props["aoi_id"] = prev_props["aoi_id"]

                            rebuilt.append({
                                "type": "Feature",
                                "geometry": feat.get("geometry"),
                                "properties": props,
                            })

                        if rebuilt:
                            current_features = {"type": "FeatureCollection", "features": rebuilt}
                            self.features_fc = current_features
                except Exception:
                    pass

                # Convert current drawn polygons to GeoDataFrame
                self.gdf = features_fc_to_gdf(current_features)

                # Dates for API
                start_api = self.start_date.value.strftime("%Y-%m-%d")
                end_api = self.end_date.value.strftime("%Y-%m-%d")

                # Build a run-specific tag/folder from current polygons + current dates
                run_tag = self._build_run_tag(start_api, end_api)
                self.dataset_tag = run_tag

                self.output_folder = os.path.join(
                    "output",
                    "S2",
                    "manual_parcel",
                    f"session_{self.session_id}",
                    run_tag
                )
                os.makedirs(self.output_folder, exist_ok=True)

                # Save current polygons for reproducibility
                self.geojson_path = os.path.join(self.output_folder, "polygons.geojson")
                self.gdf.to_file(self.geojson_path, driver="GeoJSON")

                #print(f"Session ID: {self.session_id}")
                #print(f"Run tag: {run_tag}")
                #print(f"Saved polygons: {self.geojson_path}")
                #print(f"Running process for {len(self.gdf)} polygon(s)...")

                # Download NetCDFs for the CURRENT polygons and CURRENT dates
                download_netcdf(
                    self.gdf,
                    self.output_folder,
                    self.id_column,
                    start_api,
                    end_api,
                    self.connection
                )

                print("Processing finished.")

                # Refresh viewer so it always points to the latest run
                self.viewer = MapAndPlotWidget(self)

                with self.viewer_box:
                    clear_output()
                    display(self.viewer.controls_box)
                    display(self.viewer.output_log)

            except Exception as e:
                print(f"❌ Processing Error: {e}")

            finally:
                self._set_running_state(False)

def getInterface(connection):
    return ModeSelectorDashboard(connection)

#%% Map and plot widget
class MapAndPlotWidget(widgets.VBox):
    """
    Class containing the map and the interfaces for plotting specialized plots
    """
    def __init__(self, openDashboard):
        super().__init__()

        # Member objects
        self.gdf = add_normalized_id_column(openDashboard.gdf, openDashboard.id_column)
        self.id_column = openDashboard.id_column
        self.norm_id_column = "_parcel_id_norm"
        self.output_folder = openDashboard.output_folder

        self.output_log = widgets.Output()

        start_date = openDashboard.start_date.value.strftime('%Y-%m-%d')
        end_date = openDashboard.end_date.value.strftime('%Y-%m-%d')
        self.dataset_tag = getattr(openDashboard, 'dataset_tag', _build_dataset_tag(start_date, end_date))
        self.netcdf_prefix = f"S2_extract_{start_date}_{end_date}_parcelid_"

        # Reuse existing map if provided, otherwise create one
        self._reusing_existing_map = False
        self._from_draw_dashboard = False

        if hasattr(openDashboard, "map"):
            self.m = openDashboard.map
            self._reusing_existing_map = True
        elif hasattr(openDashboard, "m"):
            self.m = openDashboard.m
            self._reusing_existing_map = True
        else:
            self.m = leafmap.Map(center=[0, 0], zoom=2)

        self.labels_group = LayerGroup(layers=[])
        self.m.add_layer(self.labels_group)

        self._refreshing_labels = False
        self.m.observe(self._on_map_layers_change, names="layers")

        self._from_draw_dashboard = isinstance(openDashboard, DrawPolygonDashboard)

        self._id_ok = True
        self._plot_type_ok = False
        self._plot_options_ok = False

        # ID combobox setup: use normalized IDs only
        unique_vals = sorted(self.gdf[self.norm_id_column].dropna().unique().tolist())
        self.id_dropdown = widgets.Combobox(
            description="Parcel ID:",
            options=unique_vals,
            value=unique_vals[0] if unique_vals else "",
            placeholder="Type to search a parcel…",
            ensure_option=True,
            style={'description_width': 'initial'}
        )
        
        # Plot type and options setup
        # Define the data mapping for the dropdowns
        self.plot_options = {
            'stat summary': [],
            'Calendar View': ['NIR-SWIR-RED', 'RED-GREEN-BLUE', 'Scatter B04-B08', 'NDVI']
        }
        
        self.dd_plot_type = widgets.Dropdown(
                            options=list(self.plot_options.keys()),
                            description='Plot Type:',
                            style={'description_width': 'initial'},
                            value=None
                    )
        
        self.dd_plot_param = widgets.Dropdown(
                            description='Options:',
                            style={'description_width': 'initial'},
                            disabled=True
                    )
        
        # Display button setup
        self.btn_display = widgets.Button(
                            description='Display',
                            button_style='primary', # Changes color to blue
                            icon='check',
                            disabled=True
                    )
                        
        # Interface Layout
        self.controls_box = widgets.HBox([
            self.id_dropdown,
            self.dd_plot_type,
            self.dd_plot_param,
            self.btn_display
        ])

        self.basemap_selector = widgets.Dropdown(
            options=[
                ("OpenStreetMap", "OpenStreetMap.Mapnik"),
                ("Esri World Imagery", "Esri.WorldImagery"),
                ("OpenTopoMap", "OpenTopoMap"),
                ("CartoDB Positron", "CartoDB.Positron"),
                ("CartoDB DarkMatter", "CartoDB.DarkMatter"),
            ],
            value="OpenStreetMap.Mapnik",
            description="Basemap:",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="270px")
        )
        
        self.basemap_selector.observe(self._on_basemap_change, names="value")
        
        self.basemap_box = widgets.VBox(
            [self.basemap_selector],
            layout=widgets.Layout(
                padding="6px",
                width="290px"
            )
        )
        
        self.basemap_control = WidgetControl(
            widget=self.basemap_box,
            position="topright"
        )
        if not (self._reusing_existing_map and self._from_draw_dashboard):
            self.m.add_control(self.basemap_control)        
        
        self.children = [
            self.m,
            self.controls_box,
            self.output_log
        ]
        
        # Bind Events
        self.id_dropdown.observe(self._on_id_change, names='value')
        self.dd_plot_type.observe(self._on_plot_type_change, names='value')
        self.dd_plot_param.observe(self._on_plot_param_change, names='value')
        self.btn_display.on_click(self._on_display_button_clicked)

        
        self._update_display_button()

        # Initialize map layers
        self._on_start()

    def add_plain_number_label(self, lat, lon, text):
        icon = DivIcon(
            html=f"""
            <div style="
                color: #000;
                font-size: 16px;
                font-weight: 700;
                line-height: 1;
                text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff,
                             -1px  1px 0 #fff, 1px  1px 0 #fff;
                pointer-events: none;
            ">{text}</div>
            """,
            icon_size=(0, 0),
            icon_anchor=(0, 0),
        )
        mk = Marker(location=(lat, lon), icon=icon)
        self.labels_group.layers = tuple(list(self.labels_group.layers) + [mk])

    def refresh_labels_on_top(self):
        """
        Rebuild labels and re-add the label layer so labels stay visible
        after clicks/popups.
        """
        try:
            self.m.remove_layer(self.labels_group)
        except Exception:
            pass
    
        self.labels_group = LayerGroup(layers=[])
        self.m.add_layer(self.labels_group)
        self.rebuild_labels()

    def _on_map_layers_change(self, change):
        """
        When the popup is closed and removed from the map, restore the labels
        so they become visible again.
        """
        if self._refreshing_labels:
            return
    
        try:
            has_popup = any(isinstance(layer, Popup) for layer in self.m.layers)
        except Exception:
            return
    
        if not has_popup:
            self._refreshing_labels = True
            try:
                self.refresh_labels_on_top()
            finally:
                self._refreshing_labels = False
    
    def rebuild_labels(self):
        self.labels_group.layers = tuple()
    
        for _, row in self.gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
    
            c = geom.centroid
            parcel_id = row[self.norm_id_column]
            if parcel_id is not None:
                self.add_plain_number_label(c.y, c.x, parcel_id)
            
    def _get_netcdf_path(self, parcel_id):
        parcel_id = normalize_parcel_id(parcel_id)
        return os.path.join(self.output_folder, f"{self.netcdf_prefix}{parcel_id}.nc")
    
    def _get_stats_csv_path(self, parcel_id):
        parcel_id = normalize_parcel_id(parcel_id)
        stat_dir = os.path.join(self.output_folder, "band_stats")
        os.makedirs(stat_dir, exist_ok=True)
        return os.path.join(stat_dir, f"{parcel_id}_stats_{self.dataset_tag}.csv")
    
    def _get_ndvi_plot_path(self, parcel_id):
        parcel_id = normalize_parcel_id(parcel_id)
        ndvi_dir = os.path.join(self.output_folder, 'ndvi')
        os.makedirs(ndvi_dir, exist_ok=True)
        return os.path.join(ndvi_dir, f"{parcel_id}_NDVI_{self.dataset_tag}.png")
    
    def _get_line_plot_path(self, parcel_id, band_name):
        parcel_id = normalize_parcel_id(parcel_id)
        safe_band = str(band_name).replace(' ', '_').replace('/', '-')
        plots_dir = os.path.join(self.output_folder, 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        return os.path.join(plots_dir, f"{parcel_id}_{safe_band}_{self.dataset_tag}.png")
    
    def _get_cview_png_path(self, parcel_id, suffix):
        parcel_id = normalize_parcel_id(parcel_id)
        cview_dir = os.path.join(self.output_folder, 'cview')
        os.makedirs(cview_dir, exist_ok=True)
        return os.path.join(cview_dir, f"{parcel_id}_{suffix}_{self.dataset_tag}.png")
    
    def _get_cview_pickle_path(self, parcel_id, suffix):
        parcel_id = normalize_parcel_id(parcel_id)
        cview_dir = os.path.join(self.output_folder, 'cview')
        os.makedirs(cview_dir, exist_ok=True)
        return os.path.join(cview_dir, f"{parcel_id}_{suffix}_{self.dataset_tag}.pickle")

    def _compute_stats_csv(self, parcel_id, netcdf_path, csv_filename):
        parcel_id = normalize_parcel_id(parcel_id)
    
        parcel = self.gdf[self.gdf[self.norm_id_column] == parcel_id]
    
        if parcel.empty:
            raise ValueError(f"No parcel found for normalized ID: {parcel_id}")
    
        out_dir = os.path.dirname(csv_filename)
        default_csv = os.path.join(out_dir, f"{parcel_id}_stats.csv")
    
        if os.path.exists(default_csv):
            os.remove(default_csv)
    
        with xr.open_dataset(netcdf_path) as ds:
            crs_wkt = ds["crs"].attrs.get("crs_wkt")
            if crs_wkt:
                ds = ds.rio.write_crs(crs_wkt)
    
            nu.ds_statistics_to_parcel_csv(
                ds,
                parcel,
                parcel_id,
                out_dir=out_dir,
                scl_list=[0, 1, 3, 8, 9, 11]
            )
    
        if os.path.exists(default_csv) and default_csv != csv_filename:
            if os.path.exists(csv_filename):
                os.remove(csv_filename)
            os.replace(default_csv, csv_filename)

    def _update_display_button(self):
        """Only update the Display button when all required selections are made."""
        self.btn_display.disabled = not (self._id_ok and self._plot_type_ok and self._plot_options_ok)

    def _on_id_change(self, change):
        with self.output_log:
            selected_val = normalize_parcel_id(change['new'])
            if selected_val is None:
                return
    
            subset = self.gdf[self.gdf[self.norm_id_column] == selected_val]
            if subset.empty:
                return
    
            self.refresh_labels_on_top()
    
            try:
                self.m.zoom_to_gdf(subset)
            except Exception:
                pass
    
            self._update_display_button()
                
    def _on_basemap_change(self, change):
        if change["name"] != "value":
            return
    
        basemap_name = change["new"]
    
        try:
            known_basemaps = {
                "OpenStreetMap.Mapnik",
                "Esri.WorldImagery",
                "OpenTopoMap",
                "CartoDB.Positron",
                "CartoDB.DarkMatter",
            }
    
            to_remove = []
            for layer in self.m.layers:
                layer_name = getattr(layer, "name", "")
                if layer_name in known_basemaps:
                    to_remove.append(layer)
    
            for layer in to_remove:
                self.m.remove_layer(layer)
    
            self.m.add_basemap(basemap_name)
    
        except Exception as e:
            with self.output_log:
                print(f"❌ Could not change basemap: {e}")

    def _on_plot_type_change(self, change):
        """
        Logic to be applied when a type of plot is selected
        """
        plot_type = change['new']

        # reset options every time
        self.dd_plot_param.options = []
        self.dd_plot_param.value = None
        self.dd_plot_param.disabled = True

        self._plot_type_ok = plot_type is not None
        self._plot_options_ok = False
        self._update_display_button()

        if plot_type is None:
            return
              
        # plot_type contains the selected value of dropdown_type
        if plot_type == 'stat summary' :
    
            # get the parcel ID
            parcel_id = self.id_dropdown.value
    
            output_path = self.output_folder
            netcdf_path = self._get_netcdf_path(parcel_id)
                
            # check if the csv with the summary statistics is available
            if not os.path.exists(netcdf_path) :
                print('Extract the data first')
                return
    
            # if here, the netcdf file is available. Check if the parcel statistics have been already extracted
            csv_filename = self._get_stats_csv_path(parcel_id)
            if not os.path.exists(csv_filename):
                self._compute_stats_csv(parcel_id, netcdf_path, csv_filename)
    
            # Read the csv as dataframe
            stat_f = pd.read_csv(csv_filename)
    
            # Determine the bands available
            bands = np.unique(stat_f['band'])
    
            self.dd_plot_param.options = bands
        
        elif plot_type == 'Calendar View': 
            # Base options always available for calendar view
            options = ['NIR-SWIR-RED', 'RED-GREEN-BLUE', 'Scatter B04-B08']

            # Add NDVI only if it exists in the selected dataset
            parcel_id = self.id_dropdown.value
            if parcel_id is not None:
                output_path = self.output_folder
                netcdf_path = self._get_netcdf_path(parcel_id)
                if os.path.exists(netcdf_path):
                    try:
                        with xr.open_dataset(netcdf_path) as ds:
                            if 'NDVI' in ds.data_vars:
                                options.append('NDVI')
                    except Exception:
                        pass

            self.dd_plot_param.options = options

        # enable param dropdown if we actually have options
        if self.dd_plot_param.options:
            self.dd_plot_param.disabled = False
            self.dd_plot_param.value = self.dd_plot_param.options[0]  # auto-select
            self._plot_options_ok = True
        else:
            self.dd_plot_param.disabled = True
            self._plot_options_ok = False

        self._update_display_button()

    def _on_plot_param_change(self, change):
        self._plot_options_ok = (change['new'] is not None)
        self._update_display_button()

    def _on_display_button_clicked(self, b):
        with self.output_log:
            clear_output(wait=True) # Clears previous plot

            if self.btn_display.disabled:
                print("⚠️ Select Parcel ID, Plot Type and Options first.")
                return
            
            selected_type = self.dd_plot_type.value
            
            if selected_type == 'stat summary':
                out = self.get_line_plot()
    
            elif selected_type == 'Calendar View':
                out = self.get_calendar_view()

            else:
                print("❌ Unknown plot type.")
                return

            if out is None:
                print("⚠️ Nothing to display.")
                return
            
            fig, ax = out
            plt.show()
            plt.close(fig)
            
    def _gdf_to_clean_geojson(self, gdf):
        gdf = make_gdf_json_safe(gdf)
        geojson = json.loads(gdf.to_json())
    
        reserved_props = {
            "style",
            "hover_style",
            "styleUrl",
            "icon",
            "icons",
        }
    
        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            if not isinstance(props, dict):
                feature["properties"] = {}
                continue
    
            for key in list(props.keys()):
                if key in reserved_props:
                    del props[key]
    
        return geojson

    def _on_start(self):
        """Initialize map layers and interactions"""
        with self.output_log:
            self.gdf = self.gdf.to_crs(epsg=4326)
    
            # In the draw-polygon workflow we reuse the same map that already
            # contains the user polygons. Do not add the dataset again and do
            # not zoom again after processing, otherwise the pre-edit and
            # post-edit shapes can both end up visible.
            if self._reusing_existing_map and self._from_draw_dashboard:
                return
    
            style = {'fillOpacity': 0.3, 'weight': 1, 'color': '#3388ff'}
            hover_style = {'fillOpacity': 0.6, 'color': 'red'}
    
            old_layer = self.m.find_layer("Parcels")
            if old_layer:
                self.m.remove_layer(old_layer)
    
            clean_geojson = self._gdf_to_clean_geojson(self.gdf)
    
            self.m.add_geojson(
                clean_geojson,
                layer_name="Parcels",
                style=style,
                hover_style=hover_style
            )

            try:
                self.m.remove_layer(self.labels_group)
            except Exception:
                pass
            
            self.labels_group = LayerGroup(layers=[])
            self.m.add_layer(self.labels_group)
            self.rebuild_labels()
    
            layer = self.m.find_layer("Parcels")
            if layer:
                layer.on_click(self._handle_click_on_map)
    
            self.m.zoom_to_gdf(self.gdf)

    def _set_dropdown_silently(self, value):
        """Set dropdown value without triggering on_value_change."""
        self.id_dropdown.unobserve(self._on_id_change, names="value")
        try:
            self.id_dropdown.value = value
        finally:
            self.id_dropdown.observe(self._on_id_change, names="value")

    def _handle_click_on_map(self, feature, **kwargs):
        """Actions to perform when a parcel is clicked"""
        with self.output_log:
            props = feature.get('properties', {})
            parcel_id = normalize_parcel_id(props.get(self.id_column))
    
            if parcel_id is None:
                return
    
            self._set_dropdown_silently(parcel_id)
    
            output_path = self.output_folder
            netcdf_path = self._get_netcdf_path(parcel_id)
    
            if os.path.exists(netcdf_path):
                csv_filename = self._get_stats_csv_path(parcel_id)
                if not os.path.exists(csv_filename):
                    self._compute_stats_csv(parcel_id, netcdf_path, csv_filename)
    
                ndvi_image_path = self._get_ndvi_plot_path(parcel_id)
                if not os.path.exists(ndvi_image_path):
                    fig_ndvi, _ = cgu.plot_csv_parcel(csv_filename, band_to_plot="NDVI", to_file=False)
                    fig_ndvi.savefig(ndvi_image_path, bbox_inches='tight', dpi=100)
                    plt.close(fig_ndvi)
    
                if os.path.exists(ndvi_image_path):
                    with open(ndvi_image_path, "rb") as f:
                        encoded_string = base64.b64encode(f.read()).decode()
                    image_data_uri = f"data:image/png;base64,{encoded_string}"
                    html_content = f"""
                        <div style="width:100%">
                            <h4>Parcel ID: {parcel_id}</h4>
                            <img src="{image_data_uri}" style="width:500px; height:auto;" alt="NDVI Plot">
                        </div>
                    """
                else:
                    html_content = "<b>Plot generated but file not found.</b>"
            else:
                html_content = f"<b>Data not extracted for ID: {parcel_id}</b><br>Please run extraction first."
    
            for layer in list(self.m.layers):
                if isinstance(layer, Popup):
                    self.m.remove_layer(layer)
    
            popup = Popup(
                location=kwargs.get("coordinates"),
                child=HTML(value=html_content),
                close_button=True,
                max_width=550,
                auto_pan=True,
                auto_pan_padding=(20, 20),
            )
    
            self.refresh_labels_on_top()
            self.m.add_layer(popup)


    def get_line_plot(self):
        """ 
        Function to generate the line plot
        """
        if self.dd_plot_param.value is None:
            return None
    
        parcel_id = self.id_dropdown.value
        band_name = self.dd_plot_param.value
    
        output_path = self.output_folder
        netcdf_path = self._get_netcdf_path(parcel_id)
    
        if not os.path.exists(netcdf_path):
            print("Extract the data first")
            return None
    
        csv_filename = self._get_stats_csv_path(parcel_id)

        if not os.path.exists(csv_filename):
            self._compute_stats_csv(parcel_id, netcdf_path, csv_filename)
    
        fig, ax = cgu.plot_csv_parcel_std(
            csv_filename,
            band_to_plot=band_name,
            to_file=False
        )

        plot_png = self._get_line_plot_path(parcel_id, band_name)
        if (fig is not None) and (not os.path.exists(plot_png)):
            fig.savefig(plot_png, bbox_inches='tight', dpi=100)
    
        return fig, ax

    def get_calendar_view(self, stretch_table=None):
        """
        Function to generate the calendar view for RGB/false-color or single-band NDVI.
        """
        if self.dd_plot_param.value is None:
            return None
    
        if self.dd_plot_param.value == 'NIR-SWIR-RED':
            stretch_table = {
                'B08': [1200, 5700],
                'B11': [800, 4100],
                'B04': [150, 2800]
            }
            bandlist = list(stretch_table.keys())
            sc_dict = None
            is_scatter = False
    
        elif self.dd_plot_param.value == 'RED-GREEN-BLUE':
            stretch_table = {
                'B04': [0, 1500],
                'B03': [0, 1500],
                'B02': [0, 1500]
            }
            bandlist = list(stretch_table.keys())
            sc_dict = None
            is_scatter = False
    
        elif self.dd_plot_param.value == 'NDVI':
            stretch_table = None
            bandlist = ['NDVI']
            sc_dict = None
            is_scatter = False
    
        elif self.dd_plot_param.value == 'Scatter B04-B08':
            stretch_table = None
            bandlist = None
            sc_dict = {
                'x': 'B04',
                'y': 'B08',
                'xmax': 6000,
                'ymax': 6000,
                'cumulative': True,
                'color': 'red',
                'cumulative_color': 'blue'
            }
            is_scatter = True
    
        else:
            print(f"Unsupported calendar view option: {self.dd_plot_param.value}")
            return None
    
        parcel_id = normalize_parcel_id(self.id_dropdown.value)
    
        output_path = self.output_folder
        netcdf_path = self._get_netcdf_path(parcel_id)
    
        if not os.path.exists(netcdf_path):
            print("Extract the data first")
            return None
    
        cview_dir = os.path.join(output_path, 'cview')
        os.makedirs(cview_dir, exist_ok=True)
    
        if is_scatter:
            suffix = f"{sc_dict['x']}_{sc_dict['y']}_scatter"
        else:
            suffix = ''.join(bandlist)
    
        cview_filename = self._get_cview_pickle_path(parcel_id, suffix)
        cview_png = self._get_cview_png_path(parcel_id, suffix)
    
        if not os.path.exists(cview_filename):
            parcel = self.gdf[self.gdf[self.norm_id_column] == parcel_id]
    
            if parcel.empty:
                raise ValueError(f"No parcel found for normalized ID: {parcel_id}")
    
            with xr.open_dataset(netcdf_path) as ds:
                crs_wkt = ds["crs"].attrs.get("crs_wkt")
                if crs_wkt:
                    ds = ds.rio.write_crs(crs_wkt)
    
                print("Computing Calendar View - Please be patient")
                if is_scatter:
                    fig, ax = ngu.calendar_view_half_weekly_scatter(
                        ds,
                        parcel,
                        [self.norm_id_column],
                        out_tif_folder_base=cview_dir,
                        sc_dict=sc_dict
                    )
                else:
                    fig, ax = ngu.calendar_view_half_weekly(
                        ds,
                        parcel,
                        [self.norm_id_column],
                        bandlist,
                        out_tif_folder_base=cview_dir,
                        stretch_table=stretch_table
                    )
    
                fig.savefig(cview_png, dpi=100, bbox_inches='tight')
                with open(cview_filename, 'wb') as f:
                    pickle.dump(fig, f)
                print("Done!")
        else:
            with open(cview_filename, 'rb') as f:
                fig = pickle.load(f)
            ax = fig.axes
            if (fig is not None) and (not os.path.exists(cview_png)):
                fig.savefig(cview_png, dpi=100, bbox_inches='tight')
    
        return fig, ax


def getIntMap(dashboard):
    return MapAndPlotWidget(dashboard)
