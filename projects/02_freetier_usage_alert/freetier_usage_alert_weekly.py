import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from datadog import initialize, api
from simple_salesforce import Salesforce


pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)


SFDC_CONFIG = {
    "username": "andrew.heo@dtdg.com",
    "password": "password",
    "security_token": "security_token",
    "domain": "login",   # use "test" for sandbox
}

DATADOG_CONFIG = {
    "api_key": os.getenv("DATADOG_API_KEY"),
    "app_key": os.getenv("DATADOG_APP_KEY"),
    "site": "datadoghq.com",
}

SLACK_CONFIG = {
    "bot_token": "xoxb-fake-slack-bot-token",
}

SEND_SLACK_ALERTS = False

CSM_SLACK_DESTINATIONS = {
    "AE_1": "U11111111",
    "AE_2": "U22222222",
    "AE_3": "U33333333",
    "AE_4": "U44444444",
    "AE_5": "U55555555",
    "AE_6": "U66666666",
    "AE_7": "U77777777",
    "AE_8": "U88888888",
    "AE_9": "U99999999",
    "AE_10": "U10101010",
}


# ------------------------------------------------------------
# Reporting window: every Monday, send the prior 7 days
# Example:
# run on Monday 2026-03-09
# report window = 2026-03-02 00:00:00 through 2026-03-08 23:59:59
# ------------------------------------------------------------

def calculate_last_7_day_reporting_window_for_monday_run():
    run_time = datetime.utcnow()

    report_end_date = run_time.date() - timedelta(days=1)
    report_start_date = report_end_date - timedelta(days=6)

    report_start_time = datetime.combine(report_start_date, datetime.min.time())
    report_end_time = datetime.combine(report_end_date, datetime.max.time())

    return report_start_time, report_end_time


def today_is_monday():
    return datetime.utcnow().weekday() == 0


# -------------------------------------------------------------------
# Datadog RUM connection
# -------------------------------------------------------------------

initialize(**DATADOG_CONFIG)


def fetch_datadog_rum_navigation_events(
    start_time,
    end_time,
    rum_application_id="abc123sampleapp",
):
    """
    Pull navigation events from Datadog RUM.
    """

    response = api.RUMEvents.search(
        body={
            "filter": {
                "from": start_time.isoformat(),
                "to": end_time.isoformat(),
                "query": "@type:view",
            },
            "page": {"limit": 1000},
        }
    )

    events = []

    for event in response.get("data", []):
        attributes = event.get("attributes", {})

        events.append(
            {
                "event_timestamp": attributes.get("timestamp"),
                "session_id": attributes.get("session", {}).get("id"),
                "user_email": attributes.get("usr", {}).get("email"),
                "account_id": attributes.get("usr", {}).get("account_id"),
                "page_url": attributes.get("view", {}).get("url"),
                "event_type": "page_view",
                "source": "datadog_rum",
            }
        )

    return pd.DataFrame(events)


# -------------------------------------------------------------------
# Salesforce connection
# -------------------------------------------------------------------

def connect_to_salesforce():
    """
    Create a Salesforce client.
    """
    sf = Salesforce(
        username=SFDC_CONFIG["username"],
        password=SFDC_CONFIG["password"],
        security_token=SFDC_CONFIG["security_token"],
        domain=SFDC_CONFIG["domain"],
    )
    return sf


def fetch_salesforce_accounts_for_account_ids(sf, account_ids):
    """
    Pull Salesforce Account records for a provided list of Salesforce Account IDs.
    Returns a pandas DataFrame.
    """

    if len(account_ids) == 0:
        return pd.DataFrame()

    unique_account_ids = sorted(set(account_ids))
    quoted_ids = ",".join([f"'{account_id}'" for account_id in unique_account_ids])

    soql = f"""
        SELECT
            Id,
            Name,
            OwnerId,
            Type,
            Industry,
            Customer_Tier__c,
            Success_Manager__c,
            Plan_Type__c
        FROM Account
        WHERE Id IN ({quoted_ids})
    """

    result = sf.query_all(soql)

    cleaned_records = []
    for record in result.get("records", []):
        cleaned_records.append(
            {
                "account_id": record.get("Id"),
                "sfdc_account_name": record.get("Name"),
                "sfdc_owner_id": record.get("OwnerId"),
                "sfdc_account_type": record.get("Type"),
                "sfdc_industry": record.get("Industry"),
                "sfdc_customer_tier": record.get("Customer_Tier__c"),
                "sfdc_success_manager": record.get("Success_Manager__c"),
                "sfdc_plan_type": record.get("Plan_Type__c"),
            }
        )

    return pd.DataFrame(cleaned_records)


# -------------------------------------------------------------------
# Slack connection
# -------------------------------------------------------------------

def send_slack_message(slack_destination, message_text):
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_CONFIG['bot_token']}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "channel": slack_destination,
            "text": message_text,
        },
        timeout=30,
    )

    return response.json()


# -------------------------------------------------------------------
# Main process
# -------------------------------------------------------------------

report_start_time, report_end_time = calculate_last_7_day_reporting_window_for_monday_run()

rum_events_df = fetch_datadog_rum_navigation_events(
    start_time=report_start_time,
    end_time=report_end_time,
)

account_ids_from_events = rum_events_df["account_id"].dropna().unique().tolist()

sf = connect_to_salesforce()

salesforce_accounts_df = fetch_salesforce_accounts_for_account_ids(
    sf=sf,
    account_ids=account_ids_from_events,
)

rum_events_with_sfdc_df = rum_events_df.merge(
    salesforce_accounts_df,
    on="account_id",
    how="left",
)

free_plan_rum_events_with_sfdc_df = rum_events_with_sfdc_df[
    rum_events_with_sfdc_df["sfdc_plan_type"] == "Free"
].copy()

