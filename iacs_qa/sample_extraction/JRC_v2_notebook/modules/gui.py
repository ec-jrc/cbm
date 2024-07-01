import io
from IPython.display import display, clear_output, HTML
import ipywidgets as widgets
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from ipyfilechooser import FileChooser

from modules.widget_builder import create_text_entry, create_button, create_info_button, create_int_entry, define_infobutton_style
from modules.input_verification import verify_parcel_df, verify_target_df, compare_bucket_lists, verify_and_report_parcel_df

display(HTML(define_infobutton_style()))

def target_widgets_on_value_change(change, datamanager): # controls gui behavior - stays in gui.py
    datamanager.target_values_state = f"(Target values were manually modified. Last change: {change['owner'].description} field changed to {change['new']}.)"
    datamanager.target_source_label.value = datamanager.target_values_state
    get_target_values_from_widgets(datamanager.target_widgets_list, datamanager)

def limit_3perc_widget_on_value_change(change, datamanager):
    datamanager.param_3_percent = change["new"]

def image_coverage_widget_on_value_change(change, datamanager):
    datamanager.covered_priority = datamanager.covered_priority_dict[change["new"]]

def get_group_id_based_on_widget_description(description, datamanager):
    for group, info in datamanager.ua_groups.items():
        if info["desc"] == description:
            return group

def get_target_values_from_widgets(widgets_list, datamanager): # controls gui behavior - stays in gui.py
    for widget_box in widgets_list:
        widget = widget_box.children[0]
        datamanager.ua_groups[get_group_id_based_on_widget_description(widget.description,datamanager)]["target"] = widget.value

def create_target_widgets(datamanager):
    widget_list = []
    for group, info in datamanager.ua_groups.items():
        target = info["target"]
        count = info["count"]
        desc = info["desc"]
        if target > count:
            target = count

        # set the boundedintext widget's input field width to 100px
        entry = widgets.BoundedIntText(
            value=target,
            min=0,
            max=int(1e10),
            description=desc,
            layout=widgets.Layout(width="200px"),
            style={"description_width": "65%", "font_family": "monospace"},
            tooltip=group,
            max_width = "50px"
        )
        entry.observe(lambda change, dm=datamanager: target_widgets_on_value_change(change, dm), names='value')

        count_label = widgets.Label(value=f"({info['count']} found)")

        group_box = widgets.HBox([entry, count_label])
        widget_list.append(group_box)
    datamanager.target_widgets_list = widget_list
    return widget_list

def create_ua_group_description(group_id, counter):
    limit = 20
    if len(group_id) > limit:
        group_id = group_id[:limit] + "..."
    # else:
    #     # add spaces to the end of the string to make all descriptions the same length
    #     group_id = group_id + " " * (limit - len(group_id))
    
    return f"{counter}. {group_id}"

def get_ua_groups_from_parcel_file(parcels_df):
    """
    Extract unique ua group identifiers from a parcel dataframe and update a global dictionary with default thresholds.

    Args:
    parcels_df (pandas.DataFrame): Dataframe containing parcel data with a column "ua_grp_id".
    """
    ua_groups = parcels_df["ua_grp_id"].unique()
    ua_group_count = parcels_df["ua_grp_id"].value_counts().to_dict()
    ua_group_dict = {}
    counter = 1
    print(f"File loaded successfully. Number of rows: {len(parcels_df)}\n")
    print(f"Detected {len(ua_groups)} unique UA groups:\n")
    for group in ua_groups:
        count_for_group = ua_group_count[group]
        # print(f"{group}: {count_for_group} rows detected.")
        if count_for_group >= 6000:
            default_target = 300
        else:
            default_target = int(count_for_group * 0.05)
        ua_group_dict[group] = {"target" : default_target, "count" : ua_group_count[group], "desc" : create_ua_group_description(group, counter)}
        counter += 1

    # draw a simple bar chart to visualize the distribution of ua groups

    fig = plt.figure(figsize=(10, 4))  # Reduced height from 5 to 3
    ax = fig.add_subplot(111)

    bars = ax.bar(ua_group_count.keys(), ua_group_count.values(), color='#1daee3')

    plt.xlabel("UA Group ID")
    plt.ylabel("Number of rows")
    plt.title("Distribution of UA groups")
    plt.xticks(rotation=45, ha='right')

    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}',
                ha='center', va='bottom')

    plt.tight_layout()  # Adjust layout to prevent cut-off labels
    plt.show()

    print("\nDefault target values set based on the number of rows in each UA group (5%, max 300).\n")

    return ua_group_dict


