from datetime import datetime
from pathlib import Path
import tempfile
from typing import Dict, Union

import pandas as pd
from pandas.testing import assert_frame_equal

from BEFL_fillbuckets_2024 import fill_buckets_2024


def test_fillbuckets_2024(
    tmp_path: Path,
    skip_parcels_0_ua_groups: bool,
    bucket_size_dict: bool,
    capping: float,
    expected_result_filename: str,
):
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

    start_time = datetime.now()
    name = f"simulate_2024_testdata_bucketsize4_capping{capping}"
    if skip_parcels_0_ua_groups:
        name = f"{name}_skip_parcels_0_ua_groups"
    buckets_test_df = fill_buckets_2024(
        parcels_df,
        ranking_df,
        bucket_size=bucket_size,
        skip_parcels_0_ua_groups=skip_parcels_0_ua_groups,
        capping=capping,
    )
    simulation = {
        "name": name,
        "descr": "first ranked Parcels, 3 parcels/holding, rules of 2024",
        "total parcels": len(buckets_test_df),
        "unique parcels": len(buckets_test_df.parcel_id.unique()),
        "unique holdings": len(buckets_test_df.holding_id.unique()),
    }

    buckets_test_df.to_csv(tmp_path / f"test_{name}.csv", index=False)
    print(simulation)
    print(f"{name} took {datetime.now()-start_time}")

    # Compare with expected result
    expected_df = pd.read_csv(input_dir / expected_result_filename)
    expected_df = expected_df.sort_values(by=list(expected_df.columns)).reset_index(
        drop=True
    )
    buckets_test_df = (
        buckets_test_df[list(expected_df.columns)]
        .sort_values(by=list(expected_df.columns))
        .reset_index(drop=True)
    )
    assert_frame_equal(buckets_test_df, expected_df)


def test_fillbuckets_2024_bucketsize(
    tmp_path: Path, bucket_size: Union[int, Dict[str, int]]
):
    # Input
    input_dir = Path(__file__).resolve().parent / "testdata"

    # Read input data
    parcels_df = pd.read_csv(input_dir / "parcels_ua_groups.csv")
    ranking_df = pd.read_csv(input_dir / "parcels_ranking.csv")

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

    buckets_test_df.to_excel(tmp_path / f"{name}.xlsx")
    print(simulation)

    # Check result
    bucket_counts = buckets_test_df.groupby(by="bucket")[["bucket"]].count()
    assert len(bucket_size) == len(bucket_counts)
    for bucket, count in bucket_counts.itertuples():
        assert bucket_size[bucket] == count


if __name__ == "__main__":
    tmp_dir = Path(
        tempfile.mkdtemp(prefix="BEFL_fillbuckets_2024/test_fillbuckets_2024_")
    )
    tmp_dir.mkdir(parents=True, exist_ok=True)
    print(f"{tmp_dir=}")

    # Test, bucket size as int
    test_fillbuckets_2024(
        tmp_path=tmp_dir,
        skip_parcels_0_ua_groups=False,
        bucket_size_dict=False,
        capping=-1,
        expected_result_filename="expected_result.csv",
    )
    # Test, bucket size as dict
    test_fillbuckets_2024(
        tmp_path=tmp_dir,
        skip_parcels_0_ua_groups=False,
        bucket_size_dict=True,
        capping=-1,
        expected_result_filename="expected_result.csv",
    )

    # Test version with less holdings needed by skipping parcels with few ua_groups
    # Remark: not to be used in 2024, maybe proposal for 2025.
    test_fillbuckets_2024(
        tmp_path=tmp_dir,
        skip_parcels_0_ua_groups=True,
        bucket_size_dict=False,
        capping=-1,
        expected_result_filename="expected_result_skip_parcels_0_ua_groups.csv",
    )

    # Test, bucket size as int, capping to 1 holding
    # Remark: capping to 1 holding results in an empty bucket, that is filled up with
    # all parcels of 1 extra holding.
    test_fillbuckets_2024(
        tmp_path=tmp_dir,
        skip_parcels_0_ua_groups=False,
        bucket_size_dict=False,
        capping=1,
        expected_result_filename="expected_result_capping1.csv",
    )

    # Test variable bucket sizes
    bucket_size = {"UA1": 6, "gUA2": 4, "UA3": 3, "UA4": 2, "UA5": 4}
    test_fillbuckets_2024_bucketsize(tmp_path=tmp_dir, bucket_size=bucket_size)
