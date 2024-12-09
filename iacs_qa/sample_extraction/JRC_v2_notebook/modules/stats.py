def calculate_holding_with_most_interventions_selected(datamanager):
    # calculate the holding with the most interventions selected
    holding_interventions = {}
    for bucket in datamanager.final_bucket_state.values():
        for parcel in bucket["parcels"]:
            holding = parcel["gsa_hol_id"]
            if holding in holding_interventions:
                holding_interventions[holding] += 1
            else:
                holding_interventions[holding] = 1
    holding_with_most_interventions = max(holding_interventions, key=holding_interventions.get)
    return holding_with_most_interventions, holding_interventions[holding_with_most_interventions]


def all_parcels_in_buckets(buckets):
    """
    Count all parcels in buckets. Identify parcels by their par_id and hol_id.
    """
    all_parcels = []
    for bucket in buckets.values():
        for parcel in bucket["parcels"]:
            unique_parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
            all_parcels.append(unique_parcel_id)
    return set(all_parcels)

def count_unique_selected_parcels_per_holding(all_selected_parcels):
    parcels_per_holding = {}
    for a in all_selected_parcels:
        par_id = a.split("_")[0]
        hol_id = a.split("_")[1]
        if hol_id in parcels_per_holding:
            parcels_per_holding[hol_id].add(par_id)
        else:
            parcels_per_holding[hol_id] = {par_id}

    # count the number of unique parcels per holding
    count_per_holding = {hol_id: len(parcels) for hol_id, parcels in parcels_per_holding.items()}

    # calculate the average number of parcels per holding
    avg_parcels_per_holding = sum(count_per_holding.values()) / len(count_per_holding)
    return count_per_holding, avg_parcels_per_holding

def count_selected_covered_parcels(datamanager):
    covered_parcels = []
    noncovered_parcels = []
    for bucket in datamanager.final_bucket_state.values():
        for parcel in bucket["parcels"]:
            unique_parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
            if parcel["covered"] == 1:
                covered_parcels.append(unique_parcel_id)
            else:
                noncovered_parcels.append(unique_parcel_id)

    return len(set(covered_parcels)), len(set(noncovered_parcels))


def calculate_stats_for_reused_parcels(datamanager):
    counts_for_parcels = {}

    for bucket_id, bucket in datamanager.final_bucket_state.items():
        for parcel in bucket["parcels"]:
            parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
            if parcel_id in counts_for_parcels:
                counts_for_parcels[parcel_id] += 1
            else:
                counts_for_parcels[parcel_id] = 1

    histogram_buckets = {}
    for parcel_id, count in counts_for_parcels.items():
        if count in histogram_buckets:
            histogram_buckets[count] += 1
        else:
            histogram_buckets[count] = 1
    
    return histogram_buckets


def calculate_summary_stats(datamanager):
    summary_stats = {}

    total_rows = len(datamanager.parcels_df)
    selected_rows = sum([len(bucket['parcels']) for bucket in datamanager.final_bucket_state.values()])
    summary_stats['total_rows'] = total_rows
    summary_stats['selected_rows'] = selected_rows

    all_unique_parcels_count = len(datamanager.parcels_df.drop_duplicates(subset=["gsa_par_id", "gsa_hol_id"]))
    all_selected_parcels = all_parcels_in_buckets(datamanager.final_bucket_state)
    all_selected_parcels_count = len(all_selected_parcels)
    summary_stats['all_unique_parcels_count'] = all_unique_parcels_count
    summary_stats['all_selected_parcels_count'] = all_selected_parcels_count

    avg_par_per_hol = count_unique_selected_parcels_per_holding(all_selected_parcels)[1]
    summary_stats['avg_par_per_hol'] = avg_par_per_hol

    total_holdings = len(datamanager.parcels_df["gsa_hol_id"].unique())
    selected_holdings = len(datamanager.added_holdings)
    summary_stats['total_holdings'] = total_holdings
    summary_stats['selected_holdings'] = selected_holdings

    avg_int_per_holding = selected_rows / selected_holdings
    summary_stats['avg_int_per_holding'] = avg_int_per_holding

    most_interventions = calculate_holding_with_most_interventions_selected(datamanager)
    summary_stats['most_interventions'] = most_interventions

    covered, noncovered = count_selected_covered_parcels(datamanager)
    summary_stats['covered_parcels'] = covered
    summary_stats['noncovered_parcels'] = noncovered

    bucket_stats = {}
    for bucket_id, info in datamanager.ua_groups.items():
        bucket_stats[bucket_id] = {
            'label': info["desc"],
            'selected': len(datamanager.final_bucket_state[bucket_id]["parcels"]),
            'total': info["count"],
            'target': info["target"]
        }
    summary_stats['bucket_stats'] = bucket_stats

    return summary_stats