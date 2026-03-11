#!/usr/bin/env python3
"""Balance SMB and Mid-Market AM territories using the shared synthetic GTM dataset."""

from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gtm_engineering.config import DATA_DIR, DEFAULT_RANDOM_SEED, TERRITORY_BALANCER_DIR
from gtm_engineering.synthetic_data import load_sample_data


OUTPUT_DIR = TERRITORY_BALANCER_DIR / "output"
RENEWAL_QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
FEATURE_COLUMNS = ["account_mrr", "products_used", "icp_tier"]
AM_ROLE = "AM"
OWNER_COUNT_PENALTY_MULTIPLIER = 0.20
TOP_RECOMMENDATIONS_TO_PRINT = 15
SALESFORCE_ACCOUNT_OBJECT = "Account"
SALESFORCE_OWNER_FIELD_NAME = "OwnerId"
PAID_ACCOUNT_MRR_THRESHOLD = 0
BALANCED_ACCOUNT_SEGMENTS = {"SMB", "Mid-Market"}


def prepare_accounts(accounts: pd.DataFrame, owners: pd.DataFrame) -> pd.DataFrame:
    accounts = accounts[
        (accounts["account_mrr"] > PAID_ACCOUNT_MRR_THRESHOLD)
        & (accounts["account_segment"].isin(BALANCED_ACCOUNT_SEGMENTS))
        & (accounts["owner_role"] == AM_ROLE)
    ].copy()
    accounts["current_owner_name"] = accounts["owner_name"]
    return accounts


