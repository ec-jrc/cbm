import pandas as pd
import logging
from modules.input_verification import verify_parcel_df, verify_target_df, compare_bucket_lists
from modules.gui import get_ua_groups_from_parcel_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_parcels_and_ua_groups(path):
    """
    Extracts the parcels from the csv file and returns a dataframe and UA group dictionary.
    """
    try:
        parcel_df = pd.read_csv(path)
        verify_parcel_df(parcel_df)
        ua_group_dict = get_ua_groups_from_parcel_file(parcel_df)
        logging.info("Parcel file verified successfully. Preview: \n%s", parcel_df.head())
        return parcel_df, ua_group_dict
    except FileNotFoundError:
        logging.error("File not found: %s", path)
        raise
    except pd.errors.ParserError:
        logging.error("Parsing error while reading the file: %s", path)
        raise
    except Exception as e:
        logging.error("Unexpected error loading parcel file: %s", e)
        raise


def extract_targets(path, ua_groups_dict):
    """
    Extracts the targets from the csv file and returns a dataframe.
    """
    try:
        target_df = pd.read_csv(path)
        verify_target_df(target_df)
        compare_bucket_lists(ua_groups_dict, target_df)
        logging.info("Targets file verified successfully. Preview: \n%s", target_df.head())
        return target_df
    except FileNotFoundError:
        logging.error("File not found: %s", path)
        raise
    except pd.errors.ParserError:
        logging.error("Parsing error while reading the file: %s", path)
        raise
    except Exception as e:
        logging.error("Unexpected error loading targets file: %s", e)
        raise


if __name__ == "__main__":
    try:
        parcel_file_path = input("Enter the path to the parcel file: ")
        parcel_df, ua_groups_initial_dict = extract_parcels_and_ua_groups(parcel_file_path)

        targets_file_path = input("Enter the path to the targets file: ")
        target_df = extract_targets(targets_file_path, ua_groups_initial_dict)
        logging.info("All files loaded successfully.")
    except Exception as e:
        logging.error("An error occurred: %s", e)


    