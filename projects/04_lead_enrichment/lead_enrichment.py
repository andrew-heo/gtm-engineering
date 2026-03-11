#!/usr/bin/env python3
"""Lead enrichment automation demo with dry-run Salesforce and Clay wrappers."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gtm_engineering.config import DATA_DIR, LEAD_ENRICHMENT_DIR
from gtm_engineering.integrations import ClayClient, SalesforceClient, SlackClient
from gtm_engineering.synthetic_data import PERSONAL_EMAIL_DOMAINS, SEGMENT_SMB, load_sample_data


OUTPUT_DIR = LEAD_ENRICHMENT_DIR / "output"
DEFAULT_SCENARIO = "all"
ALL_SCENARIOS = "all"
SCENARIO_NAMES = ["existing_lead", "matched_account", "net_new", "personal_email"]
COUNTRY_US = "US"
OPEN_STATUS = "Open"
DEMO_REQUEST_LEAD_SOURCE = "Demo Request"
ONLINE_DEMO_REQUEST_SOURCE = "online_demo_request"
UNOWNED_DEMO_REQUESTS_CHANNEL = "#unowned-demo-requests"
OWNED_DEMO_REQUESTS_CHANNEL = "#owned-demo-requests"
PROSPECT_PLAN_TYPE = "Prospect"
DEFAULT_NET_NEW_ICP_TIER = 3
DEFAULT_NET_NEW_RENEWAL_QUARTER = "Q4"
INTERESTING_MOMENT_LABEL = "Online demo request"
EMPTY_OWNER_ID = ""
EMPTY_ACCOUNT_ID = ""
EMAIL_DOMAIN_SEPARATOR = "@"

SCENARIOS = {
    "matched_account": {
        "first_name": "Jordan",
        "last_name": "Operator",
        "company_email": "newperson@company050.com",
        "company_name": "Company050 Labs",
        "job_title": "Head of Operations",
        "country": COUNTRY_US,
        "request_source": ONLINE_DEMO_REQUEST_SOURCE,
    },
    "net_new": {
        "first_name": "Morgan",
        "last_name": "Prospect",
        "company_email": "morgan@newlogoai.com",
        "company_name": "NewLogo AI",
        "job_title": "Chief of Staff",
        "country": COUNTRY_US,
        "request_source": ONLINE_DEMO_REQUEST_SOURCE,
    },
    "personal_email": {
        "first_name": "Chris",
        "last_name": "Consumer",
        "company_email": "chris@gmail.com",
        "company_name": "Unknown",
        "job_title": "Consultant",
        "country": COUNTRY_US,
        "request_source": ONLINE_DEMO_REQUEST_SOURCE,
    },
}


def is_company_email(email: str) -> bool:
    return email.split(EMAIL_DOMAIN_SEPARATOR)[-1].lower() not in PERSONAL_EMAIL_DOMAINS


def build_demo_request(scenario_name: str, datasets: dict[str, pd.DataFrame]) -> dict[str, str]:
    if scenario_name == "existing_lead":
        existing_lead = datasets["leads"].dropna(subset=["email", "matched_account_id"]).iloc[0]
        request = {
            "first_name": existing_lead["first_name"],
            "last_name": existing_lead["last_name"],
            "company_email": existing_lead["email"],
            "company_name": existing_lead["company_name"],
            "job_title": existing_lead["job_title"],
            "country": existing_lead["country"],
            "request_source": ONLINE_DEMO_REQUEST_SOURCE,
        }
    else:
        request = dict(SCENARIOS[scenario_name])
    request["request_timestamp"] = datetime.now(timezone.utc).isoformat()
    return request


def process_demo_request(
    demo_request: dict[str, str],
    salesforce_client: SalesforceClient,
    clay_client: ClayClient,
    slack_client: SlackClient,
) -> dict[str, str]:
    email = demo_request["company_email"]
    domain = email.split(EMAIL_DOMAIN_SEPARATOR)[-1].lower()

    if not is_company_email(email):
        return {
            "path": "rejected_personal_email",
            "lead_id": EMPTY_ACCOUNT_ID,
            "account_id": EMPTY_ACCOUNT_ID,
            "account_segment": "",
            "matched_owner_name": "",
            "matched_owner_role": "",
            "slack_destination": UNOWNED_DEMO_REQUESTS_CHANNEL,
            "message": "Rejected personal email; no enrichment performed.",
        }

    enrichment = clay_client.enrich_person_company(email=email, company_name=demo_request["company_name"]).payload
    existing_lead = salesforce_client.find_lead_by_email(email)

    if existing_lead:
        account = salesforce_client.find_account_by_domain(domain)
        slack_destination = OWNED_DEMO_REQUESTS_CHANNEL if account else UNOWNED_DEMO_REQUESTS_CHANNEL
        slack_client.post_message(slack_destination, f"Existing lead re-engaged: {email}")
        return {
            "path": "existing_lead",
            "lead_id": existing_lead["lead_id"],
            "account_id": account["account_id"] if account else (existing_lead.get("matched_account_id") or EMPTY_ACCOUNT_ID),
            "account_segment": account["account_segment"] if account else "",
            "matched_owner_name": account["owner_name"] if account else "",
            "matched_owner_role": account["owner_role"] if account else "",
            "slack_destination": slack_destination,
            "message": "Existing lead found; reused lead record and sent notification.",
        }

    matched_account = salesforce_client.find_account_by_domain(domain)

    if matched_account:
        # This is the core enrichment path: attach the new inbound lead to an account the AE already owns.
        lead_result = salesforce_client.create_lead(
            {
                "first_name": demo_request["first_name"],
                "last_name": demo_request["last_name"],
                "email": email,
                "company_name": enrichment["company_name"],
                "job_title": enrichment["job_title"],
                "country": demo_request["country"],
                "lead_source": DEMO_REQUEST_LEAD_SOURCE,
                "status": OPEN_STATUS,
                "matched_account_id": matched_account["account_id"],
                "owner_id": matched_account["owner_id"],
                "request_timestamp": demo_request["request_timestamp"],
            }
        )
        salesforce_client.update_account(
            matched_account["account_id"],
            {"last_interesting_moment": f"{INTERESTING_MOMENT_LABEL} ({datetime.now(timezone.utc).date()})"},
        )
        slack_client.post_message(OWNED_DEMO_REQUESTS_CHANNEL, f"Matched account demo request: {email}")
        return {
            "path": "matched_account_new_lead",
            "lead_id": lead_result.payload["lead_id"],
            "account_id": matched_account["account_id"],
            "account_segment": matched_account["account_segment"],
            "matched_owner_name": matched_account["owner_name"],
            "matched_owner_role": matched_account["owner_role"],
            "slack_destination": OWNED_DEMO_REQUESTS_CHANNEL,
            "message": "Matched existing account, created lead, updated interesting moment.",
        }

    account_result = salesforce_client.create_account(
        {
            "account_name": enrichment["company_name"],
            "domain": domain,
            "industry": enrichment["industry"],
            "employee_band": enrichment["company_size"],
            "plan_type": PROSPECT_PLAN_TYPE,
            "account_mrr": 0,
            "products_used": 0,
            "icp_tier": DEFAULT_NET_NEW_ICP_TIER,
            "renewal_quarter": DEFAULT_NET_NEW_RENEWAL_QUARTER,
            "account_segment": SEGMENT_SMB,
            "am_owner_id": EMPTY_OWNER_ID,
            "ae_owner_id": EMPTY_OWNER_ID,
            "owner_id": EMPTY_OWNER_ID,
            "owner_name": "",
            "owner_role": "",
            "must_keep_with_owner": False,
            "last_interesting_moment": f"{INTERESTING_MOMENT_LABEL} ({datetime.now(timezone.utc).date()})",
        }
    )
    lead_result = salesforce_client.create_lead(
        {
            "first_name": demo_request["first_name"],
            "last_name": demo_request["last_name"],
            "email": email,
            "company_name": enrichment["company_name"],
            "job_title": enrichment["job_title"],
            "country": demo_request["country"],
            "lead_source": DEMO_REQUEST_LEAD_SOURCE,
            "status": OPEN_STATUS,
            "matched_account_id": account_result.payload["account_id"],
            "owner_id": EMPTY_OWNER_ID,
            "request_timestamp": demo_request["request_timestamp"],
        }
    )
    slack_client.post_message(UNOWNED_DEMO_REQUESTS_CHANNEL, f"Net-new account demo request: {email}")
    return {
        "path": "net_new_account_and_lead",
        "lead_id": lead_result.payload["lead_id"],
        "account_id": account_result.payload["account_id"],
        "account_segment": account_result.payload["account_segment"],
        "matched_owner_name": account_result.payload["owner_name"],
        "matched_owner_role": account_result.payload["owner_role"],
        "slack_destination": UNOWNED_DEMO_REQUESTS_CHANNEL,
        "message": "Created new account and lead from enriched demo request.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=[*SCENARIO_NAMES, ALL_SCENARIOS],
        default=DEFAULT_SCENARIO,
    )
    args = parser.parse_args()

    scenarios = [args.scenario] if args.scenario != ALL_SCENARIOS else SCENARIO_NAMES
    datasets = load_sample_data(DATA_DIR)
    results = []

    for scenario_name in scenarios:
        salesforce_client = SalesforceClient(datasets=datasets, dry_run=True)
        clay_client = ClayClient(dry_run=True)
        slack_client = SlackClient(dry_run=True)
        result = process_demo_request(
            demo_request=build_demo_request(scenario_name, datasets=datasets),
            salesforce_client=salesforce_client,
            clay_client=clay_client,
            slack_client=slack_client,
        )
        result["scenario"] = scenario_name
        results.append(result)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / "lead_enrichment_scenarios.csv", index=False)
    print(results_df.to_string(index=False))


if __name__ == "__main__":
    main()
