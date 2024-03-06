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

from datetime import datetime
from pathlib import Path
import pandas as pd


def fill_buckets_2024(
    parcels_df: pd.DataFrame, max_parcels_per_bucket: int, print_progress: bool = False
) -> pd.DataFrame:
    """
    Simulation to fill buckets according to new rules of 2024.

    Notes:
      - this has been developed only for simulation purposes, so is not to be treated as
        production ready code and hasn't been thouroughly tested.
      - there is no support (yet) for the 3 % capping rule.
      - there is no support (yet) for different bucket sizes per unit amount.

    Args:
        parcels_df (pd.DataFrame): dataframe with parcels
        max_parcels_per_bucket (int): maximum number of parcels per bucket
        print_progress (bool, optional): True to print some progress. Defaults to False.

    Returns:
        pd.DataFrame: the filled up buckets.
    """
    parcels_sorted_df = parcels_df.sort_values(["ranking"])

    treated_parcels = set()
    treated_holdings = set()

    # Init buckets
    bucket_parcels_dict = {}
    buckets_needed = set(parcels_df["ua_group"].unique())
    for ua_group in buckets_needed:
        bucket_parcels_dict[ua_group] = {}

    # Keep looping till all buckers are filled or if we get till the end of the ranked
    # parcel list.
    buckets_filled = set()
    prc_counter = 0
    while buckets_filled != buckets_needed:
        # We got till the end of the parcel loop without getting all buckets filled :-(.
        if prc_counter >= len(parcels_sorted_df):
            print("No more parcels to loop :-(...")
            break
        prc_counter = 0

        # Only keep parcels that are relevant for UA groups for which the buckets aren't
        # filled up yet.
        parcels_sorted_df = parcels_sorted_df[
            ~parcels_sorted_df.ua_group.isin(buckets_filled)
        ]

        # Loop through parcels
        restart_prc_loop = False
        for prc in parcels_sorted_df.itertuples():
            # A bucket was filled in the previous iteration, so filter list first to get
            # some speedup.
            if restart_prc_loop:
                break

            prc_counter += 1
            if print_progress and prc_counter % 10000 == 0:
                print(f"processed {prc_counter} parcels of {len(parcels_sorted_df)}")
            if prc.parcel_id in treated_parcels:
                continue
            treated_parcels.add(prc.parcel_id)

            if prc.holding_id not in treated_holdings:
                treated_holdings.add(prc.holding_id)
                # All parcels of the holding, sorted on ranking
                prc_of_holding_df = parcels_df.loc[
                    parcels_df.holding_id == prc.holding_id
                ].sort_values(["ranking"])

                # Loop over ua_groups in holding
                for ua_group in prc_of_holding_df["ua_group"].unique():
                    # Never more than max_parcels_per_bucket in bucket
                    if len(bucket_parcels_dict[ua_group]) >= max_parcels_per_bucket:
                        if ua_group not in buckets_filled:
                            buckets_filled.add(ua_group)
                            restart_prc_loop = True
                        continue
                    prc_groep_df = prc_of_holding_df.loc[
                        prc_of_holding_df.ua_group == ua_group
                    ]
                    nb_added = 0
                    for prc_groep in prc_groep_df.itertuples():
                        if prc_groep.parcel_id not in bucket_parcels_dict[ua_group]:
                            bucket_parcels_dict[ua_group][prc_groep.parcel_id] = {
                                "bucket": ua_group,
                                "parcel_id": prc_groep.parcel_id,
                                "holding_id": prc_groep.holding_id,
                                "ua_group": ua_group,
                                "ranking": prc_groep.ranking,
                            }
                            nb_added += 1

                            # Add only 3 parcels per holding to a bucket
                            if nb_added >= 3:
                                break
                            # Only up till general maximum in bucket
                            if (
                                len(bucket_parcels_dict[ua_group])
                                >= max_parcels_per_bucket
                            ):
                                if ua_group not in buckets_filled:
                                    buckets_filled.add(ua_group)
                                    restart_prc_loop = True
                                break

            else:
                # Holding has already been processed... just try to add this single
                # parcel to each relevant bucket if it isn't in it yet.

                # All ua_groups of parcel
                prc_ua_groupen_df = parcels_df.loc[
                    parcels_df.parcel_id == prc.parcel_id
                ]
                # Loop over ua_groups in holding
                for ua_group in prc_ua_groupen_df["ua_group"].unique():
                    # Never more than max_parcels_per_bucket in bucket
                    if len(bucket_parcels_dict[ua_group]) >= max_parcels_per_bucket:
                        buckets_filled.add(ua_group)
                        restart_prc_loop = True
                        continue
                    if prc.parcel_id not in bucket_parcels_dict[ua_group]:
                        bucket_parcels_dict[ua_group][prc_groep.parcel_id] = {
                            "bucket": ua_group,
                            "parcel_id": prc.parcel_id,
                            "holding_id": prc.holding_id,
                            "ua_group": ua_group,
                            "ranking": prc.ranking,
                        }

    # Prepare result
    bucket_parcels = []
    for bucket in bucket_parcels_dict:
        for prc in bucket_parcels_dict[bucket]:
            bucket_parcels.append(bucket_parcels_dict[bucket][prc])

    return pd.DataFrame(bucket_parcels)


def test_MT():
    # Input
    input_dir = Path(__file__).resolve().parent / "data"
    bucket_size = 4

    # Read input data
    gsa_df = pd.read_csv(input_dir / "MT_GSA.csv").set_index("parcel_ID")
    ranking_df = pd.read_csv(input_dir / "MT_ranked_list.csv").set_index("parcel_ID")

    # Join gsa and ranking
    df = gsa_df.join(ranking_df).reset_index()

    # Rename columns to be compatible with BEFL names
    df = df.rename(
        columns={
            "parcel_ID": "parcel_id",
            "scheme": "ua_group",
            "farmer_ID": "holding_id",
            "rank_ID": "ranking",
        }
    )

    output_dir = input_dir

    start_time = datetime.now()
    name = f"sim_{bucket_size}P_2024_MT"
    buckets_MT_2024_df = fill_buckets_2024(df, max_parcels_per_bucket=bucket_size)
    simulation = {
        "name": name,
        "descr": (
            "Grouped Small Buckets, "
            "300 first ranked Parcels, 3 parcels/holding, "
            "rules of 2024"
        ),
        "total parcels": len(buckets_MT_2024_df),
        "unique parcels": len(buckets_MT_2024_df.parcel_id.unique()),
        "unique holdings": len(buckets_MT_2024_df.holding_id.unique()),
    }
    buckets_MT_2024_df.to_excel(output_dir / f"{name}.xlsx")
    print(simulation)
    print(f"{name} took {datetime.now()-start_time}")


if __name__ == "__main__":
    test_MT()