# ------------------------------------------------------------
# Aggregate site visits at the account level
# ------------------------------------------------------------

free_plan_account_site_visits_df = (
    free_plan_rum_events_with_sfdc_df
    .groupby(
        [
            "account_id",
            "sfdc_account_name",
            "sfdc_owner_id",
            "sfdc_success_manager",
        ],
        dropna=False,
    )
    .agg(
        total_site_visits_last_7_days=("event_timestamp", "count"),
        distinct_users_last_7_days=("user_email", "nunique"),
    )
    .reset_index()
)

# ------------------------------------------------------------
# Aggregate site visits at the person level within each account
# ------------------------------------------------------------

free_plan_account_user_site_visits_df = (
    free_plan_rum_events_with_sfdc_df
    .groupby(
        [
            "account_id",
            "sfdc_account_name",
            "sfdc_owner_id",
            "sfdc_success_manager",
            "user_email",
        ],
        dropna=False,
    )
    .agg(
        user_site_visits_last_7_days=("event_timestamp", "count"),
    )
    .reset_index()
)

# ------------------------------------------------------------
# Join in account totals so we can calculate percent of visits
# ------------------------------------------------------------

free_plan_account_user_site_visits_df = free_plan_account_user_site_visits_df.merge(
    free_plan_account_site_visits_df[
        [
            "account_id",
            "total_site_visits_last_7_days",
        ]
    ],
    on="account_id",
    how="left",
)

free_plan_account_user_site_visits_df["percent_of_total_account_site_visits"] = (
    free_plan_account_user_site_visits_df["user_site_visits_last_7_days"]
    / free_plan_account_user_site_visits_df["total_site_visits_last_7_days"]
)

# ------------------------------------------------------------
# Rank users within each account and keep the top person
# ------------------------------------------------------------

free_plan_account_user_site_visits_df = free_plan_account_user_site_visits_df.sort_values(
    [
        "account_id",
        "user_site_visits_last_7_days",
        "user_email",
    ],
    ascending=[True, False, True],
).copy()

free_plan_account_user_site_visits_df["user_rank_within_account"] = (
    free_plan_account_user_site_visits_df.groupby("account_id").cumcount() + 1
)

top_person_per_free_plan_account_df = free_plan_account_user_site_visits_df[
    free_plan_account_user_site_visits_df["user_rank_within_account"] == 1
].copy()

top_person_per_free_plan_account_df = top_person_per_free_plan_account_df[
    [
        "account_id",
        "user_email",
        "user_site_visits_last_7_days",
        "percent_of_total_account_site_visits",
    ]
].rename(
    columns={
        "user_email": "top_person_email",
        "user_site_visits_last_7_days": "top_person_site_visits_last_7_days",
        "percent_of_total_account_site_visits": "top_person_percent_of_total_account_site_visits",
    }
)

# ------------------------------------------------------------
# Build ranked top-10 customer table
# ------------------------------------------------------------

top_10_free_plan_customers_by_site_visits_df = free_plan_account_site_visits_df.merge(
    top_person_per_free_plan_account_df,
    on="account_id",
    how="left",
)

top_10_free_plan_customers_by_site_visits_df = top_10_free_plan_customers_by_site_visits_df.sort_values(
    [
        "total_site_visits_last_7_days",
        "distinct_users_last_7_days",
        "sfdc_account_name",
    ],
    ascending=[False, False, True],
).head(10).copy()

top_10_free_plan_customers_by_site_visits_df["top_person_percent_of_total_account_site_visits_display"] = (
    top_10_free_plan_customers_by_site_visits_df["top_person_percent_of_total_account_site_visits"]
    .fillna(0)
    .map(lambda x: f"{x:.0%}")
)

print("\nTOP 10 FREE-PLAN CUSTOMERS BY SITE VISITS")
print(
    top_10_free_plan_customers_by_site_visits_df[
        [
            "account_id",
            "sfdc_account_name",
            "sfdc_owner_id",
            "sfdc_success_manager",
            "total_site_visits_last_7_days",
            "distinct_users_last_7_days",
            "top_person_email",
            "top_person_percent_of_total_account_site_visits_display",
        ]
    ]
)

# ------------------------------------------------------------
# Build Slack message
# ------------------------------------------------------------

slack_message_lines = []
slack_message_lines.append(
    f"Top 10 customers (Site Visits) — {report_start_time.date()} to {report_end_time.date()}"
)

for i, (_, row) in enumerate(top_10_free_plan_customers_by_site_visits_df.iterrows(), start=1):
    account_name = row["sfdc_account_name"]
    total_site_visits_last_7_days = int(row["total_site_visits_last_7_days"])
    top_person_email = row["top_person_email"]
    top_person_percent_of_total_account_site_visits_display = row["top_person_percent_of_total_account_site_visits_display"]

    slack_message_lines.append(
        f"{i}. {account_name} ({total_site_visits_last_7_days} visits, {top_person_email} ({top_person_percent_of_total_account_site_visits_display} of total visits))"
    )

slack_message = "\n".join(slack_message_lines)

print("\nSLACK MESSAGE")
print(slack_message)

# ------------------------------------------------------------
# Optional: send the same message separately to 10 AEs / CSMs
# ------------------------------------------------------------

if SEND_SLACK_ALERTS and today_is_monday():
    for csm_name, slack_destination in CSM_SLACK_DESTINATIONS.items():
        print(f"Sending Slack alert to {csm_name} -> {slack_destination}")
        slack_response = send_slack_message(
            slack_destination=slack_destination,
            message_text=slack_message,
        )
        print(slack_response)
else:
    print("\nSEND_SLACK_ALERTS is False or today is not Monday — Slack alerts not sent.")
