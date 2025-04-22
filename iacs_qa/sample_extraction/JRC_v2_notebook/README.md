<div>
<img src="images/jrc_ec_logo.jpg" width="400"/>
</div>

# **QUASSA**
### IACS **QU**ality **AS**essment **SA**mple Extraction Tool

The code included in this notebook, developed by the JRC, implements the procedure for Member States to define their samples for the IACS quality assessment. This involves extracting parcels from the ranked list provided by the Commission, following the selection rules in the Union Level Methodology 2024 (Chapters 3 and 4). Member States have discretion over the sample sizes, within the constraints of the Methodology.

The tool takes the ranked list in CSV format and returns a list of parcels assigned to buckets representing different interventions.

Authors: Mateusz Dobrychłop (mateusz.dobrychlop@ext.ec.europa.eu), Fernando Fahl (fernando.fahl@ext.ec.europa.eu), Ferdinando Urbano (ferdinando.urbano@ec.europa.eu)

## Release notes

**Version 2 (Jupyter Notebook)**

---
**Latest update: April 22nd 2025** - (bug fix to v2.91)

* Fixed a bug related to the "Prioritize parcels covered by VHR images (beta)" parameter, where sometimes the parcels not covered by VHR images would not be extracted at all.

* Fixed an output file bug in the command-line version of the tool.


## Jupyter Notebook

