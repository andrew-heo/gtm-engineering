#!/usr/bin/env python3
"""AM renewal form automation demo with a Parabola-style workflow."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gtm_engineering.config import DATA_DIR, RENEWAL_AUTOMATION_DIR
from gtm_engineering.integrations import ParabolaClient, SalesforceClient, SlackClient
from gtm_engineering.synthetic_data import load_sample_data


OUTPUT_DIR = RENEWAL_AUTOMATION_DIR / "output"
FLOW_NAME = "am-renewal-form-automation"
RENEWALS_CHANNEL = "#renewals-desk"
RENEWAL_TASK_SUBJECT = "Review renewal form submission"
DEFAULT_STAGE_NAME = "Proposal"
RENEWAL_FORM_SOURCE = "am_renewal_form"


def build_form_submissions(datasets: dict[str, pd.DataFrame]) -> list[dict[str, str]]:
    accounts = (
        datasets["accounts"][
            (datasets["accounts"]["account_mrr"] > 0)
            & (datasets["accounts"]["owner_role"] == "AM")
            & (datasets["accounts"]["account_segment"].isin(["SMB", "Mid-Market"]))
        ]
        .sort_values(["account_mrr", "account_name"], ascending=[False, True])
        .reset_index(drop=True)
    )

    top_account = accounts.iloc[0]
    second_account = accounts.iloc[1]
    third_account = accounts.iloc[2]
    today = datetime.now(timezone.utc).date()

    return [
        {
            "submission_id": "renewal_form_001",
            "account_id": top_account["account_id"],
            "submitted_by_owner_name": top_account["owner_name"],
            "renewal_forecast": "commit",
            "renewal_risk_level": "low",
            "renewal_strategy": "multi-year upsell",
            "contract_end_date": (today + timedelta(days=75)).isoformat(),
            "renewal_nnarr": "145000",
            "pricing_exception_requested": "false",
        },
        {
            "submission_id": "renewal_form_002",
            "account_id": second_account["account_id"],
            "submitted_by_owner_name": second_account["owner_name"],
            "renewal_forecast": "best case",
            "renewal_risk_level": "high",
            "renewal_strategy": "discount request",
            "contract_end_date": (today + timedelta(days=48)).isoformat(),
            "renewal_nnarr": "98000",
            "pricing_exception_requested": "true",
        },
        {
            "submission_id": "renewal_form_003",
            "account_id": third_account["account_id"],
            "submitted_by_owner_name": "AM_99",
            "renewal_forecast": "pipeline",
            "renewal_risk_level": "medium",
            "renewal_strategy": "needs validation",
            "contract_end_date": (today + timedelta(days=55)).isoformat(),
            "renewal_nnarr": "88000",
            "pricing_exception_requested": "false",
        },
        {
            "submission_id": "renewal_form_004",
            "account_id": third_account["account_id"],
            "submitted_by_owner_name": third_account["owner_name"],
            "renewal_forecast": "",
            "renewal_risk_level": "medium",
            "renewal_strategy": "missing forecast",
            "contract_end_date": (today + timedelta(days=62)).isoformat(),
            "renewal_nnarr": "76000",
            "pricing_exception_requested": "false",
        },
    ]


def normalize_submission(raw_submission: dict[str, str], parabola_client: ParabolaClient) -> dict[str, str]:
    normalized = {
        "submission_id": raw_submission["submission_id"].strip(),
        "account_id": raw_submission["account_id"].strip(),
        "submitted_by_owner_name": raw_submission["submitted_by_owner_name"].strip(),
        "renewal_forecast": raw_submission["renewal_forecast"].strip().lower(),
        "renewal_risk_level": raw_submission["renewal_risk_level"].strip().lower(),
        "renewal_strategy": raw_submission["renewal_strategy"].strip(),
        "contract_end_date": raw_submission["contract_end_date"].strip(),
        "renewal_nnarr": int(raw_submission["renewal_nnarr"]),
        "pricing_exception_requested": raw_submission["pricing_exception_requested"].strip().lower() == "true",
    }
    flow_result = parabola_client.run_flow(FLOW_NAME, {"submission_id": normalized["submission_id"]})
    normalized["flow_status"] = flow_result.status
    normalized["flow_name"] = flow_result.payload["flow_name"]
    return normalized


def validate_submission(submission: dict[str, str], account: pd.Series | None) -> list[str]:
    errors = []
    if account is None:
        errors.append("Account not found.")
    else:
        if account["owner_name"] != submission["submitted_by_owner_name"]:
            errors.append("Submitting owner does not match the current AM owner.")
        if account["owner_role"] != "AM":
            errors.append("Renewal form must map to an AM-owned account.")
    if not submission["renewal_forecast"]:
        errors.append("Renewal forecast is required.")
    if submission["renewal_nnarr"] <= 0:
        errors.append("Renewal NNARR must be greater than zero.")
    return errors


def process_submission(
    submission: dict[str, str],
    account_lookup: dict[str, dict[str, str]],
    salesforce_client: SalesforceClient,
    slack_client: SlackClient,
) -> tuple[dict[str, str], dict[str, str] | None, dict[str, str] | None, dict[str, str]]:
    account_dict = account_lookup.get(submission["account_id"])
    account = pd.Series(account_dict) if account_dict else None
    errors = validate_submission(submission, account)

    if errors:
        slack_result = slack_client.post_message(
            RENEWALS_CHANNEL,
            f"Renewal form {submission['submission_id']} blocked: {' '.join(errors)}",
        )
        result = {
            "submission_id": submission["submission_id"],
            "account_id": submission["account_id"],
            "account_name": account["account_name"] if account is not None else "",
            "owner_name": account["owner_name"] if account is not None else submission["submitted_by_owner_name"],
            "status": "blocked",
            "path": "validation_failed",
            "renewal_forecast": submission["renewal_forecast"],
            "renewal_risk_level": submission["renewal_risk_level"],
            "renewal_nnarr": submission["renewal_nnarr"],
            "message": " ".join(errors),
        }
        return result, None, None, slack_result.payload

    opportunity_result = salesforce_client.create_opportunity(
        {
            "account_id": submission["account_id"],
            "opportunity_name": f"{account['account_name']} - Renewal",
            "owner_id": account["owner_id"],
            "stage_name": DEFAULT_STAGE_NAME,
            "nnarr": submission["renewal_nnarr"],
            "is_open": True,
            "created_date": datetime.now(timezone.utc).date().isoformat(),
            "close_date": submission["contract_end_date"],
            "source": RENEWAL_FORM_SOURCE,
        }
    )
    salesforce_client.update_account(
        submission["account_id"],
        {"last_interesting_moment": f"AM renewal form submitted ({datetime.now(timezone.utc).date()})"},
    )

    task_payload = None
    if submission["renewal_risk_level"] == "high" or submission["pricing_exception_requested"]:
        task_payload = salesforce_client.create_task(
            {
                "subject": RENEWAL_TASK_SUBJECT,
                "related_account_id": submission["account_id"],
                "owner_name": account["owner_name"],
                "description": (
                    f"Review renewal form {submission['submission_id']} for {account['account_name']}. "
                    f"Forecast={submission['renewal_forecast']}, risk={submission['renewal_risk_level']}."
                ),
            }
        ).payload

    slack_result = slack_client.post_message(
        RENEWALS_CHANNEL,
        (
            f"Renewal form processed for {account['account_name']} | owner={account['owner_name']} | "
            f"forecast={submission['renewal_forecast']} | risk={submission['renewal_risk_level']} | "
            f"nnarr={submission['renewal_nnarr']}"
        ),
    )
    result = {
        "submission_id": submission["submission_id"],
        "account_id": submission["account_id"],
        "account_name": account["account_name"],
        "owner_name": account["owner_name"],
        "status": "processed",
        "path": "renewal_opportunity_created",
        "renewal_forecast": submission["renewal_forecast"],
        "renewal_risk_level": submission["renewal_risk_level"],
        "renewal_nnarr": submission["renewal_nnarr"],
        "message": "Renewal opportunity created and downstream actions prepared.",
    }
    return result, opportunity_result.payload, task_payload, slack_result.payload


def main() -> None:
    datasets = load_sample_data(DATA_DIR)
    salesforce_client = SalesforceClient(datasets=datasets, dry_run=True)
    slack_client = SlackClient(dry_run=True)
    parabola_client = ParabolaClient(dry_run=True)

    account_lookup = datasets["accounts"].set_index("account_id").to_dict("index")
    raw_submissions = build_form_submissions(datasets)
    normalized_submissions = [normalize_submission(submission, parabola_client) for submission in raw_submissions]

    processing_results = []
    opportunity_payloads = []
    task_payloads = []
    slack_payloads = []

    for submission in normalized_submissions:
        result, opportunity_payload, task_payload, slack_payload = process_submission(
            submission=submission,
            account_lookup=account_lookup,
            salesforce_client=salesforce_client,
            slack_client=slack_client,
        )
        processing_results.append(result)
        if opportunity_payload is not None:
            opportunity_payloads.append(opportunity_payload)
        if task_payload is not None:
            task_payloads.append(task_payload)
        slack_payloads.append(slack_payload)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(normalized_submissions).to_csv(OUTPUT_DIR / "parabola_flow_runs.csv", index=False)
    pd.DataFrame(processing_results).to_csv(OUTPUT_DIR / "renewal_form_processing_results.csv", index=False)
    pd.DataFrame(opportunity_payloads).to_csv(OUTPUT_DIR / "salesforce_renewal_opportunities.csv", index=False)
    pd.DataFrame(task_payloads).to_csv(OUTPUT_DIR / "salesforce_tasks.csv", index=False)
    pd.DataFrame(slack_payloads).to_csv(OUTPUT_DIR / "slack_message_payloads.csv", index=False)

    print(pd.DataFrame(processing_results).to_string(index=False))


if __name__ == "__main__":
    main()
