from datetime import datetime
from pathlib import Path
import pandas as pd

from pandas.testing import assert_frame_equal

from iacs_qa.BEFL.BEFL_fillbuckets_2024 import fill_buckets_2024


def test_fillbuckets_2024(skip_parcels_0_ua_groups: bool):
    # Input
    input_dir = Path(__file__).resolve().parent / "testdata"
    bucket_size = 4

    # Read input data
    parcels_df = pd.read_csv(input_dir / "parcels_ua_groups.csv")
    ranking_df = pd.read_csv(input_dir / "parcels_ranking.csv")

    output_dir = input_dir

    start_time = datetime.now()
    name = f"simulate_{bucket_size}P_2024_testdata"
    buckets_test_df = fill_buckets_2024(
        parcels_df,
        ranking_df,
        bucket_size=bucket_size,
        skip_parcels_0_ua_groups=skip_parcels_0_ua_groups,
    )
    simulation = {
        "name": name,
        "descr": (
            "Grouped Small Buckets, "
            "300 first ranked Parcels, 3 parcels/holding, "
            "rules of 2024"
        ),
        "total parcels": len(buckets_test_df),
        "unique parcels": len(buckets_test_df.parcel_id.unique()),
        "unique holdings": len(buckets_test_df.holding_id.unique()),
    }

    buckets_test_df.to_excel(output_dir / f"{name}.xlsx")
    print(simulation)
    print(f"{name} took {datetime.now()-start_time}")

    # Compare with expected result
    if skip_parcels_0_ua_groups:
        expected_path = input_dir / "expected_result_skip_parcels_0_ua_groups.csv"
    else:
        expected_path = input_dir / "expected_result.csv"
    expected_df = pd.read_csv(expected_path)
    expected_df = expected_df.sort_values(by=list(expected_df.columns)).reset_index(
        drop=True
    )
    buckets_test_df = (
        buckets_test_df[list(expected_df.columns)]
        .sort_values(by=list(expected_df.columns))
        .reset_index(drop=True)
    )
    assert_frame_equal(buckets_test_df, expected_df)


if __name__ == "__main__":
    test_fillbuckets_2024(skip_parcels_0_ua_groups=False)
    test_fillbuckets_2024(skip_parcels_0_ua_groups=True)
