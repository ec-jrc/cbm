import pandas as pd

def compare_csv_files(file1, file2, ignore_columns=None):
    # Load the CSV files into pandas DataFrames
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # If there are columns to ignore, drop them
    if ignore_columns:
        df1 = df1.drop(columns=ignore_columns)
        df2 = df2.drop(columns=ignore_columns)

    # Find the rows that differ
    diff = pd.concat([df1, df2]).drop_duplicates(keep=False)

    # Count the number of differing rows
    num_differing_rows = len(diff)

    return num_differing_rows, diff

# Example function call (commented out for now)
# compare_csv_files("data1.csv", "data2.csv", ignore_columns=["ID"])


print(compare_csv_files("output/output_fast.csv", "output/output_slow.csv", ignore_columns=["order_added"]))