def get_ua_groups_from_parcel_file_ulm(parcels_df):
    """
    Extract unique ua group identifiers from a parcel dataframe and update a global dictionary with default thresholds.

    Args:
    parcels_df (pandas.DataFrame): Dataframe containing parcel data with a column "ua_grp_id".
    """
    ua_groups = parcels_df["ua_grp_id"].unique()
    ua_group_count = parcels_df["ua_grp_id"].value_counts().to_dict()
    ua_group_dict = {}
    counter = 1
    print(f"File loaded successfully. Number of rows: {len(parcels_df)}\n")
    print(f"Detected {len(ua_groups)} unique UA groups:\n")
    for group in ua_groups:
        count_for_group = ua_group_count[group]
        # print(f"{group}: {count_for_group} rows detected.")
        if 0 <= count_for_group <= 50:
            default_target = count_for_group
        elif 51 <= count_for_group <= 100:
            default_target = 50
        elif 101 <= count_for_group <= 200:
            default_target = 50
        elif 201 <= count_for_group <= 300:
            default_target = 55
        elif 301 <= count_for_group <= 400:
            default_target = 110
        elif 401 <= count_for_group <= 500:
            default_target = 115
        elif 501 <= count_for_group <= 600:
            default_target = 170
        elif 601 <= count_for_group <= 700:
            default_target = 170
        elif 701 <= count_for_group <= 800:
            default_target = 175
        elif 801 <= count_for_group <= 900:
            default_target = 230
        elif 901 <= count_for_group <= 1200:
            default_target = 230
        else: # more than 1200
            default_target = 300
        ua_group_dict[group] = {"target" : default_target, "count" : ua_group_count[group], "desc" : create_ua_group_description(group, counter)}
        counter += 1

    # draw a simple bar chart to visualize the distribution of ua groups

    fig = plt.figure(figsize=(10, 4))  # Reduced height from 5 to 3
    ax = fig.add_subplot(111)

    bars = ax.bar(ua_group_count.keys(), ua_group_count.values(), color="#1daee3")

    plt.xlabel("UA Group ID")
    plt.ylabel("Number of rows")
    plt.title("Distribution of UA groups")
    plt.xticks(rotation=45, ha="right")

    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                str(height),
                ha="center", va="bottom")

    plt.tight_layout()  # Adjust layout to prevent cut-off labels
    plt.show()

    print("\nDefault targets set based on the values recommended by the Union level methodology.\n")

    return ua_group_dict
        #PARAMETERS["ua_groups"][group] = {"target" : 300, "count" : ua_group_count[group]}

def populate_target_values(target_df, widgets_list, datamanager):
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
            if widget.description == datamanager.ua_groups[ua_group]["desc"]:
                widget.value = target
                break

def recalculate_targets_based_on_threshold(entry_widget, widgets_list, datamanager):
    """
    Adjust the values of target fields based on a new threshold set by the user.

    Args:
    entry_widget (ipywidgets.Widget): Widget that contains the new threshold value.
    widgets_list (list): List of target widgets to be adjusted.
    """
    threshold = entry_widget.value
    for widget_box in widgets_list:
        widget = widget_box.children[0]
        if widget.value > threshold:
            widget.value = threshold
    datamanager.target_values_state = "(Target values modified using the target cutoff setting.)"
    datamanager.target_source_label.value = datamanager.target_values_state

    get_target_values_from_widgets(widgets_list, datamanager)


