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
**Latest update: September 6th** - v2.7
* **Holding level intervention selection** - the target selection UI now allows for selecting Holding Level interventions. Selecting one or more Holding Level interventions results in creating an additional output file, with the summary of all holdings related to the Holding Level interventions.
* **Retain / filter out non-contributing parcels** - a new optional parameter that allows the user to decide if a highest-ranked parcel of a holding should be filtered out or retained, when all parcels of a recently completed bucket are filtered out from the parcel list.
* Summary output files - after every extraction a new file is included in the output. It's a simple text summary file listing the parameters used and some statistics calculated on the extracted dataset.
* Extraction ID - the user can now define a unique ID for each extraction. If a custom ID is not defined, the tool will automatically assign a randomized ID to simplify the distinction between output files generated for different extraction iterations.
* Increase all targets by x% - taking the place of the now deprecated target capping option - allows the user to automatically increase all bucket targets by a defined percentage
* Default target value definition - the default placeholder values for bucket targets are now calculated based on the algorithm described in the Union Level Methodology.

## Jupyter Notebook

The solution is written in Python, and made available in the form of a **Jupyter Notebook**. It is an interactive document that allows you to combine executable code, text, images, and visualizations all in one easily accessible place. Documentation can be found [here](https://docs.jupyter.org/en/latest/).

To open and use this notebook, you will need an environment that supports Jupyter Notebooks. Some recommended options to look into:
* Running the notebook in your web browser [(link)](https://docs.jupyter.org/en/latest/running.html)
* JupyterLab [(link)](https://jupyterlab.readthedocs.io/en/latest/)
* Visual Studio Code [(link)](https://code.visualstudio.com/download)

## Planned features

* More statistics and visualizations after the extraction is completed
* More statistics describing the input parcel file right after it's loaded
* Further speed increase

## Release log
Using the latest version of QUASSA is strongly recommended. That said, all superseded versions of the tool are provided as zip packages in the [version_history](https://github.com/ec-jrc/cbm/tree/main/iacs_qa/sample_extraction/JRC_v2_notebook/version_history) directory.
---
**September 6th** - v2.7
* **Holding level intervention selection** - the target selection UI now allows for selecting Holding Level interventions. Selecting one or more Holding Level interventions results in creating an additional output file, with the summary of all holdings related to the Holding Level interventions.
* **Retain / filter out non-contributing parcels** - a new optional parameter that allows the user to decide if a highest-ranked parcel of a holding should be filtered out or retained, when all parcels of a recently completed bucket are filtered out from the parcel list.
* Summary output files - after every extraction a new file is included in the output. It's a simple text summary file listing the parameters used and some statistics calculated on the extracted dataset.
* Extraction ID - the user can now define a unique ID for each extraction. If a custom ID is not defined, the tool will automatically assign a randomized ID to simplify the distinction between output files generated for different extraction iterations.
* Increase all targets by x% - taking the place of the now deprecated target capping option - allows the user to automatically increase all bucket targets by a defined percentage
* Default target value definition - the default placeholder values for bucket targets are now calculated based on the algorithm described in the Union Level Methodology.
---
**June 25th** - v2.6
* Selection of input files using a graphical file selector - as an alternative to providing a path, the user can now select the file in the file system using a new GUI feature.
* Some basic charts are now displayed describing the input data.
* New visualizations and stats were added to the final statistics frame after the extraction's completion.
* In case the parcel CSV file does not pass verification, a timestamped text file is saved listing all rows where issues occur.
* Covered parcel prioritization - bug fixes.
---
**June 12th** - v2.5
* **Prioritize parcels covered by VHR images** - new feature, currently in its test phase. Aside from being able to only select the VHR-covered parcels in the extraction, the user can now prioritize covered parcels without completely disregarding the non-covered ones.
* Minor bug and typo fixes.
---
**May 27th** - v2.4
* Major performance upgrade - between x2 and x100 speed increase, depending on input data and configuration.
* The 3% rule (limiting the number of selected holdings to 3% of the total number of holdings) now can be applied in the Optional Parameters section.
* User can now select if only HR image covered parcels should be taken into account, or if all of them should be considered.
* "Covered" column added to the output files.
* By default, the target values are now set to 5% of all interventions available in the input data for a given bucket, but not more than 300.
* After completing the sampling process, a summary with additional insights and statistics can be generated by executing the code cell in the Final statistics section at the bottom of the motebook.
---
**May 16th** - v2.3
* Fixed UI elements to adjust for potentially long UA group IDs
* Allowed Parcel IDs to be integers, as per Paolo's suggestion
---
**May 13th** - v2.2
* Directory structure changed, to clearly separate the Notebook version from older releases
* Readme added to the Notebook subfolder, mirroring to a large extent the text included in the notebook itself
* Some small GUI and documentation fixes
* Some optimization developments
---
**May 6th** - v2.1
* Slight speed increase
---
**April 30th** - v2.0
* Release of the new Notebook version of the Sample Extraction Tool
---


