#!/usr/bin/env python3

import argparse
import sys
import os

# Import your existing modules exactly as they are
from modules.data_manager import DataManager
from modules.input_verification import verify_and_report_parcel_df, verify_target_df, compare_bucket_lists
from modules.sample_extraction import (
    prepare_input_dataframe,
    prepare_buckets,
    iterate_over_interventions_fast
)
from modules.output_tools import generate_samples_extract_output
from modules.gui import get_ua_groups_from_parcel_file
import pandas as pd


def parse_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Run QUASSA sample extraction from command line.")

    # Paths
    parser.add_argument("--parcel_file", help="Path to the parcel list CSV.")
    parser.add_argument("--target_file", help="Path to the CSV with target values for each bucket.")

    # Parameters
    parser.add_argument("--3_percent", help="Whether to limit the search to 3%% of holdings (true/false).")
    parser.add_argument("--covered_priority", type=int,
                        help="0=Include all, 1=Prioritize covered, 2=Include only covered.")
    parser.add_argument("--noncontributing_filtering", type=int,
                        help="0=Filter out noncontributing highest ranked parcels once bucket is filled, 1=Retain them.")
    parser.add_argument("--extraction_id", help="Optional ID for labeling output files.")

    args = parser.parse_args()

    final_params = {}
    final_params["parcel_file"] = args.parcel_file
    final_params["target_file"] = args.target_file

    # For booleans, we need to interpret "yes"/"no"/"true"/"false"
    # Or else we keep them as None if not specified
    def interpret_bool(val):
        if isinstance(val, bool):
            return val
        if not val:
            return False
        val_lower = val.strip().lower()
        return val_lower in ["yes", "true", "1"]

    final_params["param_3_percent"] = interpret_bool(getattr(args, "3_percent", "false"))
    final_params["covered_priority"] = args.covered_priority if args.covered_priority is not None else 0
    final_params["noncontributing_filtering"] = args.noncontributing_filtering if args.noncontributing_filtering is not None else 0
    final_params["extraction_id"] = args.extraction_id if args.extraction_id else ""

    return final_params


def main(extract_targets=False):
    # 1. Parse CLI args
    params = parse_args()

    parcel_file = params["parcel_file"]
    target_file = params["target_file"]
    param_3_percent = params["param_3_percent"]
    covered_priority = params["covered_priority"]
    noncontributing_filtering = params["noncontributing_filtering"]
    extraction_id = params["extraction_id"]

    if not parcel_file:
        print("Error: no parcel file specified. Use --parcel_file.")
        sys.exit(1)

    # 2. Initialize DataManager
    dm = DataManager()
    dm.param_3_percent = param_3_percent
    dm.covered_priority = covered_priority
    dm.noncontributing_filtering = noncontributing_filtering
    dm.extraction_id = extraction_id if extraction_id else ""

    # 3. Read the parcel file, verify structure
    try:
        parcels_df = pd.read_csv(parcel_file, dtype={
            'gsa_par_id': str,
            'gsa_hol_id': str,
            'ua_grp_id': str,
            'covered': int,
            'ranking': int
        })
    except Exception as e:
        print(f"Could not read parcel CSV: {e}")
        sys.exit(1)

    try:
        verify_and_report_parcel_df(parcels_df)
    except Exception as e:
        print(f"Parcel file validation failed:\n{e}")
        sys.exit(1)

    dm.parcels_df = parcels_df
    dm.parcels_path = parcel_file
    dm.parcel_file_loaded = True

    # 4. Derive or load targets
    #    If target_file is specified, load from there.
    #    Otherwise, create defaults with get_ua_groups_from_parcel_file(...)
    if target_file and os.path.exists(target_file):
        try:
            targets_df = pd.read_csv(target_file)
            verify_target_df(targets_df)
        except Exception as e:
            print(f"Target file validation failed:\n{e}")
            sys.exit(1)

        # populate dm.ua_groups with all UA groups in the parcel file
        temp_ua_dict = get_ua_groups_from_parcel_file(dm.parcels_df, mode="simple")  # "simple" here is just to extract groups
        dm.ua_groups = temp_ua_dict
        try:
            compare_bucket_lists(dm.ua_groups, targets_df)
        except Exception as e:
            print(f"Inconsistent UA group sets:\n{e}")
            sys.exit(1)

        # Now set the target in the dictionary from the CSV
        for _, row in targets_df.iterrows():
            ua_grp = row["ua_grp_id"]
            tgt = int(row["target"])
            dm.ua_groups[ua_grp]["target"] = tgt


    else:
        # Create the default target dictionary from the parcel file
        print("No valid target file. Using default target generation...")
        ua_dict = get_ua_groups_from_parcel_file(dm.parcels_df, mode="simple")
        dm.ua_groups = ua_dict

    # 5. Perform the extraction
    #    (Same as in the notebook steps.)
    print("Preparing data for extraction...")
    prepared_df = prepare_input_dataframe(dm)
    buckets = prepare_buckets(dm.ua_groups)
    print("Beginning sample extraction process...")
    final_buckets = iterate_over_interventions_fast(prepared_df, buckets, dm, progress_widgets="console")
    dm.final_bucket_state = final_buckets

    # 6. Generate outputs
    print("Generating output files...")
    prefix, summary_path, excel_path, csv_path, hl_csv, hl_excel, par_xlsx, par_csv = generate_samples_extract_output(final_buckets, dm)


    print("")
    print("Extraction finished.")
    print(f"Summary file: {summary_path}")
    print(f"Main output CSV: {csv_path}")
    print(f"Main output Excel: {excel_path}")
    if hl_csv and hl_excel:
        print(f"Additional holding-level intervention CSV: {hl_csv}")
        print(f"Additional holding-level intervention Excel: {hl_excel}")


if __name__ == "__main__":
    main()