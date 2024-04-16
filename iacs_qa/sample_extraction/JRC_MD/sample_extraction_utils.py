import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import pandas as pd


PARAMETERS = {"parcels_path": ""}

STYLE = {'description_width': 'initial'}

# INFO_STYLE = widgets.ButtonStyle(
#     button_color='none',  # Makes the background transparent
#     border='none'         # Removes the border
# )


def verify_parcel_df(parcel_df):
    pass

def verify_target_df(target_df):
    pass

# >>> df2["ua_grp"].unique()
# array(['E5', 'ANC', 'BIS', 'ES2', 'E3', 'C5', 'SFS', 'YFS', 'C1', 'C3',
#        'E7B', 'E4', 'CIS: LA', 'C6C', 'C4', 'E1C', 'C2B', 'ES1', 'ME2',
#        'E2', 'E7A'], dtype=object)



def display_bucket_targets_config():
    style_html = """
<style>
    .custom-button-style {
        border-radius: 50%;  /* Makes the button circular */
    }
    .custom-button-style:hover {
        box-shadow: none !important;  /* Removes shadow on hover */
        transform: none !important;  /* Stops any popping or scaling */
        cursor: default;  /* Removes the hand cursor */
    }
</style>
"""
    display(HTML(style_html))



    threshold_info_button = widgets.Button(
        icon="info",
        layout = widgets.Layout(width='30px'),
        #style={"button_color": "white"}
        button_style = "",
        tooltip="""You can either provide the target values manually using the fields below, or load the values from a CSV file.
In order to load the file, use the 'Bucket targets file path' field to provide the path to the CSV file and click 'Load'.
Values loaded from a file can also be edited manually after loading.
In addition, you can set a maximum threshold value that will reduce the value for all the targets above the defined threhsold."""
    )

    threshold_info_button.add_class("custom-button-style")

    threshold_file_path_entry = widgets.Combobox(
        placeholder='example: input/targets.csv',
        description='Bucket targets file path:',
        ensure_option=False,
        disabled=False,
        style=STYLE,
    )

    threshold_file_load_button = widgets.Button(
        description="Load",
        button_style="info",
        tooltip="Click to pre-populate threshold values",
        style={"button_color": "#1daee3ff"}
    )

    valid_targets_widget = widgets.Valid(
    value=True,
    description="",
    layout=widgets.Layout(display='none')
    )

    ua_groups = {'YFS': 1, 
                            'SFS': 2, 
                            'ME2': 3, 
                            'ES2': 4, 
                            'ES1': 5, 
                            'E7B': 6, 
                            'E7A': 7, 
                            'E5': 8, 
                            'E4': 9, 
                            'E3': 10, 
                            'E2': 11, 
                            'E1C': 12, 
                            'CIS: LA': 13, 
                            "???" : 14, 
                            'C6C': 15, 
                            'C5': 16, 
                            'C4': 17, 
                            'C3': 18, 
                            'C2B': 19, 
                            'C1': 20, 
                            'BIS': 21, 
                            'ANC': 22}

    # Create widgets for each dictionary entry
    widgets_list = []
    for key, value in ua_groups.items():
        label = f"{key} (id: {value})"
        entry = widgets.BoundedIntText(value=0, min=0, max=99999999999999, description=label, layout=widgets.Layout(width='150px'))
        widgets_list.append(entry)

    output_area = widgets.Output()

    def populate_threshold_values(threshold_df, widgets_list):
        for index, row in threshold_df.iterrows():
            ua_group = row['ua_grp_id']
            target = row['target1']
            if ua_group in ua_groups.values():
                widgets_list[ua_group - 1].value = target

    def load_threshold_file(b, entry_widget, button_widget):
        file_path = entry_widget.value
        try:
            df = pd.read_csv(file_path)
            with output_area:
                clear_output()
                print("File loaded successfully. Fields populated. \n")
                print(df.head())
                populate_threshold_values(df, widgets_list)
            valid_targets_widget.value = True
            valid_targets_widget.layout.display = ''
            PARAMETERS['targets_path'] = file_path
        except Exception as e:
            with output_area:
                clear_output()
                print(f"Error loading file: {e}\n")
                print("Correct the path or file format and load again.")
                print("You can also populate the values below manually instead of loading a CSV file.")
            valid_targets_widget.value = False
            valid_targets_widget.layout.display = ''
            PARAMETERS['targets_path'] = ""

    threshold_file_load_button.on_click(lambda b: load_threshold_file(b, threshold_file_path_entry, threshold_file_load_button))

    # Organize widgets into a grid layout
    hbox1 = widgets.HBox([threshold_info_button, threshold_file_path_entry, threshold_file_load_button, valid_targets_widget])
    hbox1.layout.border = '1px solid #1daee3ff'
    grid = widgets.GridBox(widgets_list, layout=widgets.Layout(grid_template_columns="repeat(4, 200px)"))
    hbox2 = widgets.HBox([output_area])
    hbox2.layout.border = '1px solid #1daee3ff'
    hbox3 = widgets.HBox([grid])
    hbox3.layout.border = '1px solid #1daee3ff'
    vbox = widgets.VBox([hbox1, hbox2, hbox3])
    vbox.layout.border = '1px solid #1daee3ff'
    display(vbox)


