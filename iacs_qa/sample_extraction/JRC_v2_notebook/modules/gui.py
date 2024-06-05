import io
from IPython.display import display, clear_output, HTML
import ipywidgets as widgets
import pandas as pd
import matplotlib.pyplot as plt

from modules.widget_builder import create_text_entry, create_button, create_info_button, create_int_entry, define_infobutton_style
from modules.input_verification import verify_parcel_df, verify_target_df, compare_bucket_lists

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
    for group in ua_groups:
        count_for_group = ua_group_count[group]
        print(group, count_for_group)
        if count_for_group >= 6000:
            default_target = 300
        else:
            default_target = int(count_for_group * 0.05)
        ua_group_dict[group] = {"target" : default_target, "count" : ua_group_count[group], "desc" : create_ua_group_description(group, counter)}
        counter += 1
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
            populate_target_values(df, widgets_list, datamanager)
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
        grid = widgets.GridBox(widgets_list, layout=widgets.Layout(grid_template_columns="repeat(3, 350px)", padding="10px"))
        hbox1 = widgets.HBox([target_file_path_entry, target_file_load_button,target_info_button], layout=widgets.Layout(padding="10px"))
        hbox2 = widgets.HBox([target_cutoff_entry, target_cutoff_recalculate_button, target_cutoff_info_button], layout=widgets.Layout(padding="10px"))
        vbox = widgets.VBox([hbox0, grid, hbox1, hbox2, output_area])
        display(vbox)

def display_advanced_parameters(datamanager):
    holding_percentage_active = widgets.Checkbox(value=False, description="Limit search to 3% of holdings", style={"description_width": "initial"})
    holding_percentage_active.observe(lambda change: limit_3perc_widget_on_value_change(change, datamanager), names='value')

    image_coverage_radiobuttons = widgets.RadioButtons(
        options=["Include all parcels in the sample extraction", "Include only parcels covered by HR images"],
        value="Include all parcels in the sample extraction",
        description="HR image coverage options:",
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

    display(HTML("<style>.orange_label { color:orange }</style>"))
    display(HTML("<style>.orange_label_bold { color:orange; font-weight: bold }</style>"))

    display(HTML("<style>.green_label_bold { color:green; font-weight: bold }</style>"))
    display(HTML("<style>.green_label { color:green }</style>"))



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

def display_result_statistics(datamanager):
    total_rows = len(datamanager.parcels_df)
    selected_rows = sum([len(bucket['parcels']) for bucket in datamanager.final_bucket_state.values()])
    total_holdings = len(datamanager.parcels_df["gsa_hol_id"].unique())
    selected_holdings = len(datamanager.added_holdings)

    all_buckets_full = all([bucket["target"] == len(bucket["parcels"]) for bucket in datamanager.final_bucket_state.values()])
    if all_buckets_full:
        first_row_label = widgets.Label(value="All buckets are full!")
        first_row_label.add_class("green_label_bold")
    else:
        first_row_label = widgets.Label(value="Not all buckets are full. See progress indicators for details.")
        first_row_label.add_class("orange_label_bold")

    second_row_label = widgets.Label(value=f"Selected rows: {selected_rows} / {total_rows} ({selected_rows / total_rows:.2%})")

    third_row_label = widgets.Label(value=f"Selected holdings: {selected_holdings} / {total_holdings} ({selected_holdings / total_holdings:.2%})")

    vbox = widgets.VBox([first_row_label, second_row_label, third_row_label], layout=widgets.Layout(padding="10px"))
    display(vbox)
    
def display_stats_test():
    import ipywidgets as widgets
    from IPython.display import display
    import matplotlib.pyplot as plt
    import io
    from PIL import Image

    def display_result_statistics(datamanager):
        # total statistic (top)
        total_rows = len(datamanager.parcels_df)
        selected_rows = sum([len(bucket['parcels']) for bucket in datamanager.final_bucket_state.values()])
        total_holdings = len(datamanager.parcels_df["gsa_hol_id"].unique())
        selected_holdings = len(datamanager.added_holdings)

        # Pie chart for selected rows
        def create_pie_chart(selected, total, title):
            fig, ax = plt.subplots()
            sizes = [selected, total - selected]
            labels = ['Selected', 'Not Selected']
            colors = ['#ff9999','#66b3ff']
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            plt.title(title)
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            return Image.open(buf)
        
        rows_pie = create_pie_chart(selected_rows, total_rows, "Selected Rows")
        holdings_pie = create_pie_chart(selected_holdings, total_holdings, "Selected Holdings")

        rows_pie_widget = widgets.Image(value=rows_pie.tobytes(), format='png', width=200, height=200)
        holdings_pie_widget = widgets.Image(value=holdings_pie.tobytes(), format='png', width=200, height=200)

        # first row
        all_buckets_full = all([bucket["target"] == len(bucket["parcels"]) for bucket in datamanager.final_bucket_state.values()])
        if all_buckets_full:
            first_row_label = widgets.Label(value="All buckets are full!")
            first_row_label.add_class("green_label_bold")
        else:
            first_row_label = widgets.Label(value="Not all buckets are full. See progress indicators for details.")
            first_row_label.add_class("orange_label_bold")

        # Create the layout
        pie_charts_box = widgets.HBox([rows_pie_widget, holdings_pie_widget], layout=widgets.Layout(justify_content='space-around'))
        vbox = widgets.VBox([first_row_label, pie_charts_box], layout=widgets.Layout(padding="10px"))
        display(vbox)

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

def display_statistics_summary(datamanager):
    total_rows = len(datamanager.parcels_df)
    selected_rows = sum([len(bucket['parcels']) for bucket in datamanager.final_bucket_state.values()])
    total_holdings = len(datamanager.parcels_df["gsa_hol_id"].unique())
    selected_holdings = len(datamanager.added_holdings)
    avg_int_per_holding = selected_rows / selected_holdings
    most_interventions = calculate_holding_with_most_interventions_selected(datamanager)

    all_buckets_full = all([bucket["target"] == len(bucket["parcels"]) for bucket in datamanager.final_bucket_state.values()])
    if all_buckets_full:
        first_row_label = widgets.Label(value="All buckets are full!")
        first_row_label.add_class("green_label_bold")
    else:
        first_row_label = widgets.Label(value="Not all buckets are full. See progress indicators for details.")
        first_row_label.add_class("orange_label_bold")

    second_row_label = widgets.Label(value=f"Selected interventions: {selected_rows} / {total_rows} ({selected_rows/total_rows*100:.2f}%)")

    third_row_label = widgets.Label(value=f"Selected holdings: {selected_holdings} / {total_holdings} ({selected_holdings/total_holdings*100:.2f}%)")

    fourth_row_label = widgets.Label(value=f"Average selected interventions per selected holding: {avg_int_per_holding:.2f}")

    fifth_row_label = widgets.Label(value=f"Holding with most interventions selected: {most_interventions[0]} ({most_interventions[1]} interventions)")

    vbox = widgets.VBox([first_row_label, second_row_label, third_row_label, fourth_row_label, fifth_row_label], layout=widgets.Layout(padding="10px"))

    display(vbox)



def display_pie_charts(datamanager):
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
    display(vbox)