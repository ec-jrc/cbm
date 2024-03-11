from datetime import datetime
from pathlib import Path
from random import shuffle

import pandas as pd

from iacs_qa.BEFL.BEFL_fillbuckets_2024 import fill_buckets_2024


def calculate_BEFL():
    # Input
    input_dir = Path(
        "X:/__IT_TEAM_ANG_GIS/Taken/2024/2024-01-16_AMS_simulaties_buckets/dev_run"
    )
    input1_path = input_dir / "BE-FL_gsa_ua_claimed_2023_INTERN_deel_1.csv"
    input2_path = input_dir / "BE-FL_gsa_ua_claimed_2023_INTERN_deel_2.csv"
    input_path = input_dir / "BE-FL_gsa_ua_claimed_2023_INTERN_full.csv"
    bucket_size = 330
    te_negeren_groeperingen = ["RB41", "RB45", "BB41", "BS41"]

    # Lees en prepareer input data
    # ----------------------------
    if input_path.exists():
        df = pd.read_csv(input_path, sep=";")
    else:
        df = pd.concat(
            [
                pd.read_csv(input1_path, sep=";"),
                pd.read_csv(input2_path, sep=";"),
            ]
        )

        # Geef een random nummer aan elke perceel: RANKING
        ref_ids = df["GSA_PAR_ID"].unique()
        shuffle(ref_ids)
        ref_ids = pd.DataFrame(ref_ids, columns=["GSA_PAR_ID"])
        # Switch index and GSA_PAR_ID, as we want the index to be the RANKING
        ref_ids = pd.DataFrame(
            ref_ids.index, columns=["RANKING"], index=ref_ids["GSA_PAR_ID"]
        )

        # Vervang de bestaande (foute) ranking door de nieuwe
        df = df.drop(columns=["RANKING"])
        df = df[df["UA"] != "3_2_a2 "]
        df = df.join(ref_ids, on="GSA_PAR_ID")

        # Schrijf weg
        df.to_csv(input_path, sep=";", index=False)

    # Negeer/filter opgegeven groepen
    df = df[~df["GROEPERING"].isin(te_negeren_groeperingen)]

    # Groepeer kleine groepen tot 1200 percelen
    df.loc[df["GROEPERING"].isin(["BRB", "HD"]), "GROEPERING"] = "BRB,HD"
    df.loc[df["GROEPERING"].isin(["RB41", "BS41"]), "GROEPERING"] = "RB41,BS41"
    df.loc[df["GROEPERING"].isin(["EEH1", "PK"]), "GROEPERING"] = "EEH1,PK"
    df.loc[df["GROEPERING"].isin(["OCS", "BUK,BUB"]), "GROEPERING"] = "OCS,BUK,BUB"
    df.loc[
        df["GROEPERING"].isin(["EEH3b", "EEH2b", "EEH2a", "EEH3a"]), "GROEPERING"
    ] = "EEH3b,EEH2b,EEH2a,EEH3a"
    df.loc[df["GROEPERING"].isin(["RB45", "BB41"]), "GROEPERING"] = "RB45,BB41"
    df.loc[
        df["GROEPERING"].isin(["TBG", "MEG", "BLO", "MET", "BFB", "EEN", "BFR", "MEL"]),
        "GROEPERING",
    ] = "TBG,MEG,BLO,MET,BFB,EEN,BFR,MEL"

    df = df.rename(
        columns={
            "GSA_PAR_ID": "parcel_id",
            "LB_NMR": "holding_id",
            "RANKING": "ranking",
            "GROEPERING": "ua_group",
        }
    )
    parcels_df = df[["parcel_id", "holding_id", "ua_group"]]
    ranking_df = df[["parcel_id", "ranking"]].drop_duplicates()

    start = datetime.now()
    buckets_test_df = fill_buckets_2024(
        parcels_df,
        ranking_df,
        bucket_size=bucket_size,
        skip_parcels_0_ua_groups=True,
        print_progress=True,
    )
    print(f"took {datetime.now() - start}")

    simulation = {
        "name": "run BEFL",
        "descr": (
            "Grouped Small Buckets, "
            "300 first ranked Parcels, 3 parcels/holding, "
            "rules of 2024"
        ),
        "total parcels": len(buckets_test_df),
        "unique parcels": len(buckets_test_df.parcel_id.unique()),
        "unique holdings": len(buckets_test_df.holding_id.unique()),
    }
    print(simulation)
    assert all(buckets_test_df.groupby(by=["bucket"]).count() == bucket_size)


if __name__ == "__main__":
    calculate_BEFL()
