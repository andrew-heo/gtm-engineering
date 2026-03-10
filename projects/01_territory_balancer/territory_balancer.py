#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 19:54:31 2026

@author: heoandrew
"""

import os
import random
from dataclasses import dataclass

import numpy as np
import pandas as pd

COMMIT_SFDC = False

if COMMIT_SFDC:
    from simple_salesforce import Salesforce
    SFDC_CONFIG = {
    "username": "andrew.heo@company.com",
    "password": "MySuperSecretPassword123",
    "security_token": "XYZ123ABC456TOKEN",
    "domain": "login"   # use "test" for sandbox
    }

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)


RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

CSMS = [f"CSM_{i+1}" for i in range(10)]
RENEWAL_QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

EXPORT_PATH = "/Users/heoandrew/Desktop/GTM Eng/Euclid"
EXPORT = False

@dataclass
class TerritoryDistanceResult:
    sum_euclidean_distance_between_csm_book_averages_and_population_averages: float


def create_synthetic_dataset(accounts_per_csm=30):
    total_number_of_accounts = len(CSMS) * accounts_per_csm
    rows = []

    for i in range(total_number_of_accounts):
        account_mrr = np.random.lognormal(mean=7.9, sigma=0.55)
        account_mrr = int(np.clip(account_mrr, 500, 15000))

        if account_mrr < 1500:
            number_of_products_used = np.random.choice([1, 2], p=[0.7, 0.3])
        elif account_mrr < 3000:
            number_of_products_used = np.random.choice([1, 2, 3], p=[0.2, 0.5, 0.3])
        elif account_mrr < 6000:
            number_of_products_used = np.random.choice([2, 3, 4], p=[0.2, 0.5, 0.3])
        else:
            number_of_products_used = np.random.choice([3, 4, 5], p=[0.25, 0.45, 0.30])

        if account_mrr < 1500:
            icp_tier = np.random.choice([1, 2, 3], p=[0.5, 0.35, 0.15])
        elif account_mrr < 3000:
            icp_tier = np.random.choice([2, 3, 4], p=[0.3, 0.5, 0.2])
        elif account_mrr < 6000:
            icp_tier = np.random.choice([3, 4, 5], p=[0.25, 0.5, 0.25])
        else:
            icp_tier = np.random.choice([4, 5], p=[0.4, 0.6])

        renewal_quarter = np.random.choice(
            RENEWAL_QUARTERS,
            p=[0.23, 0.24, 0.24, 0.29]
        )

        rows.append(
            {
                "account_id": f"A{i + 1:04d}",
                "Renewal Quarter": renewal_quarter,
                "Account MRR": account_mrr,
                "Number of products used": number_of_products_used,
                "ICP Tier": icp_tier,
                "Current owner": None,
                "Must keep with current owner": False,
            }
        )

    dataset = pd.DataFrame(rows)

    shuffled_index = np.random.permutation(dataset.index)

    current_owners = []
    for csm in CSMS:
        current_owners.extend([csm] * accounts_per_csm)

    dataset.loc[shuffled_index, "Current owner"] = current_owners

    csm_with_high_accounts = "CSM_1"
    csm_with_low_accounts = "CSM_2"

    indices_of_highest_mrr_accounts = dataset.nlargest(12, "Account MRR").index.tolist()
    indices_of_lowest_mrr_accounts = dataset.nsmallest(12, "Account MRR").index.tolist()

    for target_csm, donor_indices in [
        (csm_with_high_accounts, indices_of_highest_mrr_accounts),
        (csm_with_low_accounts, indices_of_lowest_mrr_accounts),
    ]:
        for donor_idx in donor_indices:
            donor_current_owner = dataset.at[donor_idx, "Current owner"]

            if donor_current_owner == target_csm:
                continue

            possible_swap_indices = dataset[dataset["Current owner"] == target_csm].index.tolist()

            if not possible_swap_indices:
                continue

            swap_idx = random.choice(possible_swap_indices)
            swap_owner = dataset.at[swap_idx, "Current owner"]

            dataset.at[donor_idx, "Current owner"] = target_csm
            dataset.at[swap_idx, "Current owner"] = donor_current_owner

    for csm in [csm_with_high_accounts, csm_with_low_accounts]:
        indices_of_locked_accounts = (
            dataset[dataset["Current owner"] == csm]
            .sort_values("Account MRR", ascending=False)
            .head(2)
            .index
        )
        dataset.loc[indices_of_locked_accounts, "Must keep with current owner"] = True

    return dataset


def calculate_population_means_and_standard_deviations(df):
    columns_to_average = ["Account MRR", "Number of products used", "ICP Tier"]

    population_means = df[columns_to_average].mean().to_numpy()
    population_standard_deviations = df[columns_to_average].std().replace(0, 1).to_numpy()

    return population_means, population_standard_deviations


def calculate_csm_book_averages(df):
    columns_to_average = ["Account MRR", "Number of products used", "ICP Tier"]

    return (
        df.groupby("Current owner")[columns_to_average]
        .mean()
        .reset_index()
        .sort_values("Current owner")
    )


def sum_euclidean_distance_between_csm_book_averages_and_population_averages(df):
    population_means, population_standard_deviations = calculate_population_means_and_standard_deviations(df)
    csm_book_averages = calculate_csm_book_averages(df)

    sum_of_euclidean_distances = 0.0

    for _, row in csm_book_averages.iterrows():
        standardized_account_mrr_difference = (
            (row["Account MRR"] - population_means[0]) / population_standard_deviations[0]
        )
        standardized_number_of_products_used_difference = (
            (row["Number of products used"] - population_means[1]) / population_standard_deviations[1]
        )
        standardized_icp_tier_difference = (
            (row["ICP Tier"] - population_means[2]) / population_standard_deviations[2]
        )

        euclidean_distance = np.sqrt(
            standardized_account_mrr_difference ** 2
            + standardized_number_of_products_used_difference ** 2
            + standardized_icp_tier_difference ** 2
        )

        sum_of_euclidean_distances += euclidean_distance

    return TerritoryDistanceResult(
        sum_euclidean_distance_between_csm_book_averages_and_population_averages=sum_of_euclidean_distances
    )


def calculate_csm_book_statistics(df):
    csm_book_statistics = (
        df.groupby("Current owner")
        .agg(
            number_of_accounts=("account_id", "count"),
            average_account_mrr=("Account MRR", "mean"),
            average_number_of_products_used=("Number of products used", "mean"),
            average_icp_tier=("ICP Tier", "mean"),
            sum_of_account_mrr=("Account MRR", "sum"),
        )
        .reset_index()
        .sort_values("Current owner")
    )

    csm_book_renewal_quarter_counts = (
        df.pivot_table(
            index="Current owner",
            columns="Renewal Quarter",
            values="account_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )

    return csm_book_statistics.merge(
        csm_book_renewal_quarter_counts,
        on="Current owner",
    )


def get_target_number_of_accounts_per_csm(df):
    current_owner_counts = df["Current owner"].value_counts().to_dict()
    return {csm: current_owner_counts.get(csm, 0) for csm in CSMS}


def initialize_assignment_with_locked_accounts(df):
    working_dataset = df.copy()

    movable_account_mask = ~working_dataset["Must keep with current owner"]
    working_dataset.loc[movable_account_mask, "Current owner"] = None

    return working_dataset


def calculate_remaining_capacity_by_csm(df, target_number_of_accounts_per_csm):
    current_number_of_accounts_by_csm = df["Current owner"].value_counts().to_dict()

    return {
        csm: target_number_of_accounts_per_csm[csm] - current_number_of_accounts_by_csm.get(csm, 0)
        for csm in CSMS
    }


def calculate_maximum_number_of_accounts_per_csm_for_each_renewal_quarter(df):
    number_of_csms = len(CSMS)

    total_number_of_accounts_by_renewal_quarter = (
        df["Renewal Quarter"]
        .value_counts()
        .reindex(RENEWAL_QUARTERS, fill_value=0)
        .to_dict()
    )

    maximum_number_of_accounts_per_csm_for_each_renewal_quarter = {
        renewal_quarter: int(
            np.ceil(total_number_of_accounts_by_renewal_quarter[renewal_quarter] / number_of_csms)
        )
        for renewal_quarter in RENEWAL_QUARTERS
    }

    return maximum_number_of_accounts_per_csm_for_each_renewal_quarter


def calculate_current_number_of_accounts_for_each_renewal_quarter_for_one_csm(df, csm):
    csm_dataset = df[df["Current owner"] == csm]

    current_number_of_accounts_by_renewal_quarter = csm_dataset["Renewal Quarter"].value_counts().to_dict()

    return {
        renewal_quarter: current_number_of_accounts_by_renewal_quarter.get(renewal_quarter, 0)
        for renewal_quarter in RENEWAL_QUARTERS
    }


def csm_is_eligible_for_account_based_on_renewal_quarter_cap(
    df,
    account_idx,
    csm,
    target_number_of_accounts_per_csm,
    maximum_number_of_accounts_per_csm_for_each_renewal_quarter,
):
    remaining_capacity_by_csm = calculate_remaining_capacity_by_csm(df, target_number_of_accounts_per_csm)

    if remaining_capacity_by_csm[csm] <= 0:
        return False

    account_renewal_quarter = df.at[account_idx, "Renewal Quarter"]

    current_number_of_accounts_for_each_renewal_quarter_for_one_csm = (
        calculate_current_number_of_accounts_for_each_renewal_quarter_for_one_csm(df, csm)
    )

    current_number_of_accounts_for_that_renewal_quarter = (
        current_number_of_accounts_for_each_renewal_quarter_for_one_csm[account_renewal_quarter]
    )
    maximum_number_of_accounts_for_that_renewal_quarter = (
        maximum_number_of_accounts_per_csm_for_each_renewal_quarter[account_renewal_quarter]
    )

    return current_number_of_accounts_for_that_renewal_quarter < maximum_number_of_accounts_for_that_renewal_quarter


def assign_one_account(
    df,
    account_idx,
    target_number_of_accounts_per_csm,
    maximum_number_of_accounts_per_csm_for_each_renewal_quarter,
):
    candidate_assignment_results = []

    for csm in CSMS:
        if not csm_is_eligible_for_account_based_on_renewal_quarter_cap(
            df=df,
            account_idx=account_idx,
            csm=csm,
            target_number_of_accounts_per_csm=target_number_of_accounts_per_csm,
            maximum_number_of_accounts_per_csm_for_each_renewal_quarter=(
                maximum_number_of_accounts_per_csm_for_each_renewal_quarter
            ),
        ):
            continue

        test_dataset = df.copy()
        test_dataset.at[account_idx, "Current owner"] = csm

        assigned_accounts_only_dataset = test_dataset.dropna(subset=["Current owner"])

        territory_distance_result = (
            sum_euclidean_distance_between_csm_book_averages_and_population_averages(
                assigned_accounts_only_dataset
            )
        )

        candidate_assignment_results.append(
            (
                csm,
                territory_distance_result.sum_euclidean_distance_between_csm_book_averages_and_population_averages,
            )
        )

    # Fallback in case every CSM is already at the max for that quarter
    if not candidate_assignment_results:
        remaining_capacity_by_csm = calculate_remaining_capacity_by_csm(
            df, target_number_of_accounts_per_csm
        )

        for csm in CSMS:
            if remaining_capacity_by_csm[csm] <= 0:
                continue

            test_dataset = df.copy()
            test_dataset.at[account_idx, "Current owner"] = csm

            assigned_accounts_only_dataset = test_dataset.dropna(subset=["Current owner"])

            territory_distance_result = (
                sum_euclidean_distance_between_csm_book_averages_and_population_averages(
                    assigned_accounts_only_dataset
                )
            )

            candidate_assignment_results.append(
                (
                    csm,
                    territory_distance_result.sum_euclidean_distance_between_csm_book_averages_and_population_averages,
                )
            )

    candidate_assignment_results.sort(key=lambda x: x[1])

    return candidate_assignment_results[0][0]


def build_assignment(df, random_state=None):
    if random_state is not None:
        random.seed(random_state)
        np.random.seed(random_state)

    target_number_of_accounts_per_csm = get_target_number_of_accounts_per_csm(df)

    maximum_number_of_accounts_per_csm_for_each_renewal_quarter = (
        calculate_maximum_number_of_accounts_per_csm_for_each_renewal_quarter(df)
    )

    working_dataset = initialize_assignment_with_locked_accounts(df)

    unassigned_account_indices = working_dataset[
        working_dataset["Current owner"].isna()
    ].index.tolist()

    random.shuffle(unassigned_account_indices)

    # Seed one account into each CSM first
    for csm in CSMS:
        if not unassigned_account_indices:
            break

        remaining_capacity_by_csm = calculate_remaining_capacity_by_csm(
            working_dataset, target_number_of_accounts_per_csm
        )

        if remaining_capacity_by_csm[csm] <= 0:
            continue

        assigned_seed_account = False

        for i, account_idx in enumerate(unassigned_account_indices):
            if csm_is_eligible_for_account_based_on_renewal_quarter_cap(
                df=working_dataset,
                account_idx=account_idx,
                csm=csm,
                target_number_of_accounts_per_csm=target_number_of_accounts_per_csm,
                maximum_number_of_accounts_per_csm_for_each_renewal_quarter=(
                    maximum_number_of_accounts_per_csm_for_each_renewal_quarter
                ),
            ):
                working_dataset.at[account_idx, "Current owner"] = csm
                unassigned_account_indices.pop(i)
                assigned_seed_account = True
                break

        if not assigned_seed_account:
            account_idx = unassigned_account_indices.pop()
            working_dataset.at[account_idx, "Current owner"] = csm

    number_of_accounts_remaining_to_assign = len(unassigned_account_indices)
    next_progress_percentage_to_print = 10

    for i, account_idx in enumerate(unassigned_account_indices, start=1):
        best_csm_for_account = assign_one_account(
            df=working_dataset,
            account_idx=account_idx,
            target_number_of_accounts_per_csm=target_number_of_accounts_per_csm,
            maximum_number_of_accounts_per_csm_for_each_renewal_quarter=(
                maximum_number_of_accounts_per_csm_for_each_renewal_quarter
            ),
        )

        working_dataset.at[account_idx, "Current owner"] = best_csm_for_account

        progress_percentage = int((i / number_of_accounts_remaining_to_assign) * 100)

        if progress_percentage >= next_progress_percentage_to_print:
            print(f"    {next_progress_percentage_to_print}% assigned")
            next_progress_percentage_to_print += 10

    return working_dataset


def run_multiple_assignments(df, n_runs=10):
    best_assignment_dataset = None
    best_sum_euclidean_distance_between_csm_book_averages_and_population_averages = None
    best_run_number = None

    run_results = []

    for run_number in range(1, n_runs + 1):
        print(f"\nRunning assignment {run_number}/{n_runs}")

        seed_for_this_run = RANDOM_SEED + run_number

        candidate_assignment_dataset = build_assignment(
            df=df,
            random_state=seed_for_this_run,
        )

        territory_distance_result = (
            sum_euclidean_distance_between_csm_book_averages_and_population_averages(
                candidate_assignment_dataset
            )
        )

        candidate_sum_euclidean_distance_between_csm_book_averages_and_population_averages = (
            territory_distance_result.sum_euclidean_distance_between_csm_book_averages_and_population_averages
        )

        print(
            "Run "
            f"{run_number} distance = "
            f"{candidate_sum_euclidean_distance_between_csm_book_averages_and_population_averages:.4f}"
        )

        run_results.append(
            {
                "run_number": run_number,
                "sum_euclidean_distance_between_csm_book_averages_and_population_averages": (
                    candidate_sum_euclidean_distance_between_csm_book_averages_and_population_averages
                ),
            }
        )

        if (
            best_sum_euclidean_distance_between_csm_book_averages_and_population_averages is None
            or candidate_sum_euclidean_distance_between_csm_book_averages_and_population_averages
            < best_sum_euclidean_distance_between_csm_book_averages_and_population_averages
        ):
            best_sum_euclidean_distance_between_csm_book_averages_and_population_averages = (
                candidate_sum_euclidean_distance_between_csm_book_averages_and_population_averages
            )
            best_assignment_dataset = candidate_assignment_dataset.copy()
            best_run_number = run_number

            print(
                "New best run so far: "
                f"run {best_run_number}, "
                f"distance = "
                f"{best_sum_euclidean_distance_between_csm_book_averages_and_population_averages:.4f}"
            )

    run_summary = pd.DataFrame(run_results).sort_values(
        "sum_euclidean_distance_between_csm_book_averages_and_population_averages"
    )

    print("\nBEST RUN STATISTICS")
    print(f"Best run number: {best_run_number}")
    print(
        "Lowest sum_euclidean_distance_between_csm_book_averages_and_population_averages: "
        f"{best_sum_euclidean_distance_between_csm_book_averages_and_population_averages:.4f}"
    )

    return best_assignment_dataset, run_summary


def main():
    os.makedirs(EXPORT_PATH, exist_ok=True)

    original_dataset = create_synthetic_dataset(accounts_per_csm=30)

    print("\nORIGINAL DATASET CSM BOOK STATISTICS")
    original_dataset_csm_book_statistics = calculate_csm_book_statistics(original_dataset)
    print(original_dataset_csm_book_statistics)

    original_dataset_distance = (
        sum_euclidean_distance_between_csm_book_averages_and_population_averages(
            original_dataset
        )
    )

    print("\nORIGINAL DATASET EUCLIDEAN DISTANCE")
    print(
        original_dataset_distance
        .sum_euclidean_distance_between_csm_book_averages_and_population_averages
    )

    best_assignment_dataset, run_summary = run_multiple_assignments(
        df=original_dataset,
        n_runs=10,
    )

    print("\nRUN SUMMARY")
    print(run_summary)

    print("\nBEST ASSIGNMENT CSM BOOK STATISTICS")
    best_assignment_csm_book_statistics = calculate_csm_book_statistics(
        best_assignment_dataset
    )
    print(best_assignment_csm_book_statistics)

    best_assignment_distance = (
        sum_euclidean_distance_between_csm_book_averages_and_population_averages(
            best_assignment_dataset
        )
    )

    print("\nBEST ASSIGNMENT EUCLIDEAN DISTANCE")
    print(
        best_assignment_distance
        .sum_euclidean_distance_between_csm_book_averages_and_population_averages
    )
    if EXPORT:
        original_dataset.to_csv(
            f"{EXPORT_PATH}/territory_input_dataset.csv",
            index=False,
        )
        best_assignment_dataset.to_csv(
            f"{EXPORT_PATH}/territory_best_assignment.csv",
            index=False,
        )
        run_summary.to_csv(
            f"{EXPORT_PATH}/territory_run_summary.csv",
            index=False,
        )
    if COMMIT_SFDC:
        sfdc = best_assignment_dataset.rename(columns={"account_id":"id", "Current owner":"ownerid"})
        sfdc = sfdc[["id", "ownerid"]]
        payload = sfdc.to_dict("records")
        def connect_to_salesforce():
            sf = Salesforce(
                username=SFDC_CONFIG["username"],
                password=SFDC_CONFIG["password"],
                security_token=SFDC_CONFIG["security_token"],
                domain=SFDC_CONFIG["domain"]
            )
            return sf
        def push_updates_to_salesforce(sf, payload):
            print(f"Pushing {len(payload)} account updates to Salesforce")
            results = sf.bulk.Account.update(payload)
            print("Salesforce update complete")
            return results

if __name__ == "__main__":
    main()
