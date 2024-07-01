import os
import datetime
import pandas as pd
from modules import gui

import warnings

warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

LOG_PATH = "log.txt"
log = open(LOG_PATH, "w")


def prepare_input_dataframe(datamanager):
    print(f"Preprocessing the parcel list... ({len(datamanager.parcels_df)} rows.)")
    parcel_df = datamanager.parcels_df
    datamanager.total_holding_count = len(parcel_df["gsa_hol_id"].unique())
    datamanager.holding_3_percent_count = int(datamanager.total_holding_count * 0.03)

    if datamanager.covered_priority == 2:
        parcel_df = parcel_df[parcel_df["covered"] == 1]
    parcel_df = parcel_df.sort_values(by="ranking")
    parcel_df["row_id"] = parcel_df.apply(lambda row: f"{row['gsa_par_id']}_{row['gsa_hol_id']}_{row['ua_grp_id']}", axis=1)
    parcel_df["order_added"] = 0

    return parcel_df


def buckets_global_count(buckets):
    """
    Returns a number of rows already added to all buckets together
    """
    return sum([len(bucket['parcels']) for bucket in buckets.values()])


def prepare_buckets(ua_groups_dict):
    """
    Prepares a dictionary of buckets with the following structure:
    {group_id: {'target': 300, 'parcels': []}}
    """
    print("Preparing buckets...")
    return {group_id: {'target': info["target"], 'parcels': []} for group_id, info in ua_groups_dict.items()}


def generate_output(buckets, debug=False):
    """
    Generates xlsx and csv files with the following columns:
    - bucket_id
    - gsa_par_id
    - gsa_hol_id
    - ranking
    - covered
    - order_added
    - phase (if debug=True)
    """
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    parcel_columns = ["gsa_par_id", "gsa_hol_id", "ranking", "covered", "order_added"]#, "phase"]
    if debug:
        parcel_columns.append("phase")

    output = []
    for bucket_id, bucket in buckets.items():
        for parcel in bucket['parcels']:
            output.append([bucket_id] + [parcel[column] for column in parcel_columns])
    
    output_df = pd.DataFrame(output, columns=["bucket_id"] + parcel_columns)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

    output_path_excel = os.path.join(output_dir, f"sample_extraction_output_{timestamp}.xlsx")
    output_path_csv = os.path.join(output_dir, f"sample_extraction_output_{timestamp}.csv")

    output_df.to_excel(output_path_excel, index=False)
    output_df.to_csv(output_path_csv, index=False)

    return output_path_excel, output_path_csv


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


def count_holding_occurrences_in_bucket(holding_id, bucket):
    return sum(1 for parcel in bucket["parcels"] if parcel["gsa_hol_id"] == holding_id)


def check_holding_group(holding_group, buckets, added_rows, added_holdings, covered_priority=0):
    bucket_counter = {key: 0 for key in buckets.keys()}
    if covered_priority == 1:
        for b in buckets:
            bucket_counter[b] = count_holding_occurrences_in_bucket(holding_group["gsa_hol_id"].iloc[0], buckets[b])
    for _, holding_row in holding_group.iterrows():
        if buckets_full(buckets) or all_buckets_used_3_times(bucket_counter):
            break
        parcel_group = holding_group[holding_group["gsa_par_id"] == holding_row["gsa_par_id"]]
        buckets, bucket_counter, added_rows, added_holdings = check_parcel(parcel_group, buckets, added_rows, added_holdings, bucket_counter)

    return buckets, added_rows, added_holdings


def check_parcel(parcel_group, buckets, added_rows, added_holdings, bucket_counter=None):
    for _, parcel_row in parcel_group.iterrows():
        if buckets_full(buckets):
            break
        for bucket_id, bucket in buckets.items():
                if parcel_row["ua_grp_id"] == bucket_id and len(bucket['parcels']) < bucket['target'] and parcel_row["row_id"] not in added_rows:
                    if bucket_counter == None or bucket_counter[bucket_id] < 3:
                        bucket['parcels'].append({"gsa_par_id": parcel_row["gsa_par_id"],
                                                "gsa_hol_id": parcel_row["gsa_hol_id"],
                                                "ranking": parcel_row["ranking"],
                                                "covered": parcel_row["covered"],
                                                "order_added" : buckets_global_count(buckets) + 1,
                                                "phase" : parcel_row["phase"],
                                                })
                        added_rows.add(parcel_row["row_id"])
                        if parcel_row["gsa_hol_id"] not in added_holdings:
                            added_holdings.add(parcel_row["gsa_hol_id"])
                        if bucket_counter != None:
                            bucket_counter[bucket_id] += 1
    
    return buckets, bucket_counter, added_rows, added_holdings


def reduce_holdings(parcel_df, added_holdings):
    """
    Returns two dataframes: one with holdings that are in added_holdings and one with the rest of holdings.
    """
    return parcel_df[parcel_df["gsa_hol_id"].isin(added_holdings)], parcel_df[~parcel_df["gsa_hol_id"].isin(added_holdings)]


