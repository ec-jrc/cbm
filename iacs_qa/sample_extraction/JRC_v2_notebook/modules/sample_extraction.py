import os

import pandas as pd
import datetime
from modules import gui


def prepare_input_dataframe(datamanager):
    parcel_df = datamanager.parcels_df

    # get number of unique gsa_hol_id values:
    datamanager.total_holding_count = len(parcel_df["gsa_hol_id"].unique())
    print("Total holding count: ", datamanager.total_holding_count)

    # calculate 3% of total holdings, round down
    datamanager.holding_3_percent_count = int(datamanager.total_holding_count * 0.03)


    if datamanager.covered_priority == 2:
        parcel_df = parcel_df[parcel_df["covered"] == 1]
    # parcel_df = parcel_df[parcel_df["covered"] == 1]
    # Sort the dataframe by the 'ranking' column
    parcel_df = parcel_df.sort_values(by="ranking")

    # Create a 'row_id' by concatenating the string representations of several columns row-wise
    parcel_df["row_id"] = parcel_df.apply(lambda row: f"{row['gsa_par_id']}_{row['gsa_hol_id']}_{row['ua_grp_id']}", axis=1)

    # Initialize 'order_added' column to 0
    parcel_df["order_added"] = 0

    return parcel_df

def buckets_global_count(buckets):
    """
    Returns a number of rows already added to all buckets together
    """
    return sum([len(bucket['parcels']) for bucket in buckets.values()])


def prepare_buckets(ua_groups_dict):
    # PARAMETERS["ua_groups"][group] = {"target" : 300, "count" : ua_group_count[group]}
    buckets = {}
    for group_id, info in ua_groups_dict.items():
        target = info["target"]
        buckets[group_id] = {'target': target, 'parcels': []}
    return buckets

def generate_output(buckets):
    """
    Generates an output xlsx file with the following columns:
    - bucket_id
    - gsa_par_id
    - gsa_hol_id
    - ranking
    - target
    """
    output_dir = "output"
    # check if exists, if not create
    try:
        os.makedirs(output_dir)
    except FileExistsError:
        pass

    output = []
    for bucket_id, bucket in buckets.items():
        for parcel in bucket['parcels']:
            output.append([bucket_id, parcel["gsa_par_id"], parcel["gsa_hol_id"], parcel["ranking"], parcel["order_added"]])#, bucket['target']])
    output_df = pd.DataFrame(output, columns=["bucket_id", "gsa_par_id", "gsa_hol_id", "ranking", "order_added"])#, "target"])

    filename_excel = "sample_extraction_output_" + datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".xlsx"
    output_df.to_excel(os.path.join(output_dir, filename_excel), index=False)

    filename_csv = "sample_extraction_output_" + datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".csv"
    output_df.to_csv(os.path.join(output_dir, filename_csv), index=False)

# -----




def buckets_full(buckets):
    """
    Returns True if all buckets are full, False otherwise
    """
    return all(len(bucket['parcels']) >= bucket['target'] for bucket in buckets.values())

def get_full_bucket_ids(buckets):
    """
    Returns a list of bucket IDs that are full
    
    """
    return [bucket_id for bucket_id, bucket in buckets.items() if len(bucket['parcels']) >= bucket['target']]

def reduce_parcel_dataframe(parcel_df, full_bucket_id):
    """
    removes all rows from the dataframe where ua_grp_id equals the full_bucket value
    """
    return parcel_df[parcel_df["ua_grp_id"] != full_bucket_id]


def all_buckets_used_3_times(bucket_counter):
    """
    Returns True if all buckets have been used 3 times, False otherwise.
    """
    return all(value == 3 for value in bucket_counter.values())

def check_holding_group(holding_group, buckets, added_rows, added_holdings):
    """
    New version that adds parcels the right (?) way.
    """
    # create a dictionary that has the same keys as buckets, but the values are just zeros
    bucket_counter = {key: 0 for key in buckets.keys()}
    for index, holding_row in holding_group.iterrows():
        if buckets_full(buckets) or all_buckets_used_3_times(bucket_counter):
            break
        parcel_group = holding_group[holding_group["gsa_par_id"] == holding_row["gsa_par_id"]]
        buckets, bucket_counter, added_rows, added_holdings = check_parcel(parcel_group, buckets, added_rows, added_holdings, bucket_counter)

    return buckets, added_rows, added_holdings