def calculate_book_statistics(accounts: pd.DataFrame) -> pd.DataFrame:
    territory_summary = (
        accounts.groupby("current_owner_name")
        .agg(
            account_count=("account_id", "count"),
            avg_mrr=("account_mrr", "mean"),
            avg_products=("products_used", "mean"),
            avg_icp=("icp_tier", "mean"),
            total_mrr=("account_mrr", "sum"),
        )
        .reset_index()
    )

    renewal_mix = (
        accounts.pivot_table(
            index="current_owner_name",
            columns="renewal_quarter",
            values="account_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )

    territory_summary = territory_summary.merge(renewal_mix, on="current_owner_name", how="left")
    for renewal_quarter in RENEWAL_QUARTERS:
        if renewal_quarter not in territory_summary.columns:
            territory_summary[renewal_quarter] = 0

    return territory_summary.sort_values("current_owner_name").reset_index(drop=True)


def build_owner_state(accounts: pd.DataFrame, owner_names: list[str]) -> dict[str, dict[str, object]]:
    owner_state_by_name = {
        owner_name: {
            "count": 0,
            "feature_sums": np.zeros(len(FEATURE_COLUMNS), dtype=float),
            "quarter_counts": {quarter: 0 for quarter in RENEWAL_QUARTERS},
        }
        for owner_name in owner_names
    }

    assigned = accounts.dropna(subset=["current_owner_name"])
    for row in assigned.itertuples(index=False):
        owner_state = owner_state_by_name[row.current_owner_name]
        owner_state["count"] += 1
        owner_state["feature_sums"] += np.array([row.account_mrr, row.products_used, row.icp_tier], dtype=float)
        owner_state["quarter_counts"][row.renewal_quarter] += 1

    return owner_state_by_name


def local_assignment_score(
    owner_state: dict[str, object],
    account_row: pd.Series,
    population_means: np.ndarray,
    population_stds: np.ndarray,
    target_count: int,
) -> float:
    new_count = int(owner_state["count"]) + 1
    new_feature_sums = owner_state["feature_sums"] + np.array(
        [account_row["account_mrr"], account_row["products_used"], account_row["icp_tier"]],
        dtype=float,
    )
    new_means = new_feature_sums / new_count
    standardized_distance = np.sqrt((((new_means - population_means) / population_stds) ** 2).sum())
    count_penalty = abs(target_count - new_count) * OWNER_COUNT_PENALTY_MULTIPLIER
    return float(standardized_distance + count_penalty)


def assign_accounts(accounts: pd.DataFrame, owner_names: list[str]) -> pd.DataFrame:
    working = accounts.copy()
    movable_mask = ~working["must_keep_with_owner"].astype(bool)
    working.loc[movable_mask, "current_owner_name"] = None

    population_means = working[FEATURE_COLUMNS].mean().to_numpy()
    population_stds = working[FEATURE_COLUMNS].std().replace(0, 1).to_numpy()
    target_counts = accounts["current_owner_name"].value_counts().to_dict()
    quarter_caps = {
        quarter: int(np.ceil((working["renewal_quarter"] == quarter).sum() / len(owner_names)))
        for quarter in RENEWAL_QUARTERS
    }

    owner_state_by_name = build_owner_state(working, owner_names)
    unassigned_indices = working[working["current_owner_name"].isna()].index.tolist()
    random.shuffle(unassigned_indices)

    for account_index in unassigned_indices:
        account_row = working.loc[account_index]
        candidate_scores = []

        for owner_name in owner_names:
            owner_state = owner_state_by_name[owner_name]
            target_count = target_counts.get(owner_name, 0)
            if int(owner_state["count"]) >= target_count:
                continue
            if owner_state["quarter_counts"][account_row["renewal_quarter"]] >= quarter_caps[account_row["renewal_quarter"]]:
                continue

            candidate_scores.append(
                (
                    owner_name,
                    local_assignment_score(
                        owner_state=owner_state,
                        account_row=account_row,
                        population_means=population_means,
                        population_stds=population_stds,
                        target_count=target_count,
                    ),
                )
            )

        if not candidate_scores:
            for owner_name in owner_names:
                owner_state = owner_state_by_name[owner_name]
                target_count = target_counts.get(owner_name, 0)
                if int(owner_state["count"]) >= target_count:
                    continue
                candidate_scores.append(
                    (
                        owner_name,
                        local_assignment_score(
                            owner_state=owner_state,
                            account_row=account_row,
                            population_means=population_means,
                            population_stds=population_stds,
                            target_count=target_count,
                        ),
                    )
                )

        candidate_scores.sort(key=lambda item: item[1])
        chosen_owner = candidate_scores[0][0]
        working.at[account_index, "current_owner_name"] = chosen_owner
        working.at[account_index, "owner_name"] = chosen_owner
        # Update the running owner summary so future assignments use the latest territory shape.
        owner_state_by_name[chosen_owner]["count"] += 1
        owner_state_by_name[chosen_owner]["feature_sums"] += np.array(
            [account_row["account_mrr"], account_row["products_used"], account_row["icp_tier"]],
            dtype=float,
        )
        owner_state_by_name[chosen_owner]["quarter_counts"][account_row["renewal_quarter"]] += 1

    return working


def build_recommendations(before: pd.DataFrame, after: pd.DataFrame, owners: pd.DataFrame) -> pd.DataFrame:
    owner_lookup = (
        owners[["owner_id", "owner_name"]]
        .rename(columns={"owner_id": "recommended_owner_id", "owner_name": "recommended_owner_name"})
    )
    recommended = after.merge(owner_lookup, left_on="current_owner_name", right_on="recommended_owner_name", how="left")

    comparison = before[
        ["account_id", "account_name", "account_segment", "current_owner_name", "owner_id", "must_keep_with_owner"]
    ].merge(
        recommended[["account_id", "current_owner_name", "recommended_owner_id"]],
        on="account_id",
        suffixes=("_before", "_after"),
    )
    comparison = comparison.rename(columns={"current_owner_name_after": "recommended_owner_name"})
    comparison["reassignment_required"] = comparison["current_owner_name_before"] != comparison["recommended_owner_name"]
    return comparison.sort_values(["reassignment_required", "account_id"], ascending=[False, True]).reset_index(drop=True)


def build_salesforce_payloads(recommendations: pd.DataFrame) -> pd.DataFrame:
    payloads = recommendations[recommendations["reassignment_required"]].copy()
    payloads["object_name"] = SALESFORCE_ACCOUNT_OBJECT
    payloads["field_name"] = SALESFORCE_OWNER_FIELD_NAME
    payloads["new_value"] = payloads["recommended_owner_id"]
    return payloads[["account_id", "object_name", "field_name", "new_value"]]


def main() -> None:
    random.seed(DEFAULT_RANDOM_SEED)
    np.random.seed(DEFAULT_RANDOM_SEED)

    datasets = load_sample_data(DATA_DIR)
    owners = datasets["owners"]
    accounts = prepare_accounts(datasets["accounts"], owners)
    owner_names = owners[owners["owner_role"] == AM_ROLE]["owner_name"].tolist()

    before_stats = calculate_book_statistics(accounts)
    after_accounts = assign_accounts(accounts=accounts, owner_names=owner_names)
    after_stats = calculate_book_statistics(after_accounts)
    recommendations = build_recommendations(accounts, after_accounts, owners)
    payloads = build_salesforce_payloads(recommendations)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    before_stats.to_csv(OUTPUT_DIR / "territory_summary_before.csv", index=False)
    after_stats.to_csv(OUTPUT_DIR / "territory_summary_after.csv", index=False)
    recommendations.to_csv(OUTPUT_DIR / "territory_reassignment_recommendations.csv", index=False)
    payloads.to_csv(OUTPUT_DIR / "salesforce_update_payloads.csv", index=False)

    print("Before rebalance:")
    print(before_stats.to_string(index=False))
    print("\nAfter rebalance:")
    print(after_stats.to_string(index=False))
    print("\nRecommended reassignments:")
    print(
        recommendations[recommendations["reassignment_required"]]
        .head(TOP_RECOMMENDATIONS_TO_PRINT)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
