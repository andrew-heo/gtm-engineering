#!/usr/bin/env python3
"""Weekly free-tier usage alert demo driven by shared synthetic data."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gtm_engineering.config import DATA_DIR, FREETIER_ALERT_DIR
from gtm_engineering.integrations import SalesforceClient, SlackClient, UsageEventsClient
from gtm_engineering.synthetic_data import FREE_PLAN, load_sample_data


OUTPUT_DIR = FREETIER_ALERT_DIR / "output"
LOOKBACK_DAYS = 7
TOP_ACCOUNTS_TO_ALERT = 10
TOP_USER_RANK = 1
SLACK_DESTINATION = "#ae-weekly-alerts"
TASK_SUBJECT = "Review free-tier expansion signal"


def build_ranked_alert_table(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    accounts = datasets["accounts"].copy()
    owners = datasets["owners"].copy()
    usage_client = UsageEventsClient(datasets=datasets)

    recent_events = usage_client.fetch_recent_events(lookback_days=LOOKBACK_DAYS)
    free_accounts = accounts[accounts["plan_type"] == FREE_PLAN].copy()
    free_events = recent_events.merge(free_accounts, on="account_id", how="inner")

    account_usage = (
        free_events.groupby(["account_id", "account_name", "owner_id"], dropna=False)
        .agg(
            total_events_last_7_days=("event_id", "count"),
            distinct_users_last_7_days=("user_email", "nunique"),
        )
        .reset_index()
    )

    top_people = (
        free_events.groupby(["account_id", "user_email"], dropna=False)
        .agg(user_events_last_7_days=("event_id", "count"))
        .reset_index()
        .sort_values(["account_id", "user_events_last_7_days", "user_email"], ascending=[True, False, True])
    )
    top_people["rank_within_account"] = top_people.groupby("account_id").cumcount() + TOP_USER_RANK
    top_people = top_people[top_people["rank_within_account"] == TOP_USER_RANK].copy()

    ranked = account_usage.merge(top_people[["account_id", "user_email", "user_events_last_7_days"]], on="account_id")
    ranked = ranked.merge(
        owners[["owner_id", "owner_name", "owner_role", "slack_destination"]],
        left_on="owner_id",
        right_on="owner_id",
        how="left",
    )
    ranked["top_user_share_of_activity"] = (
        ranked["user_events_last_7_days"] / ranked["total_events_last_7_days"]
    ).round(2)

    ranked = ranked.sort_values(
        ["total_events_last_7_days", "distinct_users_last_7_days", "account_name"],
        ascending=[False, False, True],
    ).head(TOP_ACCOUNTS_TO_ALERT)

    return ranked[
        [
            "account_id",
            "account_name",
            "owner_role",
            "owner_name",
            "slack_destination",
            "total_events_last_7_days",
            "distinct_users_last_7_days",
            "user_email",
            "top_user_share_of_activity",
        ]
    ].rename(columns={"owner_name": "account_owner_name", "user_email": "top_user_email"})


def build_alert_message(ranked_alerts: pd.DataFrame) -> str:
    period_end = datetime.now(timezone.utc).date()
    period_start = period_end - timedelta(days=LOOKBACK_DAYS - 1)
    lines = [f"Top free-tier usage accounts: {period_start} to {period_end}"]

    for index, row in enumerate(ranked_alerts.itertuples(index=False), start=1):
        lines.append(
            (
                f"{index}. {row.account_name} | owner={row.account_owner_name} | "
                f"owner_role={row.owner_role} | "
                f"events={row.total_events_last_7_days} | users={row.distinct_users_last_7_days} | "
                f"top user={row.top_user_email} ({row.top_user_share_of_activity:.0%})"
            )
        )

    return "\n".join(lines)


def build_salesforce_tasks(ranked_alerts: pd.DataFrame, salesforce_client: SalesforceClient) -> list[dict[str, str]]:
    tasks = []
    for row in ranked_alerts.itertuples(index=False):
        result = salesforce_client.create_task(
            {
                "subject": TASK_SUBJECT,
                "related_account_id": row.account_id,
                "owner_name": row.account_owner_name,
                "description": (
                    f"{row.account_name} generated {row.total_events_last_7_days} events in the past 7 days. "
                    f"Top user: {row.top_user_email}."
                ),
            }
        )
        tasks.append(result.payload)
    return tasks


def main() -> None:
    datasets = load_sample_data(DATA_DIR)
    slack_client = SlackClient(dry_run=True)
    salesforce_client = SalesforceClient(datasets=datasets, dry_run=True)

    ranked_alerts = build_ranked_alert_table(datasets)
    message = build_alert_message(ranked_alerts)
    slack_payload = slack_client.post_message(SLACK_DESTINATION, message)
    salesforce_tasks = build_salesforce_tasks(ranked_alerts, salesforce_client)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ranked_alerts.to_csv(OUTPUT_DIR / "free_tier_usage_alerts.csv", index=False)
    pd.DataFrame(salesforce_tasks).to_csv(OUTPUT_DIR / "salesforce_tasks.csv", index=False)
    pd.DataFrame([slack_payload.payload]).to_csv(OUTPUT_DIR / "slack_message_payload.csv", index=False)

    print(message)


if __name__ == "__main__":
    main()
