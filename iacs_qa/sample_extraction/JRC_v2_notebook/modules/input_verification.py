import pandas as pd
import datetime


class DataFrameValidationError(Exception):
    """Exception raised for errors in the input DataFrame."""
    pass

def verify_and_report_parcel_df(parcel_df):
    """
    Fix this. This should collect all problems and throw them as a single exception.
    """

    requirements = {
        "gsa_par_id": [("string", "string"), ("int64", "integer"), ("float64", "float"),],
        "gsa_hol_id": [("int64", "integer"), ("float64", "float"),("string", "string"),],
        "ua_grp_id": [("string", "string")],
        "covered": [("int64", "integer")],
        "ranking": [("int64", "integer")]
    }

    issues_found = []

    for column, expected_types in requirements.items():
        # Check if column exists
        if column not in parcel_df.columns:
            issues_found.append(f"Column '{column}' not found in the dataframe.")
            continue

        # Check for empty values
        try:
            if parcel_df[column].isnull().any():
                issues_found.append(f"Column '{column}' contains empty values.")
        except Exception as e:
            issues_found.append(f"Error checking empty values in column '{column}': {str(e)}")

        # Get actual type
        try:
            actual_type = parcel_df[column].dtype
        except Exception as e:
            issues_found.append(f"Error getting data type of column '{column}': {str(e)}")
            continue

        # Special check for the 'covered' column
        if column == "covered":
            try:
                if not pd.api.types.is_integer_dtype(parcel_df[column]):
                    issues_found.append(f"Column '{column}' has incorrect data type. Expected {expected_types}, got {actual_type}.")
                if not parcel_df[column].isin([0, 1]).all():
                    issues_found.append(f"Column '{column}' should only contain 0s or 1s.")
            except Exception as e:
                issues_found.append(f"Error checking 'covered' column: {str(e)}")
        else:
            # Check data type for other columns
            try:
                type_matched = False
                for expected_type_str, type_name in expected_types:
                    if expected_type_str == "string":
                        if pd.api.types.is_string_dtype(parcel_df[column]) or actual_type == "object":
                            type_matched = True
                            break
                    else:
                        if pd.api.types.is_dtype_equal(actual_type, expected_type_str):
                            type_matched = True
                            break
                
                if not type_matched:
                    issues_found.append(f"Column '{column}' has incorrect data type. Expected {expected_types}, got {actual_type}.")
            except Exception as e:
                issues_found.append(f"Error checking data type of column '{column}': {str(e)}")

    # Always reach this point and raise the custom exception if issues are found
    if issues_found:
        raise DataFrameValidationError("\n" + "\n".join(issues_found))

    return True


def verify_target_df(target_df):
    """
    Verifies if all required columns are present in the dataframe, their data types are correct,
    and there are no empty values. Also checks for unique values in 'ua_grp_id'.

    Raises:
        DataFrameValidationError: If any verification check fails.

    Returns:
        True if the dataframe is valid.
    """
    requirements = {
        "ua_grp_id": ("string", "string"),
        "target": ("int64", "integer")
    }

    for column, (expected_type_str, type_name) in requirements.items():
        if column not in target_df.columns:
            raise DataFrameValidationError(f"Column '{column}' not found in the dataframe.")
        if target_df[column].isnull().any():
            raise DataFrameValidationError(f"Column '{column}' contains empty values.")

        actual_type = target_df[column].dtype

        if expected_type_str == "string":
            if not (pd.api.types.is_string_dtype(target_df[column]) or actual_type == "object"):
                raise DataFrameValidationError(f"Column '{column}' has incorrect data type. Expected {type_name}, got {actual_type}.")
        else:
            if not pd.api.types.is_integer_dtype(target_df[column]):
                raise DataFrameValidationError(f"Column '{column}' has incorrect data type. Expected {type_name}, got {actual_type}.")

    if not target_df["ua_grp_id"].is_unique:
        raise DataFrameValidationError("Column 'ua_grp_id' contains duplicate values.")

    return True


def compare_bucket_lists(ua_id_dict, target_df):
    """
    Verifies if all unique values in 'ua_grp_id' from 'target_df' are present in 'ua_id_dict'.
    Verifies if all unique values in 'ua_grp_id' from 'ua_id_dict' are present in 'target_df'.

    Raises:
        DataFrameValidationError: If the verification fails.
    
    Returns:
        True if valid.
    """
    parcel_ua_groups = set(ua_id_dict.keys())
    target_ua_groups = set(target_df["ua_grp_id"].unique())

    if ua_id_dict == {}:
        raise DataFrameValidationError("No ua_grp_id values found in the parcel data. Please load the parcel file first.")
    if not target_ua_groups.issubset(parcel_ua_groups):
        missing_groups = target_ua_groups - parcel_ua_groups
        raise DataFrameValidationError(f"UA groups {missing_groups} not found in the parcel data. Go back to the parcel and target files and make sure the ua group IDs match.")
    
    if not parcel_ua_groups.issubset(target_ua_groups):
        missing_groups = parcel_ua_groups - target_ua_groups
        raise DataFrameValidationError(f"UA groups {missing_groups} not found in the target data. Go back to the parcel and target files and make sure the ua group IDs match.")
    
    return True