def recalculate_targets_based_on_percentage(entry_widget, widgets_list, datamanager):
    """
    Adjust the values of target fields based on a percentage set by the user.
    (adds or removes a percentage of the current target value)

    Args:
    entry_widget (ipywidgets.Widget): Widget that contains the new threshold value.
    widgets_list (list): List of target widgets to be adjusted.
    """
    percentage = entry_widget.value
    for widget_box in widgets_list:
        widget = widget_box.children[0]
        widget.value += widget.value * percentage / 100
    datamanager.target_values_state = "(Target values modified using the increase by fraction setting.)"
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
            # verify_parcel_df(df)
            # verify_parcel_df_and_save_report(df)
            # verify_and_clean_with_counting(df)
            verify_and_report_parcel_df(df)
            clear_output()
            datamanager.parcels_path = file_path
            ua_group_dict = get_ua_groups_from_parcel_file(df)
            datamanager.ua_groups = ua_group_dict
            print("Parcel file header preview: \n")
            print(df.head())
            datamanager.parcels_df = df
            datamanager.parcel_file_loaded = True
        except Exception as e:
            clear_output()
            print(f"Error(s) loading file: {e}\n")

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
            compare_bucket_lists(datamanager.ua_groups, df)
            populate_target_values(df, widgets_list, datamanager)
            
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
    parcel_info_button = create_info_button("Direct or relative path to the .CSV file containing the parcel list.")
    parcel_info_button.add_class("info-button-style")

    if datamanager.parcels_path != "":
        parcel_file_path_entry.value = datamanager.parcels_path
    
    output_area = widgets.Output()
    parcel_file_load_button.unobserve_all()
    parcel_file_load_button.on_click(lambda b: load_parcel_file(parcel_file_path_entry, output_area, datamanager))

    fc = FileChooser()
    fc.filter_pattern = ["*.csv", "*.CSV"]
    fc.title = "Select parcel file using the file selector ('Select' button) or provide a path below.\nRemember to then load it using the 'Load' button."

    def parcel_entry_completion_callback(fc):
        parcel_file_path_entry.value = fc.selected
    
    fc.register_callback(parcel_entry_completion_callback)

    hbox = widgets.HBox([parcel_info_button, parcel_file_path_entry, parcel_file_load_button])
    vbox = widgets.VBox([fc, hbox, output_area])

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

        target_cutoff_info_button = create_info_button("This allows you to automatically limit all targets to a certain value (will only affect values above the defined cutoff).")
        target_cutoff_info_button.add_class("info-button-style")
        target_cutoff_entry = create_int_entry("Target cutoff:", "example: 300", 0, int(1e10), width="150px")
        target_cutoff_recalculate_button = create_button("Recalculate", "info", "Click to recalculate target values")
        target_cutoff_recalculate_button.on_click(lambda b: recalculate_targets_based_on_threshold(target_cutoff_entry, widgets_list, datamanager))

        hbox0 = widgets.HBox([target_source_label])
        grid = widgets.GridBox(widgets_list, layout=widgets.Layout(grid_template_columns="repeat(3, 350px)", padding="10px"))

        fc = FileChooser()
        fc.filter_pattern = ["*.csv", "*.CSV"]
        fc.title = "Select target file using the file selector ('Select' button) or provide a path below.\nYou can then load it using the 'Load' button."

        def target_entry_completion_callback(fc):
            target_file_path_entry.value = fc.selected
        
        fc.register_callback(target_entry_completion_callback)

        hbox1 = widgets.HBox([target_file_path_entry, target_file_load_button,target_info_button], layout=widgets.Layout(padding="10px"))
        hbox2 = widgets.HBox([target_cutoff_entry, target_cutoff_recalculate_button, target_cutoff_info_button], layout=widgets.Layout(padding="10px"))
        vbox = widgets.VBox([hbox0, grid, fc, hbox1, hbox2, output_area])

        display(vbox)