def intervention_loop(parcel_df, buckets, progress_widgets, checked_holdings, added_rows, added_holdings, full_buckets, dm):
    new_full_bucket = ""
    holding_threshold_exceeded = False
    counter_for_refreshing = 0
    for index, row in parcel_df.iterrows():
        if buckets_full(buckets):
            break
        if row["gsa_hol_id"] not in checked_holdings:
            checked_holdings.add(row["gsa_hol_id"])
            holding_group = parcel_df[parcel_df["gsa_hol_id"] == row["gsa_hol_id"]]
            buckets, added_rows, added_holdings = check_holding_group(holding_group, buckets, added_rows, added_holdings, dm.covered_priority)
        else:
            parcel_group = parcel_df[parcel_df["gsa_par_id"] == row["gsa_par_id"]]
            buckets, _, added_rows, added_holdings = check_parcel(parcel_group, buckets, added_rows, added_holdings)
            
        if counter_for_refreshing % 2 == 0:
            gui.update_output_area(buckets, progress_widgets)
            # print(f"Progress: {counter_for_refreshing}/{len(parcel_df)} | Phase: {row['phase']} | Added holdings: {len(added_holdings)} | Added rows: {len(added_rows)}")
            # log.write(f"Progress: {counter_for_refreshing}/{len(parcel_df)} | Phase: {row['phase']} | Added holdings: {len(added_holdings)} | Added rows: {len(added_rows)}")

        new_full_buckets = get_full_bucket_ids(buckets)
        holding_threshold_exceeded = False

        if dm.param_3_percent and len(added_holdings) >= dm.holding_3_percent_count and not dm.holdings_reduced:
            holding_threshold_exceeded = True
            dm.holdings_reduced = True # to make sure the holding reduction only happens once
 
        if len(new_full_buckets) != len(full_buckets):
            # new_full_bucket must be the extra element in new buckets compared to previous full bucket list
            new_full_bucket = list(set(new_full_buckets) - set(full_buckets))[0]
        
        if new_full_bucket != "" or holding_threshold_exceeded:
            return buckets, new_full_bucket, holding_threshold_exceeded, added_holdings, False
        counter_for_refreshing += 1

    gui.update_output_area(buckets, progress_widgets)
    return buckets, new_full_bucket, holding_threshold_exceeded, added_holdings, True

def find_one_and_finish(parcel_df, buckets, progress_widgets, added_rows, dm):
    # for each bucket that is empty, find the first parcel that fits and add it
    # finish when each bucket has at least one parcel
    # REMEMEBER ABOUT TARGET!
    for bucket_id, bucket in buckets.items():
        if len(bucket['parcels']) == 0:
            for _, row in parcel_df.iterrows():
                if row["ua_grp_id"] == bucket_id and row["row_id"] not in added_rows:
                    bucket['parcels'].append({"gsa_par_id": row["gsa_par_id"],
                                            "gsa_hol_id": row["gsa_hol_id"],
                                            "ranking": row["ranking"],
                                            "covered": row["covered"],
                                            "order_added" : buckets_global_count(buckets)+1,
                                            "phase" : row["phase"],
                                            })
                    added_rows.add(row["row_id"])
                    gui.update_output_area(buckets, progress_widgets)
                    break
    return buckets
    
def some_buckets_empty(buckets):
    return any(len(bucket['parcels']) == 0 and bucket['target'] > 0 for bucket in buckets.values())

def divide_into_covered_and_non_covered(parcel_df):
    covered = parcel_df[parcel_df["covered"] == 1]
    non_covered = parcel_df[parcel_df["covered"] == 0]
    return covered, non_covered

def set_phase(dataframe, phase_value):
    # add column called "phase" to dataframe, and set all values to phase_value
    dataframe["phase"] = phase_value
    return dataframe

