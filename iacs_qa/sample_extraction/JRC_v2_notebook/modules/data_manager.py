import pandas as pd


class DataManager:
    def __init__(self, parcels_path = "", targets_path = ""):
        self.parcels_path = parcels_path
        self.targets_path = targets_path
        self.ua_groups = {}
        # ua_group_dict[group] = {"target" : 300, "count" : ua_group_count[group], "desc" : create_ua_group_description(group, counter)}
        self.parcel_file_loaded = False
        self.targets_displayed_and_set = False
        self.target_values_state = "(Target values loaded from the parcel file.)"
        self.parcels_df = None
        self.target_source_label = None # Label that informs about the latest source of target values displayed
        self.param_3_percent = False
        self.holdings_reduced = False
        self.covered_priority = 0 # Prioritize parcels covered by HR images, Include only parcels covered by HR images
        self.covered_priority_dict = {"Include all parcels in the sample extraction": 0, 
                                      "Prioritize parcels covered by VHR images (beta)": 1, 
                                      "Include only parcels covered by VHR images": 2}
        self.total_holding_count = 0
        self.holding_3_percent_count = 0
        
        self.extraction_id = ""
        
        self.final_bucket_state = None

        self.holding_level_interventions = []