def display_bucket_targets_config_ulm(datamanager):
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

        target_cutoff_info_button = create_info_button("This allows you to automatically limit all targets to a certain value (will only affect values above the defined cutoff).")
        target_cutoff_info_button.add_class("info-button-style")
        target_cutoff_entry = create_int_entry("Increase all targets by", "example: 10", -100, int(1e10), width="200px")
        target_perc_label = widgets.Label(value="%")
        target_cutoff_recalculate_button = create_button("Recalculate", "info", "Click to recalculate target values")
        target_cutoff_recalculate_button.on_click(lambda b: recalculate_targets_based_on_percentage(target_cutoff_entry, widgets_list, datamanager))

        hbox0 = widgets.HBox([target_source_label])
        grid = widgets.GridBox(widgets_list, layout=widgets.Layout(grid_template_columns="repeat(3, 350px)", padding="10px"))

        fc = FileChooser()
        fc.filter_pattern = ["*.csv", "*.CSV"]
        fc.title = "Select target file using the file selector ('Select' button) or provide a path below.\nYou can then load it using the 'Load' button."

        def target_entry_completion_callback(fc):
            target_file_path_entry.value = fc.selected
        
        fc.register_callback(target_entry_completion_callback)

        hbox1 = widgets.HBox([target_file_path_entry, target_file_load_button,target_info_button], layout=widgets.Layout(padding="10px"))
        hbox2 = widgets.HBox([target_cutoff_entry, target_perc_label, target_cutoff_recalculate_button, target_cutoff_info_button], layout=widgets.Layout(padding="10px"))
        vbox = widgets.VBox([hbox0, grid, fc, hbox1, hbox2, output_area])

        display(vbox)


def display_advanced_parameters(datamanager):
    holding_percentage_active = widgets.Checkbox(value=False, description="Limit search to 3% of holdings", style={"description_width": "initial"})
    holding_percentage_active.observe(lambda change: limit_3perc_widget_on_value_change(change, datamanager), names='value')

    image_coverage_radiobuttons = widgets.RadioButtons(
        options=["Include all parcels in the sample extraction", "Prioritize parcels covered by VHR images (beta)", "Include only parcels covered by VHR images"],
        value="Include all parcels in the sample extraction",
        description="VHR image coverage options:",
        style={"description_width": "initial"}
    )
    image_coverage_radiobuttons.observe(lambda change: image_coverage_widget_on_value_change(change, datamanager), names='value')

    hbox0 = widgets.HBox([widgets.Label(value="Advanced Parameters:")], layout=widgets.Layout(padding="10px"))
    hbox1 = widgets.HBox([holding_percentage_active], layout=widgets.Layout(padding="0px"))
    hbox2 = widgets.HBox([image_coverage_radiobuttons], layout=widgets.Layout(padding="12px"))
    vbox = widgets.VBox([hbox0, hbox1, hbox2], layout=widgets.Layout(padding="10px"))
    display(vbox)


def display_output_area(buckets, datamanager):
    vbox_list = []
    dm = datamanager

    # display(HTML("<style>.orange_label { color:orange }</style>"))
    # display(HTML("<style>.orange_label_bold { color:orange; font-weight: bold }</style>"))

    # display(HTML("<style>.green_label_bold { color:green; font-weight: bold }</style>"))
    # display(HTML("<style>.green_label { color:green }</style>"))

    # display(HTML("<style>.black_label_bold { color:black; font-weight: bold }</style>"))

    # display(HTML("<style>.title_label { color:black; font-weight: bold; font-size: 12 }</style>"))

    styles_html = """
    <b>SAMPLE EXTRACTION PROGRESS:</b><br>
    <style>.orange_label { color:orange }</style>
    <style>.orange_label_bold { color:orange; font-weight: bold }</style>
    <style>.green_label_bold { color:green; font-weight: bold }</style>
    <style>.green_label { color:green }</style>
    <style>.black_label_bold { color:black; font-weight: bold }</style>
    <style>.title_label { color:black; font-weight: bold; font-size: 22px }</style>
    """
    display(HTML(styles_html))



    for bucket_id, bucket in buckets.items():
        header_label_text = dm.ua_groups[bucket_id]["desc"]
        header_label = widgets.Label(value=header_label_text, tooltip=bucket_id)
        if bucket["target"] == 0:
            header_label.add_class("green_label_bold")
            progress_value = 1
            progress_label = widgets.Label(value=f"| Found: {progress_value:.2%} ( {len(bucket['parcels'])} / {bucket['target']} )")
            progress_label.add_class("green_label")
        else:
            header_label.add_class("orange_label_bold")
            progress_value = len(bucket["parcels"]) / bucket["target"]
            progress_label = widgets.Label(value=f"| Found: {progress_value:.2%} ( {len(bucket['parcels'])} / {bucket['target']} )")
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
    
    grid = widgets.GridBox(vbox_list, layout=widgets.Layout(grid_template_columns="repeat(3, 1fr)", padding="5px"))
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
        grid.children[i].children[0].children[1].value = f"| Found: {len(bucket['parcels']) / bucket['target']:.2%} ( {len(bucket['parcels'])} / {bucket['target']} )"
        grid.children[i].children[1].value = len(bucket['parcels']) / bucket['target']