The solution is written in Python, and made available in the form of a **Jupyter Notebook**. It is an interactive document that allows you to combine executable code, text, images, and visualizations all in one easily accessible place. Documentation can be found [here](https://docs.jupyter.org/en/latest/).

To open and use this notebook, you will need an environment that supports Jupyter Notebooks. Some recommended options to look into:
* Running the notebook in your web browser [(link)](https://docs.jupyter.org/en/latest/running.html)
* JupyterLab [(link)](https://jupyterlab.readthedocs.io/en/latest/)
* Visual Studio Code [(link)](https://code.visualstudio.com/download)

## No-notebook script

While QUASSA is primarily designed to be used within a Jupyter Notebook, an alternative command-line interface (CLI) mode is now available for users who prefer to run the tool as a standalone Python script. This mode allows for greater flexibility, particularly for automated workflows or batch processing scenarios where interactive execution is not required. It can also be used in case using a notebook is not possible for any reason.

**The script is currently in its beta-testing phase.**

### When to use the CLI version

The command-line version of QUASSA is ideal for:

* Running large-scale extractions without the need for an interactive environment.
* Automating repeated sample extractions.
* Integrating QUASSA into existing data pipelines.
* Running the tool on a remote server where Jupyter is not available.

By offering both a Jupyter Notebook interface and a CLI mode, QUASSA provides flexibility for users with varying technical preferences and workflow requirements.


### Running the script

The script version of QUASSA is executed using the run_outside_notebook.py script located in the same directory as the Jupyter Notebook version:

```python run_outside_notebook.py -h```

Running the above command will display a help message outlining the available command-line arguments.

### Command-Line arguments

The script requires a set of parameters to be provided through command-line arguments:

* ```--config CONFIG```: Path to an INI configuration file containing predefined settings.
* ```--parcel_file PARCEL_FILE```: Path to the parcel list CSV file.
* ```--target_file TARGET_FILE```: (Optional) Path to a CSV file specifying bucket target values.
* ```--3_percent 3_PERCENT```: (Optional) Boolean flag (true or false) to enable limiting the search to 3% of holdings.
* ```--covered_priority COVERED_PRIORITY```: (Optional) Mode for handling parcels covered by Very High-Resolution (VHR) imagery:
    * ```0```: Include all parcels.
    * ```1```: Prioritize covered parcels.
    * ```2```: Include only covered parcels.
* ```--noncontributing_filtering NONCONTRIBUTING_FILTERING```: (Optional) Defines how non-contributing, highest-ranked parcels are handled:
    * ```0```: Filter them out once the bucket is filled.
    * ```1```: Retain them.
* ```--extraction_id EXTRACTION_ID```: (Optional) Custom ID label for output files.

### Example execution

Below is an example command for running QUASSA outside the notebook with specific parameters:

```python run_outside_notebook.py --config config.ini --parcel_file parcels.csv --target_file targets.csv --3_percent true --covered_priority 1 --noncontributing_filtering 0 --extraction_id test_run```

This command executes the extraction process with:
* A predefined configuration file (config.ini).
* A parcel file (parcels.csv).
* A target file (targets.csv).
* The 3% holdings rule enabled.
* Prioritization of covered parcels.
* Filtering out non-contributing parcels once buckets are filled.
* An extraction ID (test_run).


## Planned features

* More statistics and visualizations after the extraction is completed
* More statistics describing the input parcel file right after it's loaded
* Further speed increase

## Release log
Using the latest version of QUASSA is strongly recommended. That said, all superseded versions of the tool are provided as zip packages in the [version_history](https://github.com/ec-jrc/cbm/tree/main/iacs_qa/sample_extraction/JRC_v2_notebook/version_history) directory.
---
**March 14th 2025** - v2.91
* Added a new output file – a parcel-centric list of extracted parcels, ordering the data by parcels to give the users a quick overview of the type and number of buckets each parcel was assigned to.
---
**February 28th 2025** - v2.9
* Default bucket target values are now set to values recommended by the new ULM (5% for lot size smaller than 6000 parcels; 300 for lot size larger than 6000 parcels).
* Added a script that runs QUASSA outside the notebook (beta version)
---
**December 9th 2024** - v2.8
* Fixed a bug that caused incorrect processing of parcel IDs that started with "0".
* Fixed a bug that caused crashing for input dasets where all parcels were not covered by VHR images. 
---
**September 6th 2024** - v2.7
* **Holding level intervention selection** - the target selection UI now allows for selecting Holding Level interventions. Selecting one or more Holding Level interventions results in creating an additional output file, with the summary of all holdings related to the Holding Level interventions.
* **Retain / filter out non-contributing parcels** - a new optional parameter that allows the user to decide if a highest-ranked parcel of a holding should be filtered out or retained, when all parcels of a recently completed bucket are filtered out from the parcel list.
* Summary output files - after every extraction a new file is included in the output. It's a simple text summary file listing the parameters used and some statistics calculated on the extracted dataset.
* Extraction ID - the user can now define a unique ID for each extraction. If a custom ID is not defined, the tool will automatically assign a randomized ID to simplify the distinction between output files generated for different extraction iterations.
* Increase all targets by x% - taking the place of the now deprecated target capping option - allows the user to automatically increase all bucket targets by a defined percentage
* Default target value definition - the default placeholder values for bucket targets are now calculated based on the algorithm described in the Union Level Methodology.
---
**June 25th 2024** - v2.6
* Selection of input files using a graphical file selector - as an alternative to providing a path, the user can now select the file in the file system using a new GUI feature.
* Some basic charts are now displayed describing the input data.
* New visualizations and stats were added to the final statistics frame after the extraction's completion.
* In case the parcel CSV file does not pass verification, a timestamped text file is saved listing all rows where issues occur.
* Covered parcel prioritization - bug fixes.
---
**June 12th 2024** - v2.5
* **Prioritize parcels covered by VHR images** - new feature, currently in its test phase. Aside from being able to only select the VHR-covered parcels in the extraction, the user can now prioritize covered parcels without completely disregarding the non-covered ones.
* Minor bug and typo fixes.
---
**May 27th 2024** - v2.4
* Major performance upgrade - between x2 and x100 speed increase, depending on input data and configuration.
* The 3% rule (limiting the number of selected holdings to 3% of the total number of holdings) now can be applied in the Optional Parameters section.
* User can now select if only HR image covered parcels should be taken into account, or if all of them should be considered.
* "Covered" column added to the output files.
* By default, the target values are now set to 5% of all interventions available in the input data for a given bucket, but not more than 300.
* After completing the sampling process, a summary with additional insights and statistics can be generated by executing the code cell in the Final statistics section at the bottom of the motebook.
---
**May 16th 2024** - v2.3
* Fixed UI elements to adjust for potentially long UA group IDs
* Allowed Parcel IDs to be integers, as per Paolo's suggestion
---
**May 13th 2024** - v2.2
* Directory structure changed, to clearly separate the Notebook version from older releases
* Readme added to the Notebook subfolder, mirroring to a large extent the text included in the notebook itself
* Some small GUI and documentation fixes
* Some optimization developments
---
**May 6th 2024** - v2.1
* Slight speed increase
---
**April 30th 2024** - v2.0
* Release of the new Notebook version of the Sample Extraction Tool
---


