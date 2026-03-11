#!/usr/bin/env python3
"""Generate the shared synthetic GTM dataset and a short validation summary."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gtm_engineering.config import DATA_DIR, DATA_OUTPUT_DIR, DEFAULT_RANDOM_SEED
from gtm_engineering.synthetic_data import (
    FREE_PLAN,
    LEAD_MODELED_TIMEFRAME_DAYS,
    OPPORTUNITY_MODELED_TIMEFRAME_DAYS,
    USAGE_EVENT_MODELED_TIMEFRAME_DAYS,
    save_synthetic_gtm_data,
)


SUMMARY_ROW_ORDER = [
    "owners",
    "accounts",
    "leads",
    "opportunities",
        "product_usage_events",
        "paid_accounts",
        "free_plan_accounts",
        "open_opportunities",
        "matched_leads",
        "lead_modeled_timeframe_days",
        "opportunity_modeled_timeframe_days",
        "usage_event_modeled_timeframe_days",
        "lead_request_timestamp_min",
        "lead_request_timestamp_max",
        "opportunity_created_date_min",
        "opportunity_created_date_max",
        "usage_event_timestamp_min",
        "usage_event_timestamp_max",
]


def build_summary(dataframes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    accounts = dataframes["accounts"]
    leads = dataframes["leads"]
    opportunities = dataframes["opportunities"]
    usage_events = dataframes["product_usage_events"]
    lead_timestamps = pd.to_datetime(leads["request_timestamp"], utc=True)
    opportunity_created_dates = pd.to_datetime(opportunities["created_date"], utc=True)
    usage_event_timestamps = pd.to_datetime(usage_events["event_timestamp"], utc=True)

    summary_values = {
        "owners": len(dataframes["owners"]),
        "accounts": len(accounts),
        "leads": len(leads),
        "opportunities": len(opportunities),
        "product_usage_events": len(usage_events),
        "paid_accounts": int((accounts["account_mrr"] > 0).sum()),
        "free_plan_accounts": int((accounts["plan_type"] == FREE_PLAN).sum()),
        "open_opportunities": int(opportunities["is_open"].sum()),
        "matched_leads": int(leads["matched_account_id"].notna().sum()),
        "lead_modeled_timeframe_days": LEAD_MODELED_TIMEFRAME_DAYS,
        "opportunity_modeled_timeframe_days": OPPORTUNITY_MODELED_TIMEFRAME_DAYS,
        "usage_event_modeled_timeframe_days": USAGE_EVENT_MODELED_TIMEFRAME_DAYS,
        "lead_request_timestamp_min": lead_timestamps.min().isoformat(),
        "lead_request_timestamp_max": lead_timestamps.max().isoformat(),
        "opportunity_created_date_min": opportunity_created_dates.min().date().isoformat(),
        "opportunity_created_date_max": opportunity_created_dates.max().date().isoformat(),
        "usage_event_timestamp_min": usage_event_timestamps.min().isoformat(),
        "usage_event_timestamp_max": usage_event_timestamps.max().isoformat(),
    }
    summary = pd.DataFrame(
        [{"dataset": dataset_name, "value": summary_values[dataset_name]} for dataset_name in SUMMARY_ROW_ORDER]
    )
    return summary


def main() -> None:
    dataframes = save_synthetic_gtm_data(output_dir=DATA_DIR, seed=DEFAULT_RANDOM_SEED)
    summary = build_summary(dataframes)
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(DATA_OUTPUT_DIR / "data_summary.csv", index=False)

    print("Synthetic GTM data written to:")
    print(DATA_DIR)
    print("\nData summary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