def calculate_holding_with_most_interventions_selected(datamanager):
    # calculate the holding with the most interventions selected
    holding_interventions = {}
    for bucket in datamanager.final_bucket_state.values():
        for parcel in bucket["parcels"]:
            holding = parcel["gsa_hol_id"]
            if holding in holding_interventions:
                holding_interventions[holding] += 1
            else:
                holding_interventions[holding] = 1
    holding_with_most_interventions = max(holding_interventions, key=holding_interventions.get)
    return holding_with_most_interventions, holding_interventions[holding_with_most_interventions]


def all_parcels_in_buckets(buckets):
    """
    Count all parcels in buckets. Identify parcels by their par_id and hol_id.
    """
    all_parcels = []
    for bucket in buckets.values():
        for parcel in bucket["parcels"]:
            unique_parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
            all_parcels.append(unique_parcel_id)
    return set(all_parcels)

def count_unique_selected_parcels_per_holding(all_selected_parcels):
    parcels_per_holding = {}
    for a in all_selected_parcels:
        par_id = a.split("_")[0]
        hol_id = a.split("_")[1]
        if hol_id in parcels_per_holding:
            parcels_per_holding[hol_id].add(par_id)
        else:
            parcels_per_holding[hol_id] = {par_id}

    # count the number of unique parcels per holding
    count_per_holding = {hol_id: len(parcels) for hol_id, parcels in parcels_per_holding.items()}

    # calculate the average number of parcels per holding
    avg_parcels_per_holding = sum(count_per_holding.values()) / len(count_per_holding)
    return count_per_holding, avg_parcels_per_holding

def count_selected_covered_parcels(datamanager):
    covered_parcels = []
    noncovered_parcels = []
    for bucket in datamanager.final_bucket_state.values():
        for parcel in bucket["parcels"]:
            if parcel["covered"] == 1:
                unique_parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
                covered_parcels.append(unique_parcel_id)
            else:
                noncovered_parcels.append(unique_parcel_id)

    return len(set(covered_parcels)), len(set(noncovered_parcels))

