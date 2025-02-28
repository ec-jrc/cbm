import os
import pandas as pd
import datetime
import uuid
import pickle
from modules.stats import calculate_summary_stats

def generate_supplementary_output(datamanager):
    param_3_percent = datamanager.param_3_percent
    covered_priority = datamanager.covered_priority

    covered_priority_label = [key for key, value in datamanager.covered_priority_dict.items() if value == covered_priority][0]

    if datamanager.extraction_id and datamanager.extraction_id != "":
        prefix = datamanager.extraction_id
    else:
        prefix = f"extraction_{str(uuid.uuid4())[:8]}"
        datamanager.extraction_id = prefix

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    summary_filename = f"{prefix}_{timestamp}.txt"
    summary_path = os.path.join(output_dir, summary_filename)

    summary_stats = calculate_summary_stats(datamanager)

    # summary_stats:
    # {'total_rows': 102462, 'selected_rows': 1692, 'all_unique_parcels_count': 46114, 'all_selected_parcels_count': 1182, 'avg_par_per_hol': 6.092783505154639, 'total_holdings': 6307, 'selected_holdings': 194, 'avg_int_per_holding': 8.721649484536082, 'most_interventions': (8753, 47), 'covered_parcels': 1036, 'noncovered_parcels': 23, 'bucket_stats': {'E5': {'label': '1. E5', 'selected': 271, 'total': 5145, 'target': 300}, 'ANC': {'label': '2. ANC', 'selected': 300, 'total': 46097, 'target': 300}, 'BIS': {'label': '3. BIS', 'selected': 300, 'total': 36641, 'target': 300}, 'ES2': {'label': '4. ES2', 'selected': 66, 'total': 482, 'target': 115}, 'E3': {'label': '5. E3', 'selected': 88, 'total': 1006, 'target': 230}, 'C5': {'label': '6. C5', 'selected': 236, 'total': 3003, 'target': 300}, 'SFS': {'label': '7. SFS', 'selected': 143, 'total': 7167, 'target': 300}, 'YFS': {'label': '8. YFS', 'selected': 147, 'total': 1614, 'target': 300}, 'C1': {'label': '9. C1', 'selected': 24, 'total': 281, 'target': 55}, 'C3': {'label': '10. C3', 'selected': 15, 'total': 79, 'target': 50}, 'E7B': {'label': '11. E7B', 'selected': 6, 'total': 89, 'target': 50}, 'E4': {'label': '12. E4', 'selected': 11, 'total': 52, 'target': 50}, 'CIS: LA': {'label': '13. CIS: LA', 'selected': 35, 'total': 418, 'target': 115}, 'C6C': {'label': '14. C6C', 'selected': 6, 'total': 175, 'target': 50}, 'C4': {'label': '15. C4', 'selected': 5, 'total': 16, 'target': 16}, 'E1C': {'label': '16. E1C', 'selected': 14, 'total': 130, 'target': 50}, 'C2B': {'label': '17. C2B', 'selected': 1, 'total': 1, 'target': 1}, 'ES1': {'label': '18. ES1', 'selected': 3, 'total': 16, 'target': 16}, 'ME2': {'label': '19. ME2', 'selected': 3, 'total': 21, 'target': 21}, 'E2': {'label': '20. E2', 'selected': 9, 'total': 9, 'target': 9}, 'E7A': {'label': '21. E7A', 'selected': 4, 'total': 11, 'target': 11}, 'TEST': {'label': '22. TEST', 'selected': 3, 'total': 6, 'target': 6}, 'TEST2': {'label': '23. TEST2', 'selected': 2, 'total': 3, 'target': 3}}}

    # total_rows 102462
    # selected_rows 1692
    # all_unique_parcels_count 46114
    # all_selected_parcels_count 1182
    # avg_par_per_hol 6.092783505154639
    # total_holdings 6307
    # selected_holdings 194
    # avg_int_per_holding 8.721649484536082
    # most_interventions (8753, 47)
    # covered_parcels 1036
    # noncovered_parcels 23
    # bucket_stats {'E5': {'label': '1. E5', 'selected': 271, 'total': 5145, 'target': 300}, 'ANC': {'label': '2. 

    with open(summary_path, 'w', encoding="utf-8") as f:
        f.write(f"QUASSA Extraction Summary (ID: {prefix})\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write(f"Parameters:\n")
        f.write(f"- 3% holding limit: {'Yes' if param_3_percent else 'No'}\n")
        f.write(f"- Covered Priority: {covered_priority_label}\n")
        f.write(f"- Non-contributing, highest ranked parcel of each holding: {'Retain when a bucket is filled' if datamanager.noncontributing_filtering == 1 else 'Filter out when a bucket is filled'}\n\n")
        f.write(f"- Selected holding level interventions: {datamanager.holding_level_interventions if datamanager.holding_level_interventions != [] else 'none.'}\n\n")
        f.write(f"Bucket Summary:\n")
        f.write(f"--------------------------------------\n")
        f.write(f"Bucket ID | Selected | Target | Total | Selected / Total\n")
        f.write(f"--------------------------------------\n")
        for bucket_id, bucket in summary_stats['bucket_stats'].items():
            f.write(f"{bucket_id} | {bucket['selected']} | {bucket['target']} | {bucket['total']} | {bucket['selected'] / bucket['total']:.2%}\n")
        f.write(f"--------------------------------------\n\n")
        f.write(f"General Statistics:\n")
        f.write(f"- Total unique parcels: {summary_stats['all_unique_parcels_count']}\n")
        f.write(f"- Selected parcels: {summary_stats['all_selected_parcels_count']}\n")
        f.write(f"- Total holdings: {summary_stats['total_holdings']}\n")
        f.write(f"- Selected holdings: {summary_stats['selected_holdings']}\n")
        f.write(f"- Average number of selected parcels per selected holding: {summary_stats['avg_par_per_hol']:.2f}\n")
        f.write(f"- Selected parcels covered by VHR images: {summary_stats['covered_parcels']}\n")
        f.write(f"- Selected parcels not covered by VHR images: {summary_stats['noncovered_parcels']}\n")


    


    return prefix, summary_path, timestamp



def generate_output(buckets, prefix, timestamp, debug=False):
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

    parcel_columns = ["gsa_par_id", "gsa_hol_id", "ranking", "covered", "order_added"]
    if debug:
        parcel_columns.append("phase")

    output = []
    for bucket_id, bucket in buckets.items():
        for parcel in bucket['parcels']:
            output.append([bucket_id] + [parcel[column] for column in parcel_columns])
    
    output_df = pd.DataFrame(output, columns=["bucket_id"] + parcel_columns)

    # save output_df as pickle
    if debug:
        print("Saving output_df as pickle...")
        output_pickle_path = os.path.join(output_dir, f"{prefix}_{timestamp}.pkl")
        with open(output_pickle_path, 'wb') as f:
            pickle.dump(output_df, f)
    


    output_path_excel = os.path.join(output_dir, f"{prefix}_{timestamp}.xlsx")
    output_path_csv = os.path.join(output_dir, f"{prefix}_{timestamp}.csv")

    output_df.to_excel(output_path_excel, index=False)
    output_df.to_csv(output_path_csv, index=False)

    return output_path_excel, output_path_csv


def generate_samples_extract_output(buckets, datamanager, debug=False):
    print("Generating extraction output.")

    print("Generating summary file...")
    prefix, summary_path, timestamp = generate_supplementary_output(datamanager)

    print("Generating extracted parcel lists...")
    excel_path, csv_path = generate_output(buckets, prefix, timestamp, debug)

    hl_output_path_csv = None
    hl_output_path_excel = None

    if datamanager.holding_level_interventions != []:
        hl_output_path_csv, hl_output_path_excel = generate_holding_level_intervention_file(datamanager, prefix, timestamp)
        
    return prefix, summary_path, excel_path, csv_path, hl_output_path_csv, hl_output_path_excel


def generate_holding_level_intervention_file(datamanager, prefix, timestamp):

    print("Generating holding level intervention file...")

    hl_ua_group_list = datamanager.holding_level_interventions
    final_buckets = datamanager.final_bucket_state

    # take all holding IDs from filled buckets marked as HL after the extraction
    hl_holding_ids = []
    for bucket_id, bucket in final_buckets.items():
        if bucket_id in hl_ua_group_list:
            for parcel in bucket['parcels']:
                hl_holding_ids.append(parcel['gsa_hol_id'])

    # use the original parcels_df, filter it down to only the holdings from step 1
    parcels_df = datamanager.parcels_df
    hl_holdings_df = parcels_df[parcels_df['gsa_hol_id'].isin(hl_holding_ids)]

    # if defined by user, filter down to only covered
    if datamanager.covered_priority == 2:
        hl_holdings_df = hl_holdings_df[hl_holdings_df['covered'] == 1]

    # filter these down to only the ua_group_ids from the hl_ua_group_list
    hl_parcels_df = hl_holdings_df[hl_holdings_df['ua_grp_id'].isin(hl_ua_group_list)]


    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    hl_output_path_csv = os.path.join(output_dir, f"{prefix}_{timestamp}_holding_level_interventions.csv")
    hl_output_path_excel = os.path.join(output_dir, f"{prefix}_{timestamp}_holding_level_interventions.xlsx")

    hl_parcels_df.to_csv(hl_output_path_csv, index=False)
    hl_parcels_df.to_excel(hl_output_path_excel, index=False)

    return hl_output_path_csv, hl_output_path_excel
        

    # remember about the only-covered option

