"""
Contains: DataManager class.
Responsibilities: Manages configuration and state, handles file loading, and updates parameters.
Imports: pandas for file operations and modules from input_verification.py for data validation.
"""


import pandas as pd


class DataManager:
    def __init__(self, parcels_path = "", targets_path = ""):
        self.parcels_path = parcels_path
        self.targets_path = targets_path
        self.ua_groups = {}
        # ua_group_dict[group] = {"target" : 300, "count" : ua_group_count[group], "desc" : create_ua_group_description(group, counter)}
        self.parcel_file_loaded = False
        self.target_values_state = "(Target values loaded from the parcel file.)"
        self.parcels_df = None
        self.target_source_label = None # Label that informs about the latest source of target values displayed
        self.param_3_percent = False
        self.holdings_reduced = False
        self.covered_priority = 0 # Prioritize parcels covered by HR images, Include only parcels covered by HR images
        self.covered_priority_dict = {"Do not prioritize parcels covered by HR images": 0, 
                                      "Prioritize parcels covered by HR images": 1, 
                                      "Include only parcels covered by HR images": 2}
        self.total_holding_count = 0
        self.holding_3_percent_count = 0
        
        self.final_bucket_state = None
