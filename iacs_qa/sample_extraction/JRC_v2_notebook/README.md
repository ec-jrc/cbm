# IACS QA Sample Extraction
<div>
<img src="images/jrc_ec_logo.jpg" width="400"/>
</div>

The code included in this notebook, developed by the JRC, implements the procedure for Member States to define their samples for the IACS quality assessment. This involves extracting parcels from the ranked list provided by the Commission, following the selection rules in the Union Level Methodology 2024 (Chapters 3 and 4). Member States have discretion over the sample sizes, within the constraints of the Methodology.

The tool takes the ranked list in CSV format and returns a list of parcels assigned to buckets representing different interventions.

Authors: Mateusz Dobrychłop (mateusz.dobrychlop@ext.ec.europa.eu), Fernando Fahl (fernando.fahl@ext.ec.europa.eu), Ferdinando Urbano (ferdinando.urbano@ec.europa.eu)

## Release notes

**Version 2 (Jupyter Notebook)**

---
**Latest update: May 28th**
* Major performance upgrade - between x2 and x100 speed increase, depending on input data and configuration.
* The **3% rule** (limiting the number of selected holdings to 3% of the total number of holdings) now can be applied in the **Optional Parameters** section.
* User can now select if only HR image covered parcels should be taken into account, or if all of them should be considered.
* "Covered" column added to the output files.
* By default, the target values are now set to 5% of all interventions available in the input data for a given bucket, but not more than 300.

**Please note**: To achieve the significant performance improvements in this version, we have made minor adjustments to the algorithm. As a result, the output may differ slightly from previous versions. This is due to the data filtering that now happens at certain stages of the procedure. Because we now eliminate some interventions that can't contribute to any buckets, some interventions lower in the ranking can potentially not be picked now, even if they were picked in the previous version.

---

The solution is still in its beta testing phase. Implementation of some of the expected features and general optimization is planned for the upcoming weeks.

The following developments are planned for the near future:

* Prioritization of covered parcels (but without completely excluding non-covered parcels)

* Some more flexibility regarding the output will soon be introduced. We are also working on making the output more informative.

* In the upcoming updates, a lot of emphasis will still be placed on speed improvements.

## Jupyter Notebook

The solution is written in Python, and made available in the form of a **Jupyter Notebook**. It is an interactive document that allows you to combine executable code, text, images, and visualizations all in one easily accessible place. Documentation can be found [here](https://docs.jupyter.org/en/latest/).

To open and use this notebook, you will need an environment that supports Jupyter Notebooks. Some recommended options to look into:
* Running the notebook in your web browser [(link)](https://docs.jupyter.org/en/latest/running.html)
* JupyterLab [(link)](https://jupyterlab.readthedocs.io/en/latest/)
* Visual Studio Code [(link)](https://code.visualstudio.com/download)
