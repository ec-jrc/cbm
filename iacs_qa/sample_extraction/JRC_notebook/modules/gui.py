from IPython.display import display, clear_output, HTML
import ipywidgets as widgets
import pandas as pd

from modules.widget_builder import create_text_entry, create_button, create_info_button, create_int_entry, define_infobutton_style
from modules.input_verification import verify_parcel_df, verify_target_df, compare_bucket_lists
# from modules.data_manager import DataManager

# dm = DataManager()

display(HTML(define_infobutton_style()))

def target_widgets_on_value_change(change, datamanager): # controls gui behavior - stays in gui.py
    datamanager.target_values_state = f"(Target values were manually modified. Last change: {change['owner'].description} field changed to {change['new']}.)"
    datamanager.target_source_label.value = datamanager.target_values_state

def get_target_values_from_widgets(widgets_list, datamanager): # controls gui behavior - stays in gui.py
    for widget_box in widgets_list:
        widget = widget_box.children[0]
        datamanager.ua_groups[widget.description]["target"] = widget.value

def create_target_widgets(datamanager):
    widget_list = []
    for group, info in datamanager.ua_groups.items():
        target = info["target"]
        count = info["count"]
        if target > count:
            target = count

        entry = widgets.BoundedIntText(
            value=target,
            min=0,
            max=int(1e10),
            description=group,
            layout=widgets.Layout(width="150px"),
            style={"description_width": "initial"}
            
        )
        entry.observe(lambda change, dm=datamanager: target_widgets_on_value_change(change, dm), names='value')

        count_label = widgets.Label(value=f"({info['count']} found)")

        group_box = widgets.HBox([entry, count_label])
        widget_list.append(group_box)
    return widget_list

def get_ua_groups_from_parcel_file(parcels_df):
    """
    Extract unique ua group identifiers from a parcel dataframe and update a global dictionary with default thresholds.

    Args:
    parcels_df (pandas.DataFrame): Dataframe containing parcel data with a column "ua_grp_id".
    """
    ua_groups = parcels_df["ua_grp_id"].unique()
    ua_group_count = parcels_df["ua_grp_id"].value_counts().to_dict()
    ua_group_dict = {}
    for group in ua_groups:
        ua_group_dict[group] = {"target" : 300, "count" : ua_group_count[group]}
    return ua_group_dict
        #PARAMETERS["ua_groups"][group] = {"target" : 300, "count" : ua_group_count[group]}


def populate_target_values(target_df, widgets_list):
    """
    Populate the values of target widgets using a dataframe that contains target values.

    Args:
    target_df (pandas.DataFrame): Dataframe containing the target values with columns "ua_grp_id" and "target".
    widgets_list (list): List of widget objects where each widget's description matches a "ua_grp_id".
    """
    for index, row in target_df.iterrows():
        ua_group = row["ua_grp_id"]
        target = row["target"]
        for widget_box in widgets_list:
            widget = widget_box.children[0]
            if widget.description == ua_group:
                widget.value = target
                break

def recalculate_targets_based_on_threshold(entry_widget, widgets_list, datamanager):
    """
    Adjust the values of target fields based on a new threshold set by the user.

    Args:
    entry_widget (ipywidgets.Widget): Widget that contains the new threshold value.
    widgets_list (list): List of target widgets to be adjusted.
    """
    # group_box = widgets.HBox([entry, count_label])
    threshold = entry_widget.value
    for widget_box in widgets_list:
        widget = widget_box.children[0]
        if widget.value > threshold:
            widget.value = threshold
    datamanager.target_values_state = "(Target values modified using the target cutoff setting.)"
    datamanager.target_source_label.value = datamanager.target_values_state

    get_target_values_from_widgets(widgets_list, datamanager)


def load_parcel_file(entry_widget, output_area, datamanager):
    """
    Load parcel data from a file specified by the user, verify its structure, and update the UI accordingly.

    Args:
    entry_widget (ipywidgets.Text): Widget containing the file path to the parcel file.
    output_area (ipywidgets.Output): Widget used to display messages and file content.
    """
    with output_area:
        clear_output()
        print("Verifying file. Please wait...\n")
        file_path = entry_widget.value 
        try:
            df = pd.read_csv(file_path)
            verify_parcel_df(df)
            clear_output()
            datamanager.parcels_path = file_path
            ua_group_dict = get_ua_groups_from_parcel_file(df)
            datamanager.ua_groups = ua_group_dict
            print("File loaded successfully. Preview: \n")
            print(df.head())
            datamanager.parcels_df = df
            datamanager.parcel_file_loaded = True
        except Exception as e:
            clear_output()
            print(f"Error loading file: {e}\n")

def load_target_file(b, entry_widget, output_area, widgets_list, datamanager):
    """
    Load target values from a specified file, populate widgets, and handle errors or discrepancies in the data.

    Args:
    b (ipywidgets.Button): Button that triggered the file load.
    entry_widget (ipywidgets.Text): Widget containing the file path to the target file.
    output_area (ipywidgets.Output): Widget used to display messages and data.
    widgets_list (list): List of widgets that will be populated with the target values.
    """
    file_path = entry_widget.value
    with output_area:
        clear_output()
        try:
            df = pd.read_csv(file_path)
            verify_target_df(df)
            populate_target_values(df, widgets_list)
            compare_bucket_lists(datamanager.ua_groups, df)
            datamanager.target_values_state = "(Target values loaded from the targets file.)"
            datamanager.target_source_label.value = datamanager.target_values_state
            get_target_values_from_widgets(widgets_list, datamanager)
            print("Target file loaded successfully. Fields repopulated. \n")
        except Exception as e:
            clear_output()
            print(f"Error loading file: {e}\n")



