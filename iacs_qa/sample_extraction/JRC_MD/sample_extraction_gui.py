from input_verification import verify_parcel_df, verify_target_df, cross_verify_dfs, compare_bucket_lists
from IPython.display import display, clear_output, HTML
import ipywidgets as widgets
import pandas as pd


# TODO still:
# - text descriptions / instructions (me to write, ferdi to verify?)
# - input file format verification
# - 3% config (algorithm)
# - indicator if value loaded, manually modified, or limited by threshold


PARAMETERS = {"parcels_path": "",
              "targets_path": "",
              "ua_groups_and_thresholds": {},
              "parcel_file_loaded":False,
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


def create_text_entry(description, placeholder, width='500px'):
    """Create a text entry widget with specified properties."""
    return widgets.Combobox(
        placeholder=placeholder,
        description=description,
        ensure_option=False,
        disabled=False,
        style={"description_width": "initial"},
        layout=widgets.Layout(width=width)
    )

def create_button(description, button_style, tooltip, color='#1daee3'):
    """Create a button with specified properties."""
    return widgets.Button(
        description=description,
        button_style=button_style,
        tooltip=tooltip,
        style={"button_color": color}
    )

def create_info_button(info):
    """Create an information button with predefined style and tooltip."""
    return widgets.Button(
        icon="info",
        layout=widgets.Layout(width="30px"),
        button_style='',
        tooltip="Detailed info about file loading and verification."
    )

def get_ua_groups_from_parcel_file(parcels_df):
    """Extract unique ua_grp_id values from the parcel dataframe.
    Then populate the ua_groups_and_thresholds dictionary with these ids.
    Set default threshold values to 300 for each group.
    """
    ua_groups = parcels_df["ua_grp_id"].unique()
    for group in ua_groups:
        PARAMETERS["ua_groups_and_thresholds"][group] = 300

def load_parcel_file(entry_widget, output_area):
    """Callback function to load a file and display its contents."""
    with output_area:
        clear_output()
        print("Verifying file. Please wait...\n")
        file_path = entry_widget.value 
        try:
            df = pd.read_csv(file_path)
            verify_parcel_df(df)
            clear_output()
            PARAMETERS["parcels_path"] = file_path
            get_ua_groups_from_parcel_file(df)
            print("File loaded successfully. Preview: \n")
            print(df.head())
            PARAMETERS["parcel_file_loaded"] = True
        except Exception as e:
            clear_output()
            print(f"Error loading file: {e}\n")


def display_parcel_input_config():
    """Display the widgets for configuring the input parcel file path."""
    parcel_file_path_entry = create_text_entry("Parcel file path:", "example: input/parcels.csv")
    parcel_file_load_button = create_button("Load", "info", "Click to load parcel file")
    parcel_info_button = create_info_button("Info text here.")
    
    output_area = widgets.Output()
    parcel_file_load_button.unobserve_all()
    parcel_file_load_button.on_click(lambda b: load_parcel_file(parcel_file_path_entry, output_area))
    
    hbox = widgets.HBox([parcel_info_button, parcel_file_path_entry, parcel_file_load_button])
    vbox = widgets.VBox([hbox, output_area])
    display(vbox)

def create_info_button(tooltip, css_class="info-button-style"):
    """Create an information button with predefined style and tooltip."""
    button = widgets.Button(
        icon="info",
        layout=widgets.Layout(width="30px"),
        button_style='',
        tooltip=tooltip
    )
    button.add_class(css_class)
    return button

def create_target_widgets():
    """Create target widgets based on the parameters dictionary."""
    widgets_list = []
    if PARAMETERS["ua_groups_and_thresholds"] == {}:
        print("No ua_grp_id values found in the parcel data. Please load the parcel file first.")
    for group, threshold in PARAMETERS["ua_groups_and_thresholds"].items():
        label = group
        entry = widgets.BoundedIntText(
            value=threshold, 
            min=0, 
            max=int(1e10), 
            description=label, 
            layout=widgets.Layout(width="150px"),
            style={"description_width": "initial"}
        )
        widgets_list.append(entry)
    return widgets_list

def populate_target_values(target_df, widgets_list):
    """Populate widget values from the target dataframe."""
    for index, row in target_df.iterrows():
        ua_group = row["ua_grp_id"]
        target = row["target"]
        for widget in widgets_list:
            if widget.description == ua_group:
                widget.value = target
                break

def load_target_file(b, entry_widget, output_area, widgets_list):
    """Load target values from a file and populate widgets."""
    file_path = entry_widget.value
    with output_area:
        clear_output()
        print("Verifying file. Please wait...\n")
        try:
            df = pd.read_csv(file_path)
            verify_target_df(df)
            populate_target_values(df, widgets_list)
            compare_bucket_lists(PARAMETERS["ua_groups_and_thresholds"], df)
            print("File loaded successfully. Fields populated. \n")
            print(df.head())
        except Exception as e:
            clear_output()
            print(f"Error loading file: {e}\n")


def display_bucket_targets_config():
    """Set up and display the bucket targets configuration interface."""
    #ua_groups = { "YFS": 1, "SFS": 2, "ME2": 3, "ES2": 4, "ES1": 5, "E7B": 6, "E7A": 7, "E5": 8, "E4": 9, "E3": 10, "E2": 11, "E1C": 12, "CIS: LA": 13, "???" : 14, "C6C": 15, "C5": 16, "C4": 17, "C3": 18, "C2B": 19, "C1": 20, "BIS": 21, "ANC": 22}
    widgets_list = create_target_widgets()

    target_info_button = create_info_button("You can either provide the target values manually using the fields below, or load the values from a CSV file.")
    target_file_path_entry = create_text_entry("Bucket targets file path:", "example: input/targets.csv")
    target_file_load_button = create_button("Load", "info", "Click to pre-populate target values")

    output_area = widgets.Output()
    target_file_load_button.on_click(lambda b: load_target_file(b, target_file_path_entry, output_area, widgets_list))

    grid = widgets.GridBox(widgets_list, layout=widgets.Layout(grid_template_columns="repeat(4, 200px)"))
    hbox = widgets.HBox([target_info_button, target_file_path_entry, target_file_load_button], layout=widgets.Layout(padding="10px"))
    vbox = widgets.VBox([hbox, output_area, grid])
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