import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import pandas as pd

# TODO still:
# - text descriptions / instructions (me to write, ferdi to verify?)
# - input file format verification
# - 3% config (algorithm)
# - indicator if value loaded, manually modified, or limited by threshold


PARAMETERS = {"parcels_path": "",
              "targets_path": "",
              "ua_group_thresholds": {v:0 for v in range(1, 23)}
              }

style_html = """
<style>
    .info-button-style {
        border-radius: 50%;  /* Makes the button circular */
    }
    .info-button-style:hover {
        box-shadow: none !important;  /* Removes shadow on hover */
        transform: none !important;  /* Stops any popping or scaling */
        cursor: default;  /* Removes the hand cursor */
    }
</style>
"""
display(HTML(style_html))

def verify_parcel_df(parcel_df):
    pass

def verify_target_df(target_df):
    pass

def display_parcel_input_config():
    """
    Display the widgets for configuring the input parcel file path.
    """

    def load_file(b, entry_widget, button_widget):
        file_path = entry_widget.value

        try:
            df = pd.read_csv(file_path)
            with output_area:
                clear_output()
                print("File loaded successfully. Preview: \n")
                print(df.head())
            valid_parcels_widget.value = True
            valid_parcels_widget.layout.display = ""
            PARAMETERS["parcels_path"] = file_path

        except Exception as e:
            with output_area:
                clear_output()
                print(f"Error loading file: {e}\n")
                print("Correct the path or file format and load again.")
            valid_parcels_widget.value = False
            valid_parcels_widget.layout.display = ""
            PARAMETERS["parcels_path"] = ""

    parcel_info_button = widgets.Button(
        icon="info",
        layout = widgets.Layout(width="30px"),
        #style={"button_color": "white"}
        button_style = "",
        tooltip="""The main input for the sample extraction process is a CSV file containing the parcel data.
The file should follow the format described in the text cell above.
The file path should be provided in the field to the right. Click the "Load" button to validate and load the file.
In case the validation or loading fails, an error message will be displayed below the file path field.
In that case you'll be able to provide a corrected path or correct your file and try again."""
    )

    parcel_info_button.add_class("info-button-style")

    parcel_file_path_entry = widgets.Combobox(
        placeholder="example: input/parcels.csv",
        description="Parcel file path:",
        ensure_option=False,
        disabled=False,
        style={"description_width": "initial"},
        layout = widgets.Layout(width="500px")
    )

    parcel_file_load_button = widgets.Button(
        description="Load",
        button_style="info",
        tooltip="Click to load parcel file",
        style={"button_color": "#1daee3ff"}
    )

    valid_parcels_widget = widgets.Valid(
    value=True,
    description="",
    layout=widgets.Layout(display="none")
    )

    output_area = widgets.Output()

    parcel_file_load_button.on_click(lambda b: load_file(b, parcel_file_path_entry, parcel_file_load_button))

    hbox = widgets.HBox([parcel_info_button, parcel_file_path_entry, parcel_file_load_button, valid_parcels_widget])
    vbox = widgets.VBox([hbox, output_area])
    display(vbox)



