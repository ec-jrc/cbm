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

from typing import Dict, Union
import pandas as pd


def fill_buckets_2024(
    parcels_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    bucket_size: Union[int, Dict[str, int]],
    skip_parcels_0_ua_groups: bool,
    capping: float = -1,
    print_progress: bool = False,
) -> pd.DataFrame:
    """
    Simulation to fill buckets according to new rules of 2024.

    Notes:
      - this has been developed only for simulation purposes, so is not to be treated as
        production ready code and hasn't been thoroughly tested.

    Args:
        parcels_df (pd.DataFrame): DataFrame with parcels. Expected columns:
            ["parcel_id", "holding_id", "ua_group"].
        ranking_df (pd.DataFrame): DataFrame with parcel ranking. Expected columns:
            ["parcel_id", "ranking"].
        bucket_size (int, dict): Either an int with the maximum number of parcels per
            bucket for all "ua_group"s, or a dict with for each ua_group the maximum
            number that should be in the corresponding bucket.
        skip_parcels_0_ua_groups (bool): Skip parcels that at the moment they are
            reached in the ranking belong to no ua groups anymore. This results in
            3% fewer unique parcels and 25% fewer unique holdings in the buckets.
        capping (int or float): If >= 1, the maximum number of holdings to use for the
            selection when capping is used. If between 0 and 1, the maximum fraction
            of holdings in parcels_df to use for the selection. If value is -1, no
            capping is applied. Defaults to -1.
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
    if capping > 0 and capping < 1:
        nb_holdings = parcels_df["holding_id"].nunique()
        nb_holdings_max = int(nb_holdings * capping)
        print(f"{capping=} with {nb_holdings=}: max {nb_holdings_max} holdings")
        capping = nb_holdings_max

    # Join ranking data with the parcel data
    parcels_all_df = parcels_df.merge(ranking_df, on="parcel_id")

    # Recreate ranking df with holding_id added + sort on ranking
    ranking_df = (
        parcels_all_df[["parcel_id", "holding_id", "ranking"]]
        .drop_duplicates()
        .sort_values(["ranking"])
    )

    # Created indexed dataframes for performance
    parcels_p_df = parcels_all_df.set_index("parcel_id", drop=False)
    parcels_h_df = parcels_all_df.set_index("holding_id", drop=False)

    # Init buckets
    buckets = {}
    buckets_needed = set(parcels_all_df["ua_group"].unique())
    for ua_group in buckets_needed:
        buckets[ua_group] = {}

    # If bucket_size is a single int, prepare a dict with bucket sizes to simplify the
    # code coming later on.
    if isinstance(bucket_size, int):
        bucket_size_dict = {}
        for ua_group in buckets_needed:
            bucket_size_dict[ua_group] = bucket_size
        bucket_size = bucket_size_dict

    # Loop through parcels
    buckets_filled = set()
    holdings_treated = set()
    holdings_used = set()
    parcels_used = set()
    nb_buckets_filled = 0

    go_on = True
    capping_reached = False
    while go_on:
        # By default, one iteration is enough. If needed, go_on will be set to True
        # again in the loop later on.
        go_on = False

        # Once the capping number is reached, remove all parcels of holdings that aren't
        # treated yet from the ranked list.
        if capping_reached:
            ranking_df = ranking_df[ranking_df["holding_id"].isin(holdings_used)]
            ranking_df = ranking_df[~ranking_df["parcel_id"].isin(parcels_used)]

        for counter, parcel in enumerate(ranking_df.itertuples()):
            if buckets_filled == buckets_needed:
                break

            # If current parcel only has ua_groups that are already filled up, skip it.
            parcel_ua_groups = None
            if skip_parcels_0_ua_groups:
                parcel_ua_groups = set(
                    parcels_p_df.loc[parcels_p_df.index == parcel.parcel_id]["ua_group"]
                )
                if len(parcel_ua_groups - buckets_filled) == 0:
                    continue

            # Apply capping if the relevant number of holdings used is reached.
            if not capping_reached and capping != -1:
                if len(holdings_used) == capping:
                    capping_reached = True
                    go_on = True
                    break
                if len(holdings_used) > capping:
                    raise RuntimeError(f"{capping=} but {len(holdings_used)=}?")

            # Extra buckets filled, so filter the parcel DataFrame some more.
            if len(buckets_filled) > nb_buckets_filled:
                parcels_p_df = parcels_p_df[~parcels_p_df.ua_group.isin(buckets_filled)]
                parcels_h_df = parcels_p_df.set_index("holding_id", drop=False)
                nb_buckets_filled = len(buckets_filled)

            if print_progress and counter % 10000 == 0:
                print(f"processed {counter} parcels of {len(ranking_df)}")

            # The holding of the parcel hasn't been treated yet.
            if parcel.holding_id not in holdings_treated:
                holdings_treated.add(parcel.holding_id)

                # Get the parcels of the holding
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
                        holdings_used.add(parcel_ua_group.holding_id)
                        parcels_used.add(parcel_ua_group.parcel_id)

                        # Only up till bucket size in bucket
                        if len(buckets[ua_group]) >= bucket_size[ua_group]:
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
                    parcel_ua_groups = parcels_p_df.loc[
                        parcels_p_df.index == parcel.parcel_id
                    ]["ua_group"].unique()
                for ua_group in parcel_ua_groups:
                    if parcel.parcel_id not in buckets[ua_group]:
                        buckets[ua_group][parcel.parcel_id] = {
                            "bucket": ua_group,
                            "parcel_id": parcel.parcel_id,
                            "holding_id": parcel.holding_id,
                            "ua_group": ua_group,
                            "ranking": parcel.ranking,
                        }
                        holdings_used.add(parcel.holding_id)
                        parcels_used.add(parcel.parcel_id)
                        if len(buckets[ua_group]) >= bucket_size[ua_group]:
                            buckets_filled.add(ua_group)

    # If capping was applied and there are empty buckets, add the parsels from the first
    # holding with parcels with the relevant ua_group to that bucket to avoid it being
    # empty
    if capping_reached:
        for ua_group in buckets:
            if len(buckets[ua_group]) == 0:
                # Get parcels with the relevant ua_group, sorted by ranking
                parcels_ua_group_df = parcels_all_df.loc[
                    parcels_all_df.ua_group == ua_group
                ].sort_values(["ranking"])

                # Get the holding_id of the first parcel
                holding_id = parcels_ua_group_df["holding_id"].iloc[0]

                # Add all parcels with this ua_group of this holding to the bucket, with
                # a maximum of bucket_size
                parcels_holding_df = parcels_ua_group_df.loc[
                    parcels_all_df.holding_id == holding_id
                ].head(bucket_size[ua_group])
                for parcel in parcels_holding_df.itertuples():
                    buckets[ua_group][parcel.parcel_id] = {
                        "bucket": ua_group,
                        "parcel_id": parcel.parcel_id,
                        "holding_id": parcel.holding_id,
                        "ua_group": ua_group,
                        "ranking": parcel.ranking,
                    }

    # Prepare result
    bucket_parcels = []
    for bucket in buckets:
        for parcel in buckets[bucket]:
            bucket_parcels.append(buckets[bucket][parcel])

    return pd.DataFrame(bucket_parcels)