def display_statistics_summary(datamanager):
    total_rows = len(datamanager.parcels_df)
    selected_rows = sum([len(bucket['parcels']) for bucket in datamanager.final_bucket_state.values()])

    # a unique parcel has a unique par_id and hol_id
    # I assume that there can be multiple parcels with the same gsa_par_id but different gsa_hol_id
    all_unique_parcels_count = len(datamanager.parcels_df.drop_duplicates(subset=["gsa_par_id", "gsa_hol_id"]))
    all_selected_parcels = all_parcels_in_buckets(datamanager.final_bucket_state)
    all_selected_parcels_count = len(all_selected_parcels)

    avg_par_per_hol = count_unique_selected_parcels_per_holding(all_selected_parcels)[1]
    
    total_holdings = len(datamanager.parcels_df["gsa_hol_id"].unique())
    selected_holdings = len(datamanager.added_holdings)
    avg_int_per_holding = selected_rows / selected_holdings
    most_interventions = calculate_holding_with_most_interventions_selected(datamanager)

    all_buckets_full = all([bucket["target"] == len(bucket["parcels"]) for bucket in datamanager.final_bucket_state.values()])
    if all_buckets_full:
        bucket_status_label = widgets.Label(value="All buckets are full!")
        bucket_status_label.add_class("green_label_bold")
    else:
        bucket_status_label = widgets.Label(value="Not all buckets are full. See progress indicators for details.")
        bucket_status_label.add_class("orange_label_bold")

    title_label = widgets.Label(value="Summary statistics:")
    title_label.add_class("title_label")

    sp_label = widgets.Label(value=f"Selected individual parcels: {all_selected_parcels_count} / {all_unique_parcels_count} ({all_selected_parcels_count/all_unique_parcels_count*100:.2f}%)")
    sp_label.add_class("black_label_bold")
    tsr_label = widgets.Label(value=f"(Total selected rows: {selected_rows} / {total_rows} ({selected_rows/total_rows*100:.2f}%))")

    sh_label = widgets.Label(value=f"Selected holdings: {selected_holdings} / {total_holdings} ({selected_holdings/total_holdings*100:.2f}%)")
    sh_label.add_class("black_label_bold")

    asppsh_label = widgets.Label(value=f"Average number of selected parcels per selected holding: {avg_par_per_hol:.2f}")
    asppsh_label.add_class("black_label_bold")

    asrpsh_label = widgets.Label(value=f"(Average selected rows per selected holding: {avg_int_per_holding:.2f})")

    count_per_holding, _ = count_unique_selected_parcels_per_holding(all_selected_parcels)
    holding_with_highest_count = max(count_per_holding, key=count_per_holding.get)
    hwmrs_label = widgets.Label(value=f"Holding with most parcels selected: '{holding_with_highest_count}' ({count_per_holding[holding_with_highest_count]} parcels)")

    vbox = widgets.VBox([title_label, 
                         bucket_status_label, 
                         sp_label, 
                         sh_label, 
                         asppsh_label, 
                         #hwmrs_label,
                         ], 
                         layout=widgets.Layout(padding="10px"))

    display(vbox)

def calculate_stats_for_reused_parcels(datamanager):
    counts_for_parcels = {}

    for bucket_id, bucket in datamanager.final_bucket_state.items():
        for parcel in bucket["parcels"]:
            parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
            if parcel_id in counts_for_parcels:
                counts_for_parcels[parcel_id] += 1
            else:
                counts_for_parcels[parcel_id] = 1

    histogram_buckets = {}
    for parcel_id, count in counts_for_parcels.items():
        if count in histogram_buckets:
            histogram_buckets[count] += 1
        else:
            histogram_buckets[count] = 1
    
    return histogram_buckets

# def display_reused_histogram(datamanager):
#     histogram_buckets = calculate_stats_for_reused_parcels(datamanager)

#     sorted_buckets = dict(sorted(histogram_buckets.items()))

#     # Get keys and values
#     keys = list(sorted_buckets.keys())
#     values = list(sorted_buckets.values())

#     # Generate a colormap
#     # colors = plt.cm.viridis(np.linspace(0, 1, len(keys)))

#     # Set the figure size to make the chart flatter and more compact
#     plt.figure(figsize=(5, 3))  # Width 8, Height 4

#     # Create the bar plot
#     plt.bar(keys, values, color="#00bcd4")

#     # Add labels to each bar with smaller font size
#     for i, value in enumerate(values):
#         plt.text(keys[i], value + 5, str(value), ha="center", fontsize=8)

#     # Create x-axis labels
#     xaxis_labels = [f"Parcels used {k} times" if k > 1 else "Parcels used once" for k in keys]

