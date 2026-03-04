# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 09:41:40 2026

@authors: Gilbert Voican, Mateusz Dobrychlop and Daniele Borio
"""
#%% Import Libraries
import geopandas as gpd
from shapely.geometry import box
import os
import shutil
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import time
import datetime as dt

import leafmap
from ipyleaflet import Popup

import xarray as xr
import base64

import io
from IPython.display import clear_output

from openeo.extra.spectral_indices.spectral_indices import append_indices

import ipywidgets as widgets
from ipywidgets import HTML 

#%% Custom libraries
import netcdf_utils as nu
import csv_graphs_utils as cgu
import ncdf_graph_utils as ngu


#%% support functions
def split_extent(gdf : gpd.GeoDataFrame, max_size : int = 10000) -> list :
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

def download_netcdf(polygons_gdf : gpd.GeoDataFrame, output_folder : str, id_column : str, \
                    start_date : str, end_date : str, connection ) :
    """
    Function that downloads the netcdf files through the openEO API

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

    parcel_ids = polygons_gdf[id_column].astype(str).tolist()

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
    
    
    #I removed this code in order to implement the check if the job already run and all the output file are present
    # Remove all previous files to avoid conflicts
    #if os.path.exists(output_folder) :
    #    shutil.rmtree(output_folder)
        
        # Create the folder
    #    os.makedirs(output_folder)#, exist_ok=True)

    #information for file naming
    filename_prefix = f"S2_extract_{start_date}_{end_date}_parcelid"
    
    # list of bands to be extracted
    # bands = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12", "SCL"]
    bands = ["B02", "B03", "B04", "B08", "B11", "SCL"]
    
    s2_bands = connection.load_collection(
        "SENTINEL2_L2A",
        temporal_extent=[start_date, end_date],
        spatial_extent=get_spatial_extent(gdf_extent),
        bands=bands,
        max_cloud_cover=50
    )
    
    #cloud masking
    scl = s2_bands.band("SCL")
    # cloud_mask = (scl == 0) | (scl == 1)
    cloud_mask = (scl == 0) | (scl == 1) | (scl == 3) | (scl == 8) | (scl == 9) | (scl == 11)
    
    cloud_mask = cloud_mask.resample_cube_spatial(s2_bands)
    s2_bands_masked = s2_bands.mask(cloud_mask)

    #loading the dataset o json - for the spatial filter
    features = json.loads(gdf_extent.to_crs("EPSG:4326").to_json())

    #spatial filter - using only the pixels intersecting the polygons
    s2_bands_masked = s2_bands.filter_spatial(features)

    #adding NDVI index
    indices = append_indices(s2_bands_masked,
                             indices=["NDVI"],
                             platform="SENTINEL2")
    
    #creating the job for server execution 
    job = indices.create_job(
        title="S2 bands and NDVI",
        description="Sentinel-2 L2A bands and NDVI",
        out_format="netCDF",
        filename_prefix=filename_prefix, 
        feature_id_property=id_column,
        sample_by_feature=True,
    )
    
    #excuting the job and saving the results as NetCDF

    from rich.console import Console
    console = Console(force_jupyter=True)

    last_message = {"value": None}
    
    with console.status("Submitting job...", spinner="dots") as status:     
        def custom_print(raw_message):
            #clear_output(wait=True)

            # openeo status structure:
            # "{elapsed_time} Job {job_id}: {message}"
            elapsed_time = raw_message.split()[0]
            job_id = raw_message.split()[2].replace(":","")
    
            if "start" in raw_message:
                message = f"🚀 Job submitted and starting. ID: {job_id}."
            elif "created" in raw_message:
                message = f"🚀 Job created. ID: {job_id}."
            elif "queued" in raw_message:
                message = f"⏳ [{elapsed_time}] Job (ID: {job_id}) is waiting in the queue. Please wait."
            elif "running" in raw_message:
                message = f"⚙️ [{elapsed_time}] Job (ID: {job_id}) is now running. Please wait."
            elif "finished" in raw_message:
                message = f"✅ [{elapsed_time}] Job (ID: {job_id}) has succesfully finished. You can now run the next cell."
            else:
                message = raw_message

            last_message["value"] = message
            status.update(message)

        job.start_and_wait(print=custom_print)

    print(last_message["value"])

    job.get_results().download_files(output_folder)

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
            title=title,
            description="Sentinel-2 L2A bands and indices",
            out_format="netCDF",
            filename_prefix=filename_prefix, 
            feature_id_property=id_column,
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
    
    
class OpenEODashboard(widgets.VBox):
    """
    Class incapsulating the different functionalities for downloading Sentinel-2
    data
    """
    def __init__(self, connection):
        
        super().__init__()
        
        # 1. Store Members (The "State")
        self.connection = connection
        self.gdf = None
        self.job_results = None

        # 2. Initialize UI Components
        self.uploader = widgets.FileUpload(
            accept='.geojson', 
            multiple=False, 
            description="Select GeoJSON",
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
        self.run_button.disabled = not (self._ok_upload and self._ok_id and self._ok_dates)

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

        if not filename.lower().endswith(".geojson"):
            raise ValueError("❌ Invalid file format. Please upload a .geojson file.")

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
    
    def _load_and_validate_gdf(self, content: bytes) -> gpd.GeoDataFrame:
        """Load with GeoPandas + minimal geometry/CRS sanity checks."""
        try:
            gdf = gpd.read_file(io.BytesIO(content))
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

            try:
                filename, content = self._read_upload_bytes()

                # parse + basic structure checks (you don’t use obj yet, but it’s still a good early gate)
                _ = self._validate_geojson_text(content)

                # load + gdf checks
                gdf = self._load_and_validate_gdf(content)

                self.gdf = gdf

                # Populate ID dropdown (no validation yet)
                columns = [c for c in self.gdf.columns if c != "geometry"]
                if len(columns) == 0:
                    raise ValueError("❌ No attribute columns found (need at least one non-geometry column for Parcel ID).")

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
            
            # Arbitrary date selected for now
            MIN_DATE = self.min_date
            if s < MIN_DATE:
                print(f"⚠️ Very early start date; Data availability may be limited.")
                self._update_run_button()
                return
        
        # Validate end date manages the relationship between start and end date
        # therefore we run it when the start date is changed
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

            if e > today:
                self._ok_dates = False
                print(f"❌ End date ({e}) cannot be in the future.")
                self._update_run_button()
                return

            if e < s:
                self._ok_dates = False
                print(f"❌ End date ({e}) cannot be earlier than Start date ({s}).")
                self._update_run_button()
                return

            # Range warnings
            # Arbitrary ranges selected for now
            span = (e - s).days

            MAX_SPAN_DAYS = self.max_date_span_years * 365
            MIN_SPAN_DAYS = self.min_date_span_days
            RECENT_THRESHOLD_DAYS = self.recent_date_threshold_days
            
            if span > MAX_SPAN_DAYS:
                print(f"⚠️ Large date range ({span} days); Processing may take longer.")
            if span < MIN_SPAN_DAYS:
                print(f"⚠️ Very short date range ({span} days); Data availability may be limited.")
            if (today - e).days < RECENT_THRESHOLD_DAYS:
                print(f"⚠️ Recent end date; Data availability may be limited.")
            
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
    
                # Build the output folder
                fname = filename.split("/")[-1].split(".")[0]
                output_folder = f"output/S2/{fname}"
                
                # Format dates to string
                start_str = self.start_date.value.strftime('%Y-%m-%d')
                end_str = self.end_date.value.strftime('%Y-%m-%d')
    
                # Recover the parcel ID
                id_column = self.col_dropdown.value
                
                print(f"🗺️ Processing file: {filename}...")
                
                # Call your external function
                # Ensure your function signature is: process_data(gdf, filename, start_date, end_date)
                download_netcdf(self.gdf, output_folder, id_column, start_str, end_str, self.connection)
                
            except Exception as e:
                print(f"❌ Processing Error: {e}")

def getInterface(connection):
    return OpenEODashboard(connection)

#%% Map and plot widget
class MapAndPlotWidget(widgets.VBox):
    """
    Class containing the map and the interfaces for plotting specialized plots
    """
    def __init__(self, openDashboard):
        super().__init__() # Initialize the parent VBox
        
        # Member objects
        self.m = leafmap.Map(center=[0, 0], zoom=2)
        self.gdf = openDashboard.gdf
        self.id_column = openDashboard.col_dropdown.value

        self.output_log = widgets.Output()
        self.base_folder = "output/S2"

        # Prefix & File Info
        start_date = openDashboard.start_date.value.strftime('%Y-%m-%d')
        end_date = openDashboard.end_date.value.strftime('%Y-%m-%d')
        self.netcdf_prefix = f"S2_extract_{start_date}_{end_date}_parcelid_"
        
        file_info = openDashboard.uploader.value[0]
        self.filename = file_info['name']

        self._id_ok = True
        self._plot_type_ok = False
        self._plot_options_ok = False
        
        # ID dropdown setup
        unique_vals = sorted(self.gdf[self.id_column].unique().tolist())
        self.id_dropdown = widgets.Dropdown(
            description="Parcel ID:", 
            options=unique_vals,
            style={'description_width': 'initial'}
        )
        
        # Plot type and options setup
        # Define the data mapping for the dropdowns
        self.plot_options = {
            'stat summary': [],
            'imagettes': ['NIR-SWIR-RED', 'RED-GREEN-BLUE']
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
        self.children = [self.m, 
                         widgets.HBox([self.id_dropdown, 
                                       self.dd_plot_type,
                                       self.dd_plot_param, 
                                       self.btn_display]), 
                         self.output_log]
        
        # Bind Events
        self.id_dropdown.observe(self._on_id_change, names='value')
        self.dd_plot_type.observe(self._on_plot_type_change, names='value')
        self.dd_plot_param.observe(self._on_plot_param_change, names='value')
        self.btn_display.on_click(self._on_display_button_clicked)

        
        self._update_display_button()

        # Initialize map layers
        self._on_start()

    def _update_display_button(self):
        """Only update the Display button when all required selections are made."""
        self.btn_display.disabled = not (self._id_ok and self._plot_type_ok and self._plot_options_ok)

    def _on_id_change(self, change):
        """Zoom the map when dropdown value changes"""
        selected_val = change['new']
        self._id_ok = selected_val is not None

        if selected_val is not None and self.gdf is not None:
            subset = self.gdf[self.gdf[self.id_column] == selected_val]
            if not subset.empty:
                self.m.zoom_to_gdf(subset)

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
    
            folder_name = os.path.splitext(self.filename)[0]
            output_path = os.path.join(self.base_folder, folder_name)
            netcdf_path = os.path.join(output_path, f"{self.netcdf_prefix}{parcel_id}.nc")
                
            # check if the csv with the summary statistics is available
            if not os.path.exists(netcdf_path) :
                print('Extract the data first')
                return
    
            # if here, the netcdf file is available. Check if the parcel statistics have been already extracted
            #stat_dir = output_path + 'band_stats'
            stat_dir = os.path.join(output_path, 'band_stats')
            
            if not os.path.exists(stat_dir) :
                os.makedirs(stat_dir)
    
            csv_filename = stat_dir + '/' + str(parcel_id) + '_stats.csv'
            if not os.path.exists(csv_filename) :
                # Compute the band statistics
    
                parcel = self.gdf[self.gdf[self.id_column] == parcel_id]
         
                with xr.open_dataset(netcdf_path) as ds:
                    # assign the crs
                    crs_wkt = ds["crs"].attrs.get("crs_wkt")
                    ds = ds.rio.write_crs(crs_wkt)    
        
                    nu.ds_statistics_to_parcel_csv(ds, parcel, parcel_id, out_dir = stat_dir,\
                                                   scl_list = [0, 1, 3, 8, 9, 11])
    
            # Read the csv as dataframe
            stat_f = pd.read_csv(csv_filename)
    
            # Determine the bands available
            bands = np.unique(stat_f['band'])
    
            self.dd_plot_param.options = bands
        
        elif plot_type == 'imagettes': 
            self.dd_plot_param.options = ['NIR-SWIR-RED', 'RED-GREEN-BLUE']

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
    
            elif selected_type == 'imagettes':
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

    def _on_start(self):
        """Initialize map layers and interactions"""
        with self.output_log:
            self.gdf = self.gdf.to_crs(epsg=4326)

            style = {'fillOpacity': 0.3, 'weight': 1, 'color': '#3388ff'}
            hover_style = {'fillOpacity': 0.6, 'color': 'red'}

            old_layer = self.m.find_layer("Parcels")
            if old_layer:
                self.m.remove_layer(old_layer)
             
            self.m.add_geojson(
                self.gdf.__geo_interface__, 
                layer_name="Parcels",
                style=style,
                hover_style=hover_style
            )
                 
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
            parcel_id = props.get(self.id_column)
            
            if parcel_id is None:
                return

            # 1. Update Dropdown (triggers on_value_change zoom)
            #self.id_dropdown.value = parcel_id
            self._set_dropdown_silently(parcel_id)
                 
            # 2. Path Logic
            folder_name = os.path.splitext(self.filename)[0]
            output_path = os.path.join(self.base_folder, folder_name)
            netcdf_path = os.path.join(output_path, f"{self.netcdf_prefix}{parcel_id}.nc")
             
            if os.path.exists(netcdf_path):
                stat_dir = os.path.join(output_path, 'band_stats')
                if not os.path.exists(stat_dir):
                    os.makedirs(stat_dir)
     
                csv_filename = os.path.join(stat_dir, f"{parcel_id}_stats.csv")
                
                # Compute stats if CSV doesn't exist
                if not os.path.exists(csv_filename):
                    parcel = self.gdf[self.gdf[self.id_column] == parcel_id]
                    with xr.open_dataset(netcdf_path) as ds:
                        # Handle CRS
                        crs_wkt = ds["crs"].attrs.get("crs_wkt")
                        if crs_wkt:
                            ds = ds.rio.write_crs(crs_wkt)
                  
                        nu.ds_statistics_to_parcel_csv(ds, parcel, parcel_id, out_dir=stat_dir,
                                                       scl_list=[0, 1, 3, 8, 9, 11])
     
                # Handle NDVI Plotting
                ndvi_dir = os.path.join(output_path, 'ndvi')
                if not os.path.exists(ndvi_dir):
                    os.makedirs(ndvi_dir)
     
                ndvi_image_path = os.path.join(ndvi_dir, f"{parcel_id}_NDVI.png")
                if not os.path.exists(ndvi_image_path):
                    cgu.plot_csv_parcel(csv_filename, output_folder=ndvi_dir, band_to_plot="NDVI")
                
                # Prepare HTML for Popup
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

            # 3. Create and Show Popup
            # Remove previous popups to keep map clean
            for layer in list(self.m.layers):
                if isinstance(layer, Popup):
                    self.m.remove_layer(layer)
            
            popup = Popup(
                location=kwargs.get("coordinates"),
                child=HTML(value=html_content),
                close_button=True,
                max_width=550,
                auto_pan=True,                 # pan only (no zoom) to keep popup visible
                auto_pan_padding=(20, 20),     # keep it away from edges so close button is accessible
            )
            self.m.add_layer(popup)


    def get_line_plot(self):
        """ 
        Function to generate the line plot
        """
        if self.dd_plot_param.value == None :
            return None
    
        parcel_id = self.id_dropdown.value
        
        folder_name = os.path.splitext(self.filename)[0]
        output_path = os.path.join(self.base_folder, folder_name)
        netcdf_path = os.path.join(output_path, f"{self.netcdf_prefix}{parcel_id}.nc")

        # check if the netcdf file is available
        if not os.path.exists(netcdf_path) :
            print('Extract the data first')
            return None
    
        # if here, the netcdf file is available. Check if the parcel statistics have been already extracted
        stat_dir = os.path.join(output_path, 'band_stats')
        #stat_dir = output_path + 'band_stats'
        
        if not os.path.exists(stat_dir) :
            os.makedirs(stat_dir)
    
        csv_filename = stat_dir + '/' + str(parcel_id) + '_stats.csv'
        if not os.path.exists(csv_filename) :
            # Compute the band statistics
    
            parcel = self.gdf[self.gdf[self.id_column] == parcel_id]
     
            with xr.open_dataset(netcdf_path) as ds:
                # assign the crs
                crs_wkt = ds["crs"].attrs.get("crs_wkt")
                ds = ds.rio.write_crs(crs_wkt)    
        
                nu.ds_statistics_to_parcel_csv(ds, parcel, parcel_id, out_dir = stat_dir,\
                                               scl_list = [0, 1, 3, 8, 9, 11])
    
        # Read the csv as dataframe
        fig, ax = cgu.plot_csv_parcel(csv_filename, band_to_plot = self.dd_plot_param.value, to_file = False)
    
        return fig, ax

    def get_calendar_view(self, stretch_table = None) :
        """ 
        Function to generate the calendar view with the imagettes
        """
        if self.dd_plot_param.value == None :
            return None

        if self.dd_plot_param.value == 'NIR-SWIR-RED' :
            stretch_table =  {'B08' : [1200, 5700],
                                'B11' : [800, 4100],
                                'B04' : [150, 2800]}

        if self.dd_plot_param.value == 'RED-GREEN-BLUE' :
    
            stretch_table = {'B04' : [0, 1500],
                             'B03' : [0, 1500],
                             'B02' : [0, 1500]
                            }
        # Other stretching tables could be defined depending on the specified composition
        
        # Check if the netcdf exists
        parcel_id = self.id_dropdown.value
        
        folder_name = os.path.splitext(self.filename)[0]
        output_path = os.path.join(self.base_folder, folder_name)
        netcdf_path = os.path.join(output_path, f"{self.netcdf_prefix}{parcel_id}.nc")
    
        # check if the netcdf file is available
        if not os.path.exists(netcdf_path) :
            print('Extract the data first')
            return None
    
        # Check if the figure was already generated
        cview_dir = os.path.join(output_path, 'cview')
        #cview_dir = output_path + 'cview'
        
        if not os.path.exists(cview_dir) :
            os.makedirs(cview_dir)
    
        bandlist = list(stretch_table.keys())
        cview_filename = cview_dir + '/' + str(parcel_id) + '_' + "".join(bandlist) + '.pickle'
    
        if not os.path.exists(cview_filename) :
            
            parcel = self.gdf[self.gdf[self.id_column] == parcel_id]
     
            with xr.open_dataset(netcdf_path) as ds:
    
                # assign the crs
                crs_wkt = ds["crs"].attrs.get("crs_wkt")
                ds = ds.rio.write_crs(crs_wkt)    
        
                print('Computing Calendar View - Be patient')
                '''

                def calendar_view_half_weekly(ds, parcel = None, name_cols = None, band_list = None, \
                              out_tif_folder_base = "./", 
                              stretch_table = None, buffer_size_meter = 50, \
                              vector_color = "black", image_resolution = 100 ) 
                '''
                
                # Now make the calendar view
                fig, ax = ngu.calendar_view_half_weekly(ds, parcel, [self.id_column], bandlist, out_tif_folder_base = cview_dir, stretch_table = stretch_table)
                print('Done!')
            
        else :
            # If it exists, it can be laoded from file
            with open(cview_filename, 'rb') as f:
                fig = pickle.load(f)
    
            ax = fig.axes
        
        return fig, ax

    

def getIntMap(dashboard):
    return MapAndPlotWidget(dashboard)

    