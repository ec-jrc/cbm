"""
BSD 3-Clause License

Copyright (c) 2024, Pieter Roggemans

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pandas as pd


def fill_buckets_2024(
    parcels_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    bucket_size: int,
    skip_parcels_0_ua_groups: bool,
    print_progress: bool = False,
) -> pd.DataFrame:
    """
    Simulation to fill buckets according to new rules of 2024.

    Notes:
      - this has been developed only for simulation purposes, so is not to be treated as
        production ready code and hasn't been thouroughly tested.
      - there is no support (yet) for the 3 % capping rule.
      - there is no support (yet) for different bucket sizes per unit amount.

    Args:
        parcels_df (pd.DataFrame): DataFrame with parcels. Expected columns:
            ["parcel_id", "holding_id", "ua_group"].
        ranking_df (pd.DataFrame): DataFrame with parcel ranking. Expected columns:
            ["parcel_id", "ranking"].
        bucket_size (int): maximum number of parcels per bucket.
        skip_parcels_0_ua_groups (bool): skip parcels that at the moment they are
            reached in the ranking belong to no ua groups anymore. This results in
            3% fewer unique parcels and 25% fewer unique holdings in the buckets.
        print_progress (bool, optional): True to print some progress. Defaults to False.

    Returns:
        pd.DataFrame: the filled up buckets.
    """
    # Check input parameters
    expected_columns = ["parcel_id", "holding_id", "ua_group"]
    if sorted(parcels_df.columns) != sorted(expected_columns):
        raise ValueError(
            f"parcels_df should have columns {expected_columns}, not "
            f"{list(parcels_df.columns)}"
        )
    expected_columns = ["parcel_id", "ranking"]
    if sorted(ranking_df.columns) != sorted(expected_columns):
        raise ValueError(
            f"ranking_df should have columns {expected_columns}, not "
            f"{list(ranking_df.columns)}"
        )

    # Join ranking data with the parcel data
    parcels_df = parcels_df.merge(ranking_df, on="parcel_id")

    # Recreate ranking df with holding_id added + sort on ranking
    ranking_df = (
        parcels_df[["parcel_id", "holding_id", "ranking"]]
        .drop_duplicates()
        .sort_values(["ranking"])
    )
    parcels_df = parcels_df.set_index("parcel_id", drop=False)
    # Also create a parcel list with an index on holding_id
    parcels_h_df = parcels_df.set_index("holding_id", drop=False)

    # Init buckets
    buckets = {}
    buckets_needed = set(parcels_df["ua_group"].unique())
    for ua_group in buckets_needed:
        buckets[ua_group] = {}

    # Loop through parcels
    buckets_filled = set()
    holdings_treated = set()
    nb_buckets_filled = 0
    for counter, parcel in enumerate(ranking_df.itertuples()):
        if buckets_filled == buckets_needed:
            break

        # If the current parcel only has ua_groups that are already filled up, skip it.
        parcel_ua_groups = None
        if skip_parcels_0_ua_groups:
            parcel_ua_groups = set(
                parcels_df.loc[parcels_df.index == parcel.parcel_id]["ua_group"]
            )
            if len(parcel_ua_groups - buckets_filled) == 0:
                continue

        # Extra buckets filled, so filter the parcel DataFrame some more.
        if len(buckets_filled) > nb_buckets_filled:
            parcels_df = parcels_df[~parcels_df.ua_group.isin(buckets_filled)]
            parcels_h_df = parcels_df.set_index("holding_id", drop=False)
            nb_buckets_filled = len(buckets_filled)

        if print_progress and counter % 10000 == 0:
            print(f"processed {counter} parcels of {len(ranking_df)}")

        if parcel.holding_id not in holdings_treated:
            holdings_treated.add(parcel.holding_id)
            # All parcels of the holding
            parcels_holding_df = parcels_h_df.loc[
                parcels_h_df.index == parcel.holding_id
            ]

            # Loop over ua_groups in holding
            for ua_group in parcels_holding_df["ua_group"].unique():
                # Parcels in the holding with this ua_group, sorted by ranking
                parcels_ua_group_df = parcels_holding_df.loc[
                    parcels_holding_df.ua_group == ua_group
                ].sort_values(["ranking"])

                nb_added = 0
                for parcel_ua_group in parcels_ua_group_df.itertuples():
                    buckets[ua_group][parcel_ua_group.parcel_id] = {
                        "bucket": ua_group,
                        "parcel_id": parcel_ua_group.parcel_id,
                        "holding_id": parcel_ua_group.holding_id,
                        "ua_group": ua_group,
                        "ranking": parcel_ua_group.ranking,
                    }

                    # Only up till bucket size in bucket
                    if len(buckets[ua_group]) >= bucket_size:
                        buckets_filled.add(ua_group)
                        break

                    # Add maximum 3 parcels per holding to a bucket
                    nb_added += 1
                    if nb_added >= 3:
                        break

        else:
            # Holding has already been processed... just try to add this single
            # parcel to each relevant bucket if it isn't in it yet.

            # Loop over ua_groups of current parcel
            if parcel_ua_groups is None:
                parcel_ua_groups = parcels_df.loc[parcels_df.index == parcel.parcel_id][
                    "ua_group"
                ].unique()
            for ua_group in parcel_ua_groups:
                if parcel.parcel_id not in buckets[ua_group]:
                    buckets[ua_group][parcel_ua_group.parcel_id] = {
                        "bucket": ua_group,
                        "parcel_id": parcel.parcel_id,
                        "holding_id": parcel.holding_id,
                        "ua_group": ua_group,
                        "ranking": parcel.ranking,
                    }
                    if len(buckets[ua_group]) >= bucket_size:
                        buckets_filled.add(ua_group)

    # Prepare result
    bucket_parcels = []
    for bucket in buckets:
        for parcel in buckets[bucket]:
            bucket_parcels.append(buckets[bucket][parcel])

    return pd.DataFrame(bucket_parcels)
