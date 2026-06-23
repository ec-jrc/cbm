# Sentinel Parcel Viewer (SPV)

**Interactive parcel-level analysis of Sentinel-2 data on the Copernicus Data Space Ecosystem.**

The Sentinel Parcel Viewer (SPV) is a JupyterLab-based tool for **parcel-level analysis using Sentinel‑2 imagery**. It allows extraction of Sentinel‑2 data for user-defined parcels, run time-series analysis of spectral bands and vegetation indices, and explore results through interactive graphs and calendar views — all directly inside the Copernicus Data Space Ecosystem (CDSE), with data extraction handled by the [openEO](https://openeo.org/) backend.

---

## Features

- **Two ways to define areas of interest**
  - *Load an existing dataset* (GeoJSON/JSON, GeoPackage, KML, or a zipped ESRI shapefile).
  - *Draw polygons interactively* on a map (with OpenStreetMap or ESRI World Imagery basemaps).
- **Automated Sentinel‑2 extraction** through openEO, with a 50 m buffer around each parcel.
- **Large-area processing** — datasets are automatically tiled into sub‑areas below 50 × 50 km, with a built-in retry mechanism for failed jobs.
- **Caching** — identical extraction requests (same dataset + date range) are detected and skipped, reusing existing results.
- **Visualization**
  - *Stats summary*: per-band statistics (B02, B03, B04, B08, B11) and NDVI.
  - *Calendar view*: false color (NIR–SWIR–RED), RGB (Red–Green–Blue), scatter plots (e.g. B04–B08), and NDVI.
  - Click any parcel on the map to pop up its **NDVI time series**.
- **Input validation** for dataset quality and date ranges to catch problems early.

---

## How it works

1. The notebook bootstraps itself by downloading the required Python modules and installing dependencies.
2. It requires user authentication against the openEO federation endpoint of the Copernicus Data Space Ecosystem.
3. Through an interactive widget interface, define parcels and a date range.
4. SPV submits extraction jobs to openEO and downloads the results as **NetCDF** files (one set per dataset, containing all pixel values per parcel across the selected dates).
5. The visualization interface loads automatically so you can generate graphs and calendar views.

---

## Requirements

- An account on the **[Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/)** (free registration).
- Access to the **JupyterLab** environment provided by CDSE.
- A medium or large server instance is recommended for better performance.

Python dependencies (installed automatically by the notebook):

```
leafmap, ipywidgets, IPython, geopandas, ipyleaflet, numpy, tqdm,
pandas, xarray<2025.01.2, rioxarray, netcdf4, h5netcdf, openeo, rich
```

---

## Getting started

### 1. Environment setup

1. Log in to the Copernicus Data Space Ecosystem and open the **JupyterLab** environment.
2. Start a server instance (Medium or Large recommended).
3. In the `mystorage` directory, create a working folder (e.g. `spv`).
4. Upload the **`SPV.ipynb`** notebook into that folder (drag & drop, or use the upload button).
5. Open the notebook (double-click).

### 2. Initialization & authentication

1. **Run the first code cell.** It downloads the required modules and installs dependencies. Wait for:
   > *"Installs completed. You can now run the next cell to authenticate."*
2. **Run the authentication cell.**
   - If a valid session exists (sessions last ~30 days), you'll see *"Authenticated using refresh token."*
   - Otherwise, a URL is printed. Open it in your browser, log in, and grant access to **openEO**, then return to JupyterLab.
3. **Run the "Load interface" cell.** The interactive interface appears, offering two modes: *Load existing dataset* and *Draw polygons on map*.

---

## Usage

### Mode A — Load an existing dataset

1. **Select dataset** — a geospatial file in one of the supported formats (`.geojson`, `.json`, `.gpkg`, `.kml`, or `.zip` for ESRI shapefiles).
2. **Select start and end dates** — the temporal range for extraction.
3. **Select Parcel ID** — a column that uniquely identifies each parcel. (A unique ID field can be created in QGIS.)
4. **Click "Run"** to start extraction. Progress messages keep you informed (e.g. *"Processing subset 2/10"*).

If the area is very large, it is automatically split into sub-areas below 50 × 50 km to comply with the CDSE recommendation of keeping requests below 100 × 100 km. Failed jobs are retried automatically (up to 3 times, with a 60‑second delay); after three consecutive failures the job is considered failed.

On success, NetCDF files are generated and stored under `output/S2/`. If the same extraction is requested again later, SPV reuses the cached files and reports *"All NetCDF files already exist. Skipping job creation."*

### Mode B — Draw polygons on the map

1. Use the map navigation (zoom, pan) to find your area. Start on **OpenStreetMap**, then switch to **ESRI World Imagery** for precise boundary delineation.
2. **Draw a polygon**: activate the *Draw a polygon* tool, click to add vertices, and close it by double-clicking or clicking the first vertex again. Each polygon gets a unique label.
3. **Edit** polygons with the *Edit layers* tool (drag vertices, then *Save* or *Cancel*).
4. **Delete** polygons with the *Delete layers* tool, or *Clear all* to remove everything. (Identifiers are not reused after deletion.)
5. Select **start** and **end** dates and click **"Run process"**.

> Note: if you only change a polygon's geometry, the extraction is **not** re-run (so previous outputs can be reused). To force a new extraction after editing geometry, change the date range slightly (e.g. shift a date by one day).

### Visualization

Once NetCDF files are ready, the visualization interface loads automatically. From the dropdown menus, choose:

- the **parcel ID**,
- the **visualization type** — *Stats summary* or *Calendar view*,
- the specific **option**:
  - *Stats summary*: individual bands (B02, B03, B04, B08, B11) or NDVI.
  - *Calendar view*: false color (NIR–SWIR–RED), RGB (Red–Green–Blue), scatter plots (e.g. B04–B08), or NDVI.

Click **"Display"** to render the graph or calendar view below the interface. You can also **click directly on a parcel** in the map to see its NDVI time series as a popup.

---

## Input data requirements

When loading an existing dataset, the following checks are enforced:

**Format & structure**
- Supported formats only: GeoJSON/JSON, GeoPackage, KML, or a ZIP containing exactly one shapefile.
- GeoJSON must be valid UTF‑8, valid JSON, and a non-empty `FeatureCollection`.
- The file must be readable and contain at least one feature.
- A geometry field must be present; features with null/empty geometries are removed.
- Only **Polygon** and **MultiPolygon** geometries are accepted; invalid geometries (self-intersections, broken rings) are rejected.
- A defined **CRS** is required.

**Limits**
- Maximum **20,000** parcels per dataset.
- Maximum file size of **100 MB**.
- (Split larger datasets into smaller subsets.)

**Date range checks**
- Both start and end dates are required; the start date cannot be in the future; the end date cannot precede the start date.
- Warnings are shown for: start dates before the recommended minimum, future end dates, very large ranges (longer processing), very short ranges (little/no data), and end dates very close to today (newest acquisitions may not be available yet).

---

## Outputs

All outputs are saved under `output/S2/<dataset_name_hash>/`, where the hash encodes the extraction parameters so identical requests are not reprocessed. The folder is organized into subfolders:

| Folder | Contents |
|---|---|
| `band_stats` | CSV files with per-band statistics |
| `cview` | Calendar view images |
| `ndvi` | NDVI outputs |
| `plots` | Graph visualizations |

The raw NetCDF files (all pixel values per parcel across the selected dates, plus a 50 m buffer) are stored under `output/S2/`.

---

## Repository structure

| File | Purpose |
|---|---|
| `SPV.ipynb` | Main notebook — entry point. Bootstraps, authenticates, and loads the interface. |
| `bootstrap.py` | Downloads required modules and installs dependencies. |
| `openeo_utils.py` | Core logic: dataset loading/validation, openEO extraction, and the interactive widget interface. |
| `netcdf_utils.py` | NetCDF processing: masking (incl. SCL cloud masking), band statistics, and spectral indices (NDVI, ratios). |
| `ncdf_graph_utils.py` | Calendar-view rendering (RGB, false color, scatter) from NetCDF data. |
| `csv_graphs_utils.py` | Time-series / profile graphs from the generated CSV statistics. |
| `plot_utils.py` | Plotting helpers (date handling, band stretching, layout). |
| `requirements.txt` | Python dependencies. |
---

## Authors & credits

Developed by **Gilbert Voican, Mateusz Dobrychlop, and Daniele Borio**.

The notebook pulls its modules from the upstream repository: <https://github.com/ec-jrc/cbm>.