def display_parcel_input_config(datamanager):
    """
    Display a user interface for configuring the parcel file input path and load button.
    """
    parcel_file_path_entry = create_text_entry("Parcel file path:", "example: input/parcels.csv")
    parcel_file_load_button = create_button("Load", "info", "Click to load parcel file")
    parcel_info_button = create_info_button("Info text here.")
    parcel_info_button.add_class("info-button-style")

    if datamanager.parcels_path != "":
        parcel_file_path_entry.value = datamanager.parcels_path
    
    output_area = widgets.Output()
    parcel_file_load_button.unobserve_all()
    parcel_file_load_button.on_click(lambda b: load_parcel_file(parcel_file_path_entry, output_area, datamanager))
    
    hbox = widgets.HBox([parcel_info_button, parcel_file_path_entry, parcel_file_load_button])
    vbox = widgets.VBox([hbox, output_area])
    display(vbox)


def display_bucket_targets_config(datamanager):
    """
    Set up and display a user interface for configuring and populating target values for different buckets using widgets.
    """
    widgets_list = create_target_widgets(datamanager)

    if widgets_list == []:
        print("Please load the parcel file first and run this cell again.")
    else:
        target_source_label = widgets.Label(value=datamanager.target_values_state)
        datamanager.target_source_label = target_source_label

        target_info_button = create_info_button("You can either provide the target values manually using the fields below, or load the values from a CSV file.")
        target_info_button.add_class("info-button-style")
        target_file_path_entry = create_text_entry("Bucket targets file path:", "example: input/targets.csv")
        target_file_load_button = create_button("Load", "info", "Click to pre-populate target values")

        if datamanager.targets_path != "":
            target_file_path_entry.value = datamanager.targets_path
        
        output_area = widgets.Output()
        target_file_load_button.on_click(lambda b: load_target_file(b, target_file_path_entry, output_area, widgets_list, datamanager))

        target_cutoff_info_button = create_info_button("Info text here.")
        target_cutoff_info_button.add_class("info-button-style")
        target_cutoff_entry = create_int_entry("Target cutoff:", "example: 300", 0, int(1e10), width="150px")
        target_cutoff_recalculate_button = create_button("Recalculate", "info", "Click to recalculate target values")
        target_cutoff_recalculate_button.on_click(lambda b: recalculate_targets_based_on_threshold(target_cutoff_entry, widgets_list, datamanager))

        hbox0 = widgets.HBox([target_source_label])
        grid = widgets.GridBox(widgets_list, layout=widgets.Layout(grid_template_columns="repeat(3, 300px)", padding="10px"))
        hbox1 = widgets.HBox([target_file_path_entry, target_file_load_button,target_info_button], layout=widgets.Layout(padding="10px"))
        hbox2 = widgets.HBox([target_cutoff_entry, target_cutoff_recalculate_button, target_cutoff_info_button], layout=widgets.Layout(padding="10px"))
        vbox = widgets.VBox([hbox0, grid, hbox1, hbox2, output_area])
        display(vbox)

def display_advanced_config():
    """
    Display a configuration interface with advanced options for setting constraints on parcel processing and output settings.
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
    
    # make all widgets in the config_box boxes disabled:
    for box in config_box.children:
        for widget in box.children:
            widget.disabled = True
    
    display(config_box)


def display_output_area(buckets):

    # display(HTML("<style>.red_label { color:red }</style>"))
    # l = Label(value="My Label")
    # l.add_class("red_label")
    # display(l)
    vbox_list = []

    display(HTML("<style>.orange_label { color:orange }</style>"))
    display(HTML("<style>.orange_label_bold { color:orange; font-weight: bold }</style>"))

    display(HTML("<style>.green_label_bold { color:green; font-weight: bold }</style>"))
    display(HTML("<style>.green_label { color:green }</style>"))



    for bucket_id, bucket in buckets.items():
        header_label = widgets.Label(value=f"Bucket: {bucket_id}")
        if bucket["target"] == 0:
            header_label.add_class("green_label_bold")
            progress_value = 1
            progress_label = widgets.Label(value=f"Completed: {progress_value:.2%} ( {len(bucket['parcels'])} / {bucket['target']} )")
            progress_label.add_class("green_label")
        else:
            header_label.add_class("orange_label_bold")
            progress_value = len(bucket["parcels"]) / bucket["target"]
            progress_label = widgets.Label(value=f"Completed: {progress_value:.2%} ( {len(bucket['parcels'])} / {bucket['target']} )")
            progress_label.add_class("orange_label")
        progress_bar = widgets.FloatProgress(
            value=progress_value,
            min=0,
            max=1,
            description="Progress:",
            bar_style="info",
            style={"description_width": "initial"}
        )
        hbox_header_progress = widgets.HBox([header_label, progress_label])
        vbox_list.append(widgets.VBox([hbox_header_progress, progress_bar]))
    
    grid = widgets.GridBox(vbox_list, layout=widgets.Layout(grid_template_columns="repeat(3, 1fr)", padding="10px"))
    display(grid)
    return grid

def update_output_area(buckets, grid):
    """
    update widgets created in display_output_area
    """
    for i, (bucket_id, bucket) in enumerate(buckets.items()):
        if bucket['target'] == 0:
            continue
        if len(bucket['parcels']) == bucket['target']:
            grid.children[i].children[0].children[0].add_class("green_label_bold")
            grid.children[i].children[0].children[1].add_class("green_label")
        grid.children[i].children[0].children[1].value = f"Completed: {len(bucket['parcels']) / bucket['target']:.2%} ( {len(bucket['parcels'])} / {bucket['target']} )"
        grid.children[i].children[1].value = len(bucket['parcels']) / bucket['target']
        