import io
from IPython.display import display, clear_output, HTML
import ipywidgets as widgets
import pandas as pd
import matplotlib.pyplot as plt
from ipyfilechooser import FileChooser

from modules.widget_builder import create_text_entry, create_button, create_info_button, create_int_entry, define_infobutton_style
from modules.input_verification import verify_target_df, compare_bucket_lists, verify_and_report_parcel_df


display(HTML(define_infobutton_style()))

def target_widgets_on_value_change(change, datamanager): # controls gui behavior - stays in gui.py
    datamanager.target_values_state = f"(Target values were manually modified. Last change: {change['owner'].description} field changed to {change['new']}.)"
    datamanager.target_source_label.value = datamanager.target_values_state
    get_target_values_from_widgets(datamanager.target_widgets_list, datamanager)

def limit_3perc_widget_on_value_change(change, datamanager):
    datamanager.param_3_percent = change["new"]

def image_coverage_widget_on_value_change(change, datamanager):
    datamanager.covered_priority = datamanager.covered_priority_dict[change["new"]]

def noncontributing_widget_on_value_change(change, datamanager):
    datamanager.noncontributing_filtering = datamanager.noncontributing_filtering_dict[change["new"]]

def extraction_id_widget_on_value_change(change, datamanager):
    datamanager.extraction_id = change["new"]

def get_group_id_based_on_widget_description(description, datamanager):
    for group, info in datamanager.ua_groups.items():
        if info["desc"] == description:
            return group

def get_target_values_from_widgets(widgets_list, datamanager): # controls gui behavior - stays in gui.py
    for widget_box in widgets_list:
        widget = widget_box.children[0]
        datamanager.ua_groups[get_group_id_based_on_widget_description(widget.description,datamanager)]["target"] = widget.value

def holding_level_button_switch(dm, button):
    if button.act:
        button.act = False
        button.style = {"button_color": "#d3d3d3"}
        dm.holding_level_interventions.remove(button.id)
    else:
        button.act = True
        button.style = {"button_color": "#ffdd00"}
        dm.holding_level_interventions.append(button.id)

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

        holding_level_button = widgets.Button(
            description="HL",
            #button_style="info",
            tooltip=f"Holding level intervention?",
            layout=widgets.Layout(width="40px"),
            style = {"button_color": "#d3d3d3"},
        )

        holding_level_button.act = False
        holding_level_button.id = group

        holding_level_button.on_click(lambda b: holding_level_button_switch(datamanager, b))

        group_box = widgets.HBox([entry, holding_level_button, count_label])

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


def get_ua_groups_from_parcel_file(parcels_df, mode="simple"):
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


    if mode == "ulm":
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
        print("\nDefault targets set based on the values recommended by the ULM.\n")

    # else:
    #     for group in ua_groups:
    #         count_for_group = ua_group_count[group]
    #         # print(f"{group}: {count_for_group} rows detected.")
    #         if count_for_group >= 6000:
    #             default_target = 300
    #         elif count_for_group >= 20:
    #             default_target = int(count_for_group * 0.05)
    #         else:
    #             default_target = 1
    #         ua_group_dict[group] = {"target" : default_target, "count" : ua_group_count[group], "desc" : create_ua_group_description(group, counter)}
    #         counter += 1
    #     print("\nDefault targets set to 5% of the total number of rows for each UA group (max 300).\n")

    else:
        for group in ua_groups:
            count_for_group = ua_group_count[group]
            if count_for_group <= 6000:
                default_target = round(count_for_group * 0.05)
            else:
                default_target = 300
        
            if default_target == 0:
                default_target = 1

            ua_group_dict[group] = {"target" : default_target, "count" : ua_group_count[group], "desc" : create_ua_group_description(group, counter)}
            counter += 1
    
    return ua_group_dict

def display_ua_grp_distribution_chart(ua_group_dict):
    
    # draw a simple bar chart to visualize the distribution of ua groups
    print(f"Detected {len(ua_group_dict)} unique UA groups:\n")
    fig = plt.figure(figsize=(10, 4))  # Reduced height from 5 to 3
    ax = fig.add_subplot(111)

    # count the number of rows for each ua group
    ua_group_count = {}
    for group, info in ua_group_dict.items():
        ua_group_count[info["desc"]] = info["count"]
    
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
    datamanager.target_values_state = "(Target values modified using the increase by percentage setting.)"
    datamanager.target_source_label.value = datamanager.target_values_state

    get_target_values_from_widgets(widgets_list, datamanager)