#     # Set title and labels with smaller font sizes
#     plt.title("Parcels found in multiple ua_group buckets", fontsize=10)
#     plt.xlabel("")
#     plt.ylabel("Number of parcels", fontsize=10)
#     plt.xticks(keys, xaxis_labels, rotation=45, ha="right", fontsize=8)  # Use custom labels and rotate them
#     plt.yticks(fontsize=8)  # Smaller font size for y-axis ticks

#     plt.show()

def reused_histogram_widget(datamanager):
    histogram_buckets = calculate_stats_for_reused_parcels(datamanager)

    sorted_buckets = dict(sorted(histogram_buckets.items()))

    # Get keys and values
    keys = list(sorted_buckets.keys())
    values = list(sorted_buckets.values())

    # Generate a colormap
    # colors = plt.cm.viridis(np.linspace(0, 1, len(keys)))

    # Set the figure size to make the chart flatter and more compact
    figsize = (5, 3)
    plt.figure(figsize=figsize)  # Width 8, Height 4

    # Create the bar plot
    plt.bar(keys, values, color="#1daee3")

    # Add labels to each bar with smaller font size
    for i, value in enumerate(values):
        plt.text(keys[i], value + 5, str(value), ha="center", fontsize=8)

    # Create x-axis labels
    xaxis_labels = [f"Parcels found in {k} buckets" if k > 1 else "Parcels found in 1 bucket" for k in keys]

    # Set title and labels with smaller font sizes
    plt.title("Parcels found in multiple ua_group buckets", fontsize=10)
    plt.xlabel("")
    plt.ylabel("Number of parcels", fontsize=10)
    plt.xticks(keys, xaxis_labels, rotation=45, ha="right", fontsize=8)  # Use custom labels and rotate them
    plt.yticks(fontsize=8)  # Smaller font size for y-axis ticks

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return widgets.Image(value=buf.getvalue(), format='png')#, width=figsize[0]*25, height=figsize[1]*25)

def display_covered_parcels_piechart(datamanager):
    covered, noncovered = count_selected_covered_parcels(datamanager)
    # Function to create a pie chart and return it as an image widget
    def create_pie_chart(covered, noncovered, figsize=(7, 7)):
        fig, ax = plt.subplots(figsize=figsize)  # Adjust size here
        sizes = [covered, noncovered]
        labels = ['Covered', 'Non-covered']
        colors = ['#1daee3', '#DFDFDF']
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 14})
        
        # Set the font size of the labels dynamically
        for text in texts:
            text.set_fontsize(40) 
        for autotext in autotexts:
            autotext.set_fontsize(40)
        
        ax.axis('equal')
        plt.title("Selected parcels covered by VHR images", fontsize=40)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return widgets.Image(value=buf.getvalue(), format='png', width=figsize[0]*25, height=figsize[1]*25)

    pcs = 12

    covered_pie_widget = create_pie_chart(covered, noncovered, figsize=(pcs, pcs))

    #display(covered_pie_widget)
    return covered_pie_widget

def display_reused_and_covered(datamanager):
    histogram = reused_histogram_widget(datamanager)
    piechart = display_covered_parcels_piechart(datamanager)
    grid = widgets.GridBox([histogram, piechart], layout=widgets.Layout(grid_template_columns="repeat(2, 500px)", padding="1px"))
    display(grid)