def display_parcel_input_config():
    parcel_file_path_entry = widgets.Combobox(
        placeholder='example: input/parcels.csv',
        description='Parcel file path:',
        ensure_option=False,
        disabled=False,
        style=STYLE,
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
    layout=widgets.Layout(display='none')
    )

    output_area = widgets.Output()

    def load_file(b, entry_widget, button_widget):
        file_path = entry_widget.value
        try:
            df = pd.read_csv(file_path)
            with output_area:
                clear_output()
                print("File loaded successfully. Preview: \n")
                print(df.head())
            valid_parcels_widget.value = True
            valid_parcels_widget.layout.display = ''
            PARAMETERS['parcels_path'] = file_path
        except Exception as e:
            with output_area:
                clear_output()
                print(f"Error loading file: {e}\n")
                print("Correct the path or file format and load again.")
            valid_parcels_widget.value = False
            valid_parcels_widget.layout.display = ''
            PARAMETERS['parcels_path'] = ""

    parcel_file_load_button.on_click(lambda b: load_file(b, parcel_file_path_entry, parcel_file_load_button))

    hbox = widgets.HBox([parcel_file_path_entry, parcel_file_load_button, valid_parcels_widget])
    vbox = widgets.VBox([hbox, output_area])
    display(vbox)

    #return df



# def display_input_config_():
#     # entry field to provide text input
#     style = {'description_width': 'initial'}

#     # First set of widgets
#     parcel_file_path_entry = widgets.Combobox(
#         placeholder='example: input/parcels.csv',
#         description='Parcel file path:',
#         ensure_option=False,
#         disabled=False,
#         style=style,
#     )

#     parcel_file_load_button = widgets.Button(
#         description="Load",
#         button_style="info",
#         tooltip="Click to_load
#  parcel file",
#         style={"button_color": "#1daee3ff"}
#     )

#     # Second set of widgets, initially not displayed
#     second_file_path_entry = widgets.Combobox(
#         placeholder='example: input/second.csv',
#         description='Second file path:',
#         ensure_option=False,
#         disabled=True,  # Disabled initially
#         style=style,
#     )

#     second_file_load_button = widgets.Button(
#         description="Load",
#         button_style="info",
#         tooltip="Click to_load
#  second file",
#         style={"button_color": "#1daee3ff"},
#         disabled=True  # Disabled initially
#     )

#     output_area = widgets.Output()
    
#     # Checkbox to control the display of the second set of widgets
#     enable_second_set = widgets.Checkbox(
#         value=False,
#         description='Enable second file loading',
#         disabled=False
#     )

#     second_widgets_container = widgets.VBox([second_file_path_entry, second_file_load_button])
#     second_widgets_container.layout.display = 'none'  # Hide initially

#     def load_file(b, entry_widget, button_widget):
#         file_path = entry_widget.value
#         try:
#             df = pd.read_csv(file_path)
#             with output_area:
#                 clear_output()
#                 print(df.head())
#             button_widget.description = 'File OK (load again?)'
#             button_widget.style.button_color = 'green'
#         except Exception as e:
#             with output_area:
#                 clear_output()
#                 print(f"Error loading file: {e}")
#             button_widget.description = 'Load again'
#             button_widget.style.button_color = "#1daee3ff"

#     def toggle_second_set(change):
#         if change.new:
#             second_widgets_container.layout.display = 'flex'  # Show widgets
#             second_file_path_entry.disabled = False
#             second_file_load
#     _button.disabled = False
#         else:
#             second_widgets_container.layout.display = 'none'  # Hide widgets
#             second_file_path_entry.disabled = True
#             second_file_load
#     _button.disabled = True

#     enable_second_set.observe(toggle_second_set, names='value')

#     parcel_file_load_button.on_click(lambda b: load_file(b, parcel_file_path_entry, parcel_file_load_button))
#     second_file_load_button.on_click(lambda b: load_file(b, second_file_path_entry, second_file_load_button))

#     hbox1 = widgets.HBox([parcel_file_path_entry, parcel_file_load_button])
#     vbox = widgets.VBox([hbox1, enable_second_set, second_widgets_container, output_area])
#     display(vbox)