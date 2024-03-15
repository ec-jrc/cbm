from datetime import datetime
from pathlib import Path
from typing import Dict, Union
import pandas as pd

from pandas.testing import assert_frame_equal

from iacs_qa.BEFL.BEFL_fillbuckets_2024 import fill_buckets_2024


def test_fillbuckets_2024(skip_parcels_0_ua_groups: bool, bucket_size_dict: bool):
    # Input
    input_dir = Path(__file__).resolve().parent / "testdata"

    # Read input data
    parcels_df = pd.read_csv(input_dir / "parcels_ua_groups.csv")
    ranking_df = pd.read_csv(input_dir / "parcels_ranking.csv")
    if bucket_size_dict:
        bucket_size = {}
        for ua_group in parcels_df["ua_group"].unique():
            bucket_size[ua_group] = 4
    else:
        bucket_size = 4

    output_dir = input_dir

    start_time = datetime.now()
    name = "simulate_2024_testdata"
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


def test_fillbuckets_2024_bucketsize(bucket_size: Union[int, Dict[str, int]]):
    # Input
    input_dir = Path(__file__).resolve().parent / "testdata"

    # Read input data
    parcels_df = pd.read_csv(input_dir / "parcels_ua_groups.csv")
    ranking_df = pd.read_csv(input_dir / "parcels_ranking.csv")

    output_dir = input_dir

    name = "simulate_2024_testdata_bucketsize"
    buckets_test_df = fill_buckets_2024(
        parcels_df,
        ranking_df,
        bucket_size=bucket_size,
        skip_parcels_0_ua_groups=False,
    )
    simulation = {
        "name": name,
        "descr": (
            "Grouped Small Buckets, "
            "first ranked Parcels, 3 parcels/holding, "
            "rules of 2024"
        ),
        "total parcels": len(buckets_test_df),
        "unique parcels": len(buckets_test_df.parcel_id.unique()),
        "unique holdings": len(buckets_test_df.holding_id.unique()),
    }

    buckets_test_df.to_excel(output_dir / f"{name}.xlsx")
    print(simulation)

    # Check result
    bucket_counts = buckets_test_df.groupby(by="bucket")[["bucket"]].count()
    assert len(bucket_size) == len(bucket_counts)
    for bucket, count in bucket_counts.itertuples():
        assert bucket_size[bucket] == count


if __name__ == "__main__":
    # Test, bucket size as int
    test_fillbuckets_2024(skip_parcels_0_ua_groups=False, bucket_size_dict=False)
    # Test, bucket size as dict
    test_fillbuckets_2024(skip_parcels_0_ua_groups=False, bucket_size_dict=True)

    # Test version with less holdings needed by skipping parcels with few ua_groups
    # Remark: not to be used in 2024, maybe proposel for 2025.
    test_fillbuckets_2024(skip_parcels_0_ua_groups=True, bucket_size_dict=False)

    # Test variable bucket sizes
    bucket_size = {"UA1": 6, "gUA2": 4, "UA3": 3, "UA4": 2, "UA5": 4}
    test_fillbuckets_2024_bucketsize(bucket_size=bucket_size)