def display_bucket_targets_config():
    
    target_info_button = widgets.Button(
        icon="info",
        layout = widgets.Layout(width="30px"),
        #style={"button_color": "white"}
        button_style = "",
        tooltip="""You can either provide the target values manually using the fields below, or load the values from a CSV file.
In order to load the file, use the "Bucket targets file path" field to provide the path to the CSV file and click "Load".
Values loaded from a file can also be edited manually after loading.
In addition, you can set a maximum threshold value that will reduce the value for all the targets above the defined threhsold."""
    )

    target_info_button.add_class("info-button-style")

    target_file_path_entry = widgets.Combobox(
        placeholder="example: input/targets.csv",
        description="Bucket targets file path:",
        #width = "400px",
        ensure_option=False,
        disabled=False,
        style={"description_width": "initial"},
        layout = widgets.Layout(width="500px")
    )

    target_file_load_button = widgets.Button(
        description="Load",
        button_style="info",
        tooltip="Click to pre-populate target values",
        style={"button_color": "#1daee3ff"}
    )

    valid_targets_widget = widgets.Valid(
    value=True,
    description="",
    layout=widgets.Layout(display="none")
    )

    # group name / id mapping
    ua_groups = {   "YFS": 1, 
                    "SFS": 2, 
                    "ME2": 3, 
                    "ES2": 4, 
                    "ES1": 5, 
                    "E7B": 6, 
                    "E7A": 7, 
                    "E5": 8, 
                    "E4": 9, 
                    "E3": 10, 
                    "E2": 11, 
                    "E1C": 12, 
                    "CIS: LA": 13, 
                    "???" : 14, 
                    "C6C": 15, 
                    "C5": 16, 
                    "C4": 17, 
                    "C3": 18, 
                    "C2B": 19, 
                    "C1": 20, 
                    "BIS": 21, 
                    "ANC": 22}

    # Create widgets for each dictionary entry
    widgets_list = []
    for key, value in ua_groups.items():
        label = f"{key} (id: {value})"
        entry = widgets.BoundedIntText(value=0, 
                                       min=0, 
                                       max=99999999999999, 
                                       description=label, 
                                       layout=widgets.Layout(width="150px"),
                                       style={"description_width": "initial"},
                                       )
        widgets_list.append(entry)



    target_cutoff_info_button = widgets.Button(
        icon="info",
        layout = widgets.Layout(width="30px"),
        #style={"button_color": "white"}
        button_style = "",
        tooltip="""Provide a maximum target threshold independent from the values loaded above.
If any of the target values is above this threshold, it will be reduced to the threshold value."""
    )

    target_cutoff_info_button.add_class("info-button-style")

    target_cutoff_entry = widgets.BoundedIntText(value=0, 
                                       min=0, 
                                       max=99999999999999, 
                                       description="Target cutoff:", 
                                       layout=widgets.Layout(width="150px"),
                                       style={"description_width": "initial"},
                                       )

    target_cutoff_recalculate_button = widgets.Button(
        description="Recalculate targets",
        button_style="info",
        tooltip="Click to recalculate target values based on the target cutoff.",
        style={"button_color": "#1daee3ff"}
    )

    output_area = widgets.Output()

    def populate_target_values(target_df, widgets_list):
        for index, row in target_df.iterrows():
            ua_group = row["ua_grp_id"]
            target = row["target1"]
            if ua_group in ua_groups.values():
                widgets_list[ua_group - 1].value = target

    def load_target_file(b, entry_widget, button_widget):
        file_path = entry_widget.value
        try:
            df = pd.read_csv(file_path)
            with output_area:
                clear_output()
                print("File loaded successfully. Fields populated. \n")
                print(df.head())
                populate_target_values(df, widgets_list)
            valid_targets_widget.value = True
            valid_targets_widget.layout.display = ""
            PARAMETERS["targets_path"] = file_path
        except Exception as e:
            with output_area:
                clear_output()
                print(f"Error loading file: {e}\n")
                print("Correct the path or file format and load again.")
                print("You can also populate the values below manually instead of loading a CSV file.")
            valid_targets_widget.value = False
            valid_targets_widget.layout.display = ""
            PARAMETERS["targets_path"] = ""
    
    def recalculate_targets_based_on_threshold(b):
        threshold = target_cutoff_entry.value
        for widget in widgets_list:
            if widget.value > threshold:
                widget.value = threshold

    target_file_load_button.on_click(lambda b: load_target_file(b, target_file_path_entry, target_file_load_button))
    target_cutoff_recalculate_button.on_click(recalculate_targets_based_on_threshold)

    # Organize widgets into a grid layout
    hbox1 = widgets.HBox([target_info_button, target_file_path_entry, target_file_load_button, valid_targets_widget], layout = widgets.Layout(padding="10px"))
    grid = widgets.GridBox(widgets_list, layout=widgets.Layout(grid_template_columns="repeat(4, 200px)"))
    hbox2 = widgets.HBox([output_area], layout = widgets.Layout(padding="10px"))
    hbox3 = widgets.HBox([grid], layout = widgets.Layout(padding="10px"))
    hbox4 = widgets.HBox([target_cutoff_info_button, target_cutoff_entry, target_cutoff_recalculate_button], layout = widgets.Layout(padding="10px"))
    vbox = widgets.VBox([hbox1, hbox2, hbox3, hbox4])
    display(vbox)

def display_advanced_config():
    """
    Display the widgets for configuring advanced parameters.
    """
   
    # Widgets for holding target
    holding_active = widgets.Checkbox(value=True, description="Prioritize parcels of a holding until a limit per bucket is reached", style={"description_width": "initial"})
    holding_max = widgets.IntText(value=3, description="Parcels per bucket in a holding:", style={"description_width": "initial"})
    
    # Widgets for holding percentage
    holding_percentage_active = widgets.Checkbox(value=False, description="Limit search to a given fraction of holdings", style={"description_width": "initial"})
    holding_percentage_max = widgets.FloatText(value=0.03, description="Holding fraction limit:", style={"description_width": "initial"})
    
    # Widgets for image coverage
    image_coverage_active = widgets.Checkbox(value=True, description="Only include parcels covered by HR Images", style={"description_width": "initial"})
    
    # Widgets for output settings
    output_path = widgets.Text(value="./output", description="Output path:", style={"description_width": "initial"})
    #output_suffix = widgets.Text(value="STATS_300", description="Output Suffix:")

    # Observers to enable/disable max fields based on 'active' checkbox state
    def toggle_holding(change):
        holding_max.disabled = not change.new

    def toggle_holding_percentage(change):
        holding_percentage_max.disabled = not change.new

    holding_active.observe(toggle_holding, names='value')
    holding_percentage_active.observe(toggle_holding_percentage, names='value')

    # Layout for each parameter section
    holding_box = widgets.VBox([holding_active, holding_max], layout = widgets.Layout(padding="10px"))
    holding_percentage_box = widgets.VBox([holding_percentage_active, holding_percentage_max], layout = widgets.Layout(padding="10px"))
    image_coverage_box = widgets.VBox([image_coverage_active], layout = widgets.Layout(padding="10px"))
    output_box = widgets.VBox([widgets.Label(value="Output Settings:"), output_path], layout = widgets.Layout(padding="10px"))
    
    # Display all settings together
    config_box = widgets.VBox([holding_box, holding_percentage_box, image_coverage_box, output_box])
    display(config_box)