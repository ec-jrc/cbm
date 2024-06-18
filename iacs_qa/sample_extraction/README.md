Member States must define their samples for the ICAS quality assessment (one for each unit group) by extracting parcels from the ranked list provided by the Commission. The rules for selecting the parcels are provided in the Union Level Methodology 2024 (Chapter 3 and 4). Sample sizes remain at the discretion of Member States, within the constraints imposed by the Methodology.  
In this section you can find the code developed by the JRC and some Member States to implement this procedure (see subfolders for versions shared by each contributor). 
The JRC tool is called **QUality ASsessment SAmple extraction tool (QUASSA)**. We try to develop the tool with new versions that improve the graphical interface, usability and available options and reduce computation time. All versions implement the same algorithm so they must give the same results (if the same option setting is used).
The use of QUASSA is not compulsory. The JRC makes it available for Member States that want to use it voluntarily for sample extraction or to verify that samples generated with other tools are consistent with the QUASSA results.

In the figure below, there is a sketch illustrating the workflow to implement the rules for sample extraction without the "maximum 3% of holdings" rule (click to view it in full resolution).  

<img src="https://github.com/ec-jrc/cbm/blob/main/iacs_qa/sample_extraction/workflow_selection.png" width="420" height="613">  

This is the workflow when the "maximum 3% of holdings" rule is applied (click to view it in full resolution).  

<img src="https://github.com/ec-jrc/cbm/blob/main/iacs_qa/sample_extraction/workflow_selection_3perc.png" width="565" height="620">