def load_parcel_file(entry_widget, output_area, datamanager):
    """
    Load parcel data from a file specified by the user, verify its structure, and update the UI accordingly.

    Args:
    entry_widget (ipywidgets.Text): Widget containing the file path to the parcel file.
    output_area (ipywidgets.Output): Widget used to display messages and file content.
    """
    datamanager.targets_displayed_and_set = False
    with output_area:
        clear_output()
        print("Verifying file. Please wait...\n")
        file_path = entry_widget.value 
        try:
            try:
                df = pd.read_csv(file_path, dtype={'gsa_par_id': str, 'gsa_hol_id': str, 'ua_grp_id': str})
            except KeyError:
                print("One of the following columns: 'gsa_par_id', 'gsa_hol_id' or 'ua_grp_id' not found in CSV file")

            verify_and_report_parcel_df(df)
            clear_output()
            datamanager.parcels_path = file_path
            ua_group_dict = get_ua_groups_from_parcel_file(df)
            print(len(ua_group_dict))
            display_ua_grp_distribution_chart(ua_group_dict)
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


def display_bucket_targets_config(datamanager, mode=""):
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

        if mode == "threshold":
            target_cutoff_info_button = create_info_button("This allows you to automatically limit all targets to a certain value (will only affect values above the defined cutoff).")
            target_cutoff_info_button.add_class("info-button-style")
            target_cutoff_entry = create_int_entry("Target cutoff:", "example: 300", 0, int(1e10), width="150px")
            target_perc_label = widgets.Label(value="")
            target_cutoff_recalculate_button = create_button("Recalculate", "info", "Click to recalculate target values")
            target_cutoff_recalculate_button.on_click(lambda b: recalculate_targets_based_on_threshold(target_cutoff_entry, widgets_list, datamanager))
        
        else:

            target_cutoff_info_button = create_info_button("This allows you to increase all targets by a given percentage.")
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
        datamanager.targets_displayed_and_set = True

def display_optional_parameters(datamanager):
    if not datamanager.parcel_file_loaded:
        print("Please load the parcel file first and run this cell again.")
    else:
        extraction_id_entry = create_text_entry("Extraction ID:", "", width='400px')
        extraction_id_entry.observe(lambda change: extraction_id_widget_on_value_change(change, datamanager), names='value')
        extraction_id_infobutton = create_info_button("Unique identifier for the extraction. Will be used to name the output files. If left empty, an ID will be generated automatically.")

        holding_percentage_active = widgets.Checkbox(value=False, description="Limit search to 3% of holdings", style={"description_width": "initial"})
        holding_percentage_active.observe(lambda change: limit_3perc_widget_on_value_change(change, datamanager), names='value')

        image_coverage_radiobuttons = widgets.RadioButtons(
            options=["Include all parcels in the sample extraction", 
                     "Prioritize parcels covered by VHR images (beta)", "Include only parcels covered by VHR images"],
            value="Include all parcels in the sample extraction",
            description="VHR image coverage options:",
            style={"description_width": "initial"}
        )
        image_coverage_radiobuttons.observe(lambda change: image_coverage_widget_on_value_change(change, datamanager), names='value')

        consider_noncontributing_radiobuttons = widgets.RadioButtons(
            options=["Filter out when a bucket is filled", 
                     "Retain when a bucket is filled"],
            value="Filter out when a bucket is filled",
            description="Non-contributing, highest-ranked parcel of a holding:",
            style={"description_width": "initial"}
        )
        consider_noncontributing_radiobuttons.observe(lambda change: noncontributing_widget_on_value_change(change, datamanager), names='value')

        hbox_prefix = widgets.HBox([extraction_id_entry, extraction_id_infobutton], layout=widgets.Layout(padding="10px"))
        hbox1 = widgets.HBox([holding_percentage_active], layout=widgets.Layout(padding="0px"))
        hbox2 = widgets.HBox([image_coverage_radiobuttons], layout=widgets.Layout(padding="12px"))
        hbox3 = widgets.HBox([consider_noncontributing_radiobuttons], layout=widgets.Layout(padding="12px"))
        vbox = widgets.VBox([hbox_prefix, hbox1, hbox2, hbox3], layout=widgets.Layout(padding="10px"))
        #vbox = widgets.VBox([hbox1, hbox2], layout=widgets.Layout(padding="10px"))
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


