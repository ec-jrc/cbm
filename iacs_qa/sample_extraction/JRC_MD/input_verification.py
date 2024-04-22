import pandas as pd

def verify_parcel_df(parcel_df):
    """
    Verifies if all required columns are present in the dataframe, their data types are correct,
    and there are no empty values.
    Returns True if valid, otherwise prints an error and returns False.
    """
    requirements = {
        "gsa_par_id": ("string", "string"),
        "gsa_hol_id": ("int64", "integer"),
        "ua_grp_id": ("string", "string"),
        "covered": ("int64", "integer"),
        "ranking": ("int64", "integer")
    }

    for column, (expected_type_str, type_name) in requirements.items():
        if column not in parcel_df.columns:
            print(f"Column '{column}' not found in the dataframe.")
            return False
        if parcel_df[column].isnull().any():
            print(f"Column '{column}' contains empty values.")
            return False
        
        actual_type = parcel_df[column].dtype

        # Special check for the 'covered' column to ensure it's binary (0 or 1)
        if column == "covered":
            if not pd.api.types.is_integer_dtype(parcel_df[column]):
                print(f"Column '{column}' has incorrect data type. Expected {type_name}, got {actual_type}.")
                return False
            if not parcel_df[column].isin([0, 1]).all():
                print(f"Column '{column}' should only contain 0s or 1s.")
                return False
        else:
            if expected_type_str == "string":
                if not (pd.api.types.is_string_dtype(parcel_df[column]) or actual_type == "object"):
                    print(f"Column '{column}' has incorrect data type. Expected {type_name}, got {actual_type}.")
                    return False
            else:
                if not pd.api.types.is_dtype_equal(actual_type, expected_type_str):
                    print(f"Column '{column}' has incorrect data type. Expected {type_name}, got {actual_type}.")
                    return False

    return True


def verify_target_df(target_df):
    """
    Verifies if all required columns are present in the dataframe, their data types are correct,
    and there are no empty values. Also checks for unique values in 'ua_grp_id'.
    Returns True if valid, otherwise prints an error and returns False.
    """
    requirements = {
        "ua_grp_id": (str, "string"),
        "target1": (int, "integer")
    }

    for column, (expected_type, type_name) in requirements.items():
        if column not in target_df.columns:
            print(f"Column '{column}' not found in the dataframe.")
            return False
        if target_df[column].isnull().any():
            print(f"Column '{column}' contains empty values.")
            return False
        if not pd.api.types.is_dtype_equal(target_df[column].dtype, expected_type):
            actual_type = target_df[column].dtype
            print(f"Column '{column}' has incorrect data type. Expected {type_name}, got {actual_type}.")
            return False

    if not target_df["ua_grp_id"].is_unique:
        print("Column 'ua_grp_id' contains duplicate values.")
        return False

    return True

def cross_verify_dfs(parcel_df, target_df):
    """
    Verifies if all unique values in 'ua_grp_id' from 'target_df' are present in 'parcel_df'.
    Verifies if all unique values in 'ua_grp_id' from 'parcel_df' are present in 'target_df'.
    Returns True if valid, otherwise prints an error and returns False.
    """
    parcel_ua_groups = set(parcel_df["ua_grp_id"].unique())
    target_ua_groups = set(target_df["ua_grp_id"].unique())

    if not target_ua_groups.issubset(parcel_ua_groups):
        missing_groups = target_ua_groups - parcel_ua_groups
        print(f"Target groups {missing_groups} not found in the parcel data.")
        return False

    if not parcel_ua_groups.issubset(target_ua_groups):
        missing_groups = parcel_ua_groups - target_ua_groups
        print(f"Parcel groups {missing_groups} not found in the target data.")
        return False

    return True
        