def check_parcel(parcel_group, buckets, added_rows, added_holdings, bucket_counter=None):
    for index, parcel_row in parcel_group.iterrows():
        if buckets_full(buckets):
            break
        for bucket_id, bucket in buckets.items():
                if parcel_row["ua_grp_id"] == bucket_id and len(bucket['parcels']) < bucket['target'] and parcel_row["row_id"] not in added_rows:
                    if bucket_counter == None or bucket_counter[bucket_id] < 3:
                        bucket['parcels'].append({"gsa_par_id": parcel_row["gsa_par_id"],
                                                "gsa_hol_id": parcel_row["gsa_hol_id"],
                                                "ranking": parcel_row["ranking"],
                                                "order_added" : buckets_global_count(buckets)+1,
                                                })
                        added_rows.add(parcel_row["row_id"])
                        if parcel_row["gsa_hol_id"] not in added_holdings:
                            added_holdings.add(parcel_row["gsa_hol_id"])
                            #print("Added holdings:",len(added_holdings))
                        if bucket_counter != None:
                            bucket_counter[bucket_id] += 1
    
    return buckets, bucket_counter, added_rows, added_holdings

def reduce_holdings(parcel_df, added_holdings):
    # removes all rows from the dataframe where gsa_hol_id is not one of the checked_holdings
    return parcel_df[parcel_df["gsa_hol_id"].isin(added_holdings)]


def iterate_over_interventions(parcel_df, buckets, progress_widgets): #, progress_bars):
    """
    Main loop of the script.
    Iterates over the rows in the interventions dataframe and adds parcels to the buckets.
    """

    #print("Buckets: (\033[92mgreen\033[0m = full, \033[93myellow\033[0m = still looking for parcels)")

    checked_holdings = set()
    added_rows = set()
    for index, row in parcel_df.iterrows():
        
        if buckets_full(buckets):
            break
        if row["gsa_hol_id"] not in checked_holdings:
            checked_holdings.add(row["gsa_hol_id"])
            holding_group = parcel_df[parcel_df["gsa_hol_id"] == row["gsa_hol_id"]]
            buckets = check_holding_group(holding_group, buckets, added_rows)
        else:
            parcel_group = parcel_df[parcel_df["gsa_par_id"] == row["gsa_par_id"]]
            buckets, bucket_counter = check_parcel(parcel_group, buckets, added_rows)

        if index % 20 == 0:
            gui.update_output_area(buckets, progress_widgets)

    gui.update_output_area(buckets, progress_widgets)
    return buckets

def intervention_loop(parcel_df, buckets, progress_widgets, checked_holdings, added_rows, added_holdings, full_buckets, dm):

    for index, row in parcel_df.iterrows():
        if buckets_full(buckets):
            break
        if row["gsa_hol_id"] not in checked_holdings:
            checked_holdings.add(row["gsa_hol_id"])
            holding_group = parcel_df[parcel_df["gsa_hol_id"] == row["gsa_hol_id"]]
            buckets, added_rows, added_holdings = check_holding_group(holding_group, buckets, added_rows, added_holdings)
        else:
            parcel_group = parcel_df[parcel_df["gsa_par_id"] == row["gsa_par_id"]]
            buckets, bucket_counter, added_rows, added_holdings = check_parcel(parcel_group, buckets, added_rows, added_holdings)
            
        if index % 20 == 0:
            gui.update_output_area(buckets, progress_widgets)

        new_full_buckets = get_full_bucket_ids(buckets)
        holding_threshold_exceeded = False

        if dm.param_3_percent and len(added_holdings) >= dm.holding_3_percent_count:
            holding_threshold_exceeded = True
            dm.param_3_percent = False # to make sure the holding reduction only happens once

        if len(new_full_buckets) != len(full_buckets):
            # new_full_bucket must be the extra element in new buckets compared to previous full bucket list
            new_full_bucket = list(set(new_full_buckets) - set(full_buckets))[0]
        else:
            new_full_bucket = ""
        
        if new_full_bucket != "" or holding_threshold_exceeded: # this is always true after the first time it's true. this resets the lopp indefinitely
            return buckets, new_full_bucket, holding_threshold_exceeded, added_holdings, False


    gui.update_output_area(buckets, progress_widgets)
    return buckets, new_full_bucket, holding_threshold_exceeded, added_holdings, True

def iterate_over_interventions_fast(parcel_df, buckets, progress_widgets, dm):
    """
    Main loop of the script.
    Iterates over the rows in the interventions dataframe and adds parcels to the buckets.
    """

    #print("Buckets: (\033[92mgreen\033[0m = full, \033[93myellow\033[0m = still looking for parcels)")

    checked_holdings = set()
    added_rows = set()
    added_holdings = set()
    full_buckets = []
    all_checked = False
    while not buckets_full(buckets) and not all_checked:
        buckets, new_full_bucket, holding_threshold_exceeded, added_holdings, all_checked = intervention_loop(parcel_df, buckets, progress_widgets, checked_holdings, added_rows, added_holdings, full_buckets, dm)
        if new_full_bucket != "":
            full_buckets.append(new_full_bucket)
            parcel_df = reduce_parcel_dataframe(parcel_df, new_full_bucket)
        if holding_threshold_exceeded:
            parcel_df = reduce_holdings(parcel_df, added_holdings)

    gui.update_output_area(buckets, progress_widgets)
    dm.final_bucket_state = buckets
    return buckets





    