def display_bucket_pie_charts(datamanager):
    # total statistic (top)
    total_rows = len(datamanager.parcels_df)
    selected_rows = sum([len(bucket['parcels']) for bucket in datamanager.final_bucket_state.values()])
    total_holdings = len(datamanager.parcels_df["gsa_hol_id"].unique())
    selected_holdings = len(datamanager.added_holdings)

    # Function to create a pie chart and return it as an image widget
    def create_pie_chart(selected, total, title, figsize=(7, 7)):
        fig, ax = plt.subplots(figsize=figsize)  # Adjust size here
        sizes = [selected, total - selected]
        labels = ['Selected', 'Remaining']
        colors = ['#31C800', '#DFDFDF']
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 14})
        
        # Set the font size of the labels dynamically
        for text in texts:
            text.set_fontsize(40) 
        for autotext in autotexts:
            autotext.set_fontsize(40)
        
        ax.axis('equal')
        plt.title(title, fontsize=40)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return widgets.Image(value=buf.getvalue(), format='png', width=figsize[0]*25, height=figsize[1]*25)

    pcs = 15

    rows_pie_widget = create_pie_chart(selected_rows, total_rows, f"Selected interventions ({selected_rows} / {total_rows})", figsize=(pcs, pcs))
    holdings_pie_widget = create_pie_chart(selected_holdings, total_holdings, f"Selected holdings ({selected_holdings} / {total_holdings})", figsize=(pcs, pcs))

    # create a horizontal box to display the pie charts side by side
    hbox = widgets.HBox([rows_pie_widget, holdings_pie_widget], layout=widgets.Layout(justify_content='space-around'))

    bucket_stats_widget_list = []
    for bucket_id, info in datamanager.ua_groups.items():
        label = info["desc"]
        selected = info["selected"]
        total = info["count"]
        title_label = widgets.Label(value=label)
        if selected == info["target"]:
            title_label.add_class("green_label_bold")
            title_label.value += " (target reached)"
        else:
            title_label.add_class("orange_label_bold")
            title_label.value += f" (target not reached)"
        selected_label = widgets.Label(value=f"Selected: {selected} / {total} ({selected/total*100:.2f}%) Target: {info['target']}")
        bucket_pie_widget = create_pie_chart(selected, total, bucket_id, figsize=(10,10))
        vbox = widgets.VBox([title_label, selected_label, bucket_pie_widget], layout=widgets.Layout(padding="10px"))
        bucket_stats_widget_list.append(vbox)

    buckets_grid = widgets.GridBox(bucket_stats_widget_list, layout=widgets.Layout(grid_template_columns="repeat(3, 350px)", padding="10px"))
    
    vbox = widgets.VBox([hbox, buckets_grid], layout=widgets.Layout(padding="10px"))

    # a lot of this function is not used now, refactor
    display(buckets_grid)


def display_bucket_stats(datamanager):
    def create_fraction_bar(selected, total, title, figsize=(5, 1)):
        fig, ax = plt.subplots(figsize=figsize)
        
        fraction = selected / total
        ax.barh(0, fraction, height=0.5, color='#1daee3')
        ax.barh(0, 1-fraction, left=fraction, height=0.5, color='#DFDFDF')
        ax.set_xlim(0, 1)
        ax.set_yticks([])
        ax.set_xticks([])
        
        # Add labels
        ax.text(0.5, 0, f'{selected}/{total} ({fraction:.1%})', 
                ha='center', va='center', fontweight='bold', fontsize=18)
        
        #plt.title(title, fontsize=18, pad=20)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        plt.close(fig)
        return widgets.Image(value=buf.getvalue(), format='png', width=figsize[0]*50, height=figsize[1]*50)

    bucket_stats_widget_list = []
    for bucket_id, info in datamanager.ua_groups.items():
        label = info["desc"]
        selected = info["selected"]
        total = info["count"]
        title_label = widgets.Label(value=label, style={'font_size': '14px', 'font_weight': 'bold'})
        if selected == info["target"]:
            title_label.add_class("green_label_bold")
            title_label.value += " (target reached)"
        else:
            title_label.add_class("orange_label_bold")
            title_label.value += f" (target not reached)"
        selected_label = widgets.Label(value=f"Selected: {selected} / {total} ({selected/total*100:.2f}%) Target: {info['target']}", 
                                       style={'font_size': '14px'})
        bucket_widget = create_fraction_bar(selected, total, bucket_id)
        vbox = widgets.VBox([title_label, selected_label, bucket_widget], 
                            layout=widgets.Layout(padding="10px", align_items='center', width='300px'))
        bucket_stats_widget_list.append(vbox)

    buckets_grid = widgets.GridBox(bucket_stats_widget_list, 
                                   layout=widgets.Layout(grid_template_columns="repeat(3, 320px)", 
                                                         grid_gap='15px', 
                                                         padding="10px"))
    
    display(buckets_grid)