def iterate_over_interventions_fast(parcel_df, buckets, progress_widgets, dm):
    """
    Main loop of the script.
    Iterates over the rows in the interventions dataframe and adds parcels to the buckets.

    This currently desperately needs refactoring. A lot of code blocks are repeated.
    """
    checked_holdings = set()
    added_rows = set()
    added_holdings = set()
    full_buckets = []
    all_checked = False
    dm.holdings_reduced = False

    if dm.covered_priority == 1:
        covered, non_covered = divide_into_covered_and_non_covered(parcel_df)
        parcel_df = covered

    while not buckets_full(buckets) and not all_checked:
        parcel_df = set_phase(parcel_df, "first loop")
        buckets, new_full_bucket, holding_threshold_exceeded, added_holdings, all_checked = intervention_loop(parcel_df, buckets, progress_widgets, checked_holdings, added_rows, added_holdings, full_buckets, dm)
        if new_full_bucket != "":
            # remove rows associated with a recently completed bucket
            full_buckets.append(new_full_bucket)
            parcel_df = reduce_parcel_dataframe(parcel_df, new_full_bucket)
        if holding_threshold_exceeded:
            # reduce the holdings to the ones that have already been added
            parcel_df, all_the_rest_df = reduce_holdings(parcel_df, added_holdings)
            parcel_df = set_phase(parcel_df, "first loop but 3% exceeded")

    # After the loop above:
    # 
    # - if 3% rule is NOT selected and "prioritize covered" is NOT selected: all parcels were checked
    # 
    # - if 3% rule is NOT selected and "prioritize covered" is selected: all covered parcels were checked
    # ---> if some buckets are still not full, go through non-covered belonging to added holdings
    # ------> if some buckets are still not full, go through the rest of non-covered
    #
    # - if 3% rule is selected and "prioritize covered" is selected: all covered in 3% were checked
    # ---> if some buckets are still not full, go through non-covered belonging to added holdings
    # ------> if some buckets are still not full, go through the rest of covered (outside 3%)
    # ---------> if some buckets are still not full, go through the rest of non-covered (outside 3%)
    #
    # - if 3% rule is selected and "prioritize covered" is not selected: all parcels in 3% were checked
    # ---> if some buckets are still not full, go through the rest of parcels
    #
 
    if dm.covered_priority == 1 and some_buckets_empty(buckets):
        all_checked = False
        parcel_df, all_the_rest_noncovered = reduce_holdings(non_covered, added_holdings)
        #print("setting phase to noncovered belonging to added holdings")
        parcel_df = set_phase(parcel_df, "noncovered belonging to added holdings")
        parcel_df.to_excel("noncovered_belonging_to_added_holdings.xlsx")
        all_the_rest_noncovered.to_excel("all_the_rest_noncovered1.xlsx")
        for bucket_id in full_buckets:
            parcel_df = reduce_parcel_dataframe(parcel_df, bucket_id)
            all_the_rest_noncovered = reduce_parcel_dataframe(all_the_rest_noncovered, bucket_id)
            all_the_rest_noncovered.to_excel("all_the_rest_noncovered2.xlsx")

        checked_holdings = set()

        while not buckets_full(buckets) and not all_checked:
            buckets, new_full_bucket, holding_threshold_exceeded, added_holdings, all_checked = intervention_loop(parcel_df, buckets, progress_widgets, checked_holdings, added_rows, added_holdings, full_buckets, dm)
            if new_full_bucket != "":
                # remove rows associated with a recently completed bucket
                full_buckets.append(new_full_bucket)
                parcel_df = reduce_parcel_dataframe(parcel_df, new_full_bucket)
        # at this point all covered were checked, and non-covered that are in added holdings were checked
        # now we have to check the rest of non-covered
        if some_buckets_empty(buckets):
            #print("setting phase to noncovered not in added holdings")
            parcel_df = all_the_rest_noncovered
            parcel_df = set_phase(parcel_df, "noncovered not in added holdings")
            parcel_df.to_excel("noncovered_not_in_added_holdings.xlsx")
            
            parcel_df.to_excel("all_the_rest_noncovered3.xlsx")
            all_checked = False
            while not buckets_full(buckets) and not all_checked:
                buckets, new_full_bucket, holding_threshold_exceeded, added_holdings, all_checked = intervention_loop(parcel_df, buckets, progress_widgets, checked_holdings, added_rows, added_holdings, full_buckets, dm)
                if new_full_bucket != "":
                    # remove rows associated with a recently completed bucket
                    full_buckets.append(new_full_bucket)
                    parcel_df = reduce_parcel_dataframe(parcel_df, new_full_bucket)


    # the if statement above deals with both the 3% and no 3% scenario in "prioritize covered" mode.
    # even if the 3% rule is not selected, the first loop that goes through the non-covered parcels
    # has to only consider the holdings already added to the sample.

    
    if dm.holdings_reduced and some_buckets_empty(buckets):
        #print("Searching through the 3% of holdings finished. Some buckets are still empty. Trying to add one parcel to each of them, using the remaining data.")
        all_the_rest_df = set_phase(all_the_rest_df, "covered or non-covered outside 3%, single parcel for empty bucket check")
        buckets = find_one_and_finish(all_the_rest_df, buckets, progress_widgets, added_rows, dm)
        if dm.covered_priority == 1 and some_buckets_empty(buckets):
            #print("Some buckets are still empty. Trying to add one parcel to each of them, using the remaining non-covered parcels.")
            all_the_rest_noncovered = set_phase(all_the_rest_noncovered, "non-covered outside 3%, single parcel for empty bucket check")
            buckets = find_one_and_finish(all_the_rest_noncovered, buckets, progress_widgets, added_rows, dm)

    gui.update_output_area(buckets, progress_widgets)
    dm.final_bucket_state = buckets
    dm.added_holdings = added_holdings


    return buckets
