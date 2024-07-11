import os
import pandas as pd
import datetime
import uuid
import pickle

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

    with open(summary_path, 'w') as f:
        f.write(f"QUASSA Extraction Summary (ID: {prefix})\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write(f"Parameters:\n")
        f.write(f"- 3% holding limit: {'Yes' if param_3_percent else 'No'}\n")
        f.write(f"- Covered Priority: {covered_priority_label}\n\n")
        f.write(f"Bucket Summary:\n")
        f.write(f"--------------------------------------\n")
        f.write(f"Bucket ID | Number of Parcels | Target\n")
        f.write(f"--------------------------------------\n")
        for bucket_id, bucket in datamanager.final_bucket_state.items():
            f.write(f"{bucket_id} | {len(bucket['parcels'])} | {bucket['target']}\n")


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
        print("Generating holding level intervention file...")
        hl_output_path_csv, hl_output_path_excel = generate_holding_level_intervention_file(datamanager, prefix, timestamp)
        
    return prefix, summary_path, excel_path, csv_path, hl_output_path_csv, hl_output_path_excel

# Example usage:
# prefix, summary_path, excel_path, csv_path = generate_samples_extract_output(buckets, datamanager, user_prefix="my_extraction", debug=True)
# print(f"Extraction Prefix: {prefix}")
# print(f"Summary file: {summary_path}")
# print(f"Excel file: {excel_path}")
# print(f"CSV file: {csv_path}")

# Or without a user-specified prefix:
# prefix, summary_path, excel_path, csv_path = generate_samples_extract_output(buckets, datamanager, debug=True)
# print(f"Extraction Prefix: {prefix}")
# print(f"Summary file: {summary_path}")
# print(f"Excel file: {excel_path}")
# print(f"CSV file: {csv_path}")

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

