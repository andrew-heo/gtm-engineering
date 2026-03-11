#!/usr/bin/env python3
"""Generate weekly state-of-the-business markdown reports."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gtm_engineering.config import (
    DATA_DIR,
    FREETIER_ALERT_DIR,
    LEAD_ENRICHMENT_DIR,
    MARKETING_ATTRIBUTION_DIR,
    REPORTING_ROOT,
    RENEWAL_AUTOMATION_DIR,
    TERRITORY_BALANCER_DIR,
)
from gtm_engineering.synthetic_data import load_sample_data


REPORTS = {
    "am": {
        "title": "AM Weekly State of the Business",
        "filter": lambda accounts: (accounts["owner_role"] == "AM") & (accounts["account_mrr"] > 0),
    },
    "smb": {
        "title": "SMB Weekly State of the Business",
        "filter": lambda accounts: accounts["account_segment"] == "SMB",
    },
    "mm": {
        "title": "Mid-Market Weekly State of the Business",
        "filter": lambda accounts: accounts["account_segment"] == "Mid-Market",
    },
    "ent": {
        "title": "Enterprise Weekly State of the Business",
        "filter": lambda accounts: accounts["account_segment"] == "Enterprise",
    },
}

CLOSED_STAGES = {"Closed Won", "Closed Lost"}


def format_int(value: float | int) -> str:
    return f"{int(round(value)):,}"


def format_currency(value: float | int) -> str:
    return f"${int(round(value)):,.0f}"


def normalize_sfdc_id(value: object) -> str:
    if pd.isna(value):
        return ""
    string_value = str(value).strip()
    if not string_value or string_value.lower() == "nan":
        return ""
    integer_portion = string_value.split(".")[0]
    if integer_portion.isdigit():
        return integer_portion.zfill(12)
    return integer_portion


def markdown_table(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return "_No records._"
    headers = list(dataframe.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in dataframe.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in headers) + " |")
    return "\n".join(lines)


def build_reporting_window(datasets: dict[str, pd.DataFrame]) -> tuple[pd.Timestamp, pd.Timestamp]:
    leads = datasets["leads"].copy()
    usage = datasets["product_usage_events"].copy()
    leads["request_timestamp"] = pd.to_datetime(leads["request_timestamp"], utc=True)
    usage["event_timestamp"] = pd.to_datetime(usage["event_timestamp"], utc=True)
    period_end = max(leads["request_timestamp"].max(), usage["event_timestamp"].max()).normalize()
    period_start = period_end - pd.Timedelta(days=6)
    return period_start, period_end


def load_workflow_outputs() -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    outputs["territory_before"] = pd.read_csv(TERRITORY_BALANCER_DIR / "output/territory_summary_before.csv")
    outputs["territory_after"] = pd.read_csv(TERRITORY_BALANCER_DIR / "output/territory_summary_after.csv")
    outputs["territory_improvement"] = pd.read_csv(
        TERRITORY_BALANCER_DIR / "output/territory_balance_improvement_summary.csv"
    )
    outputs["free_tier"] = pd.read_csv(FREETIER_ALERT_DIR / "output/free_tier_usage_alerts.csv")
    outputs["lead_enrichment"] = pd.read_csv(LEAD_ENRICHMENT_DIR / "output/lead_enrichment_scenarios.csv")
    outputs["renewal_forms"] = pd.read_csv(
        RENEWAL_AUTOMATION_DIR / "output/renewal_form_processing_results.csv"
    )
    outputs["renewal_opportunities"] = pd.read_csv(
        RENEWAL_AUTOMATION_DIR / "output/salesforce_renewal_opportunities.csv"
    )
    outputs["attribution"] = pd.read_csv(MARKETING_ATTRIBUTION_DIR / "output/opportunity_attribution.csv")
    outputs["attribution_summary"] = pd.read_csv(MARKETING_ATTRIBUTION_DIR / "output/attribution_summary.csv")

    for dataframe_name in ["free_tier", "renewal_forms", "renewal_opportunities", "attribution"]:
        dataframe = outputs[dataframe_name]
        for column in dataframe.columns:
            if column.endswith("_id") or column == "account_id":
                dataframe[column] = dataframe[column].map(normalize_sfdc_id)
        outputs[dataframe_name] = dataframe

    return outputs


def build_rep_table(opportunities: pd.DataFrame, accounts: pd.DataFrame, value_column: str) -> pd.DataFrame:
    account_owner = accounts[["account_id", "owner_name", "owner_role", "account_segment"]].copy()
    owner_pipeline = opportunities.merge(account_owner, on="account_id", how="left")
    rep_table = (
        owner_pipeline.groupby("owner_name", dropna=False)
        .agg(accounts=("account_id", "nunique"), pipeline_nnarr=(value_column, "sum"))
        .reset_index()
        .sort_values(["pipeline_nnarr", "owner_name"], ascending=[False, True])
    )
    return rep_table


def build_report_markdown(
    report_key: str,
    report_title: str,
    accounts: pd.DataFrame,
    opportunities: pd.DataFrame,
    leads: pd.DataFrame,
    usage_events: pd.DataFrame,
    workflow_outputs: dict[str, pd.DataFrame],
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> str:
    mask = REPORTS[report_key]["filter"](accounts)
    report_accounts = accounts[mask].copy()
    report_account_ids = set(report_accounts["account_id"].map(normalize_sfdc_id))

    accounts = accounts.copy()
    accounts["account_id"] = accounts["account_id"].map(normalize_sfdc_id)
    opportunities["account_id"] = opportunities["account_id"].map(normalize_sfdc_id)
    leads["matched_account_id"] = leads["matched_account_id"].fillna("").map(normalize_sfdc_id)
    usage_events["account_id"] = usage_events["account_id"].map(normalize_sfdc_id)

    opportunities["created_date"] = pd.to_datetime(opportunities["created_date"], utc=True)
    opportunities["close_date"] = pd.to_datetime(opportunities["close_date"], utc=True)
    leads["request_timestamp"] = pd.to_datetime(leads["request_timestamp"], utc=True)
    usage_events["event_timestamp"] = pd.to_datetime(usage_events["event_timestamp"], utc=True)

    report_opps = opportunities[opportunities["account_id"].isin(report_account_ids)].copy()
    created_last_week = report_opps[
        (report_opps["created_date"] >= period_start) & (report_opps["created_date"] <= period_end)
    ].copy()
    closed_last_week = report_opps[
        (report_opps["close_date"] >= period_start)
        & (report_opps["close_date"] <= period_end)
        & (report_opps["stage_name"].isin(CLOSED_STAGES))
    ].copy()
    report_leads = leads[leads["matched_account_id"].isin(report_account_ids)].copy()
    leads_last_week = report_leads[
        (report_leads["request_timestamp"] >= period_start) & (report_leads["request_timestamp"] <= period_end)
    ].copy()
    usage_last_week = usage_events[
        (usage_events["account_id"].isin(report_account_ids))
        & (usage_events["event_timestamp"] >= period_start)
        & (usage_events["event_timestamp"] <= period_end)
    ].copy()

    top_reps = build_rep_table(created_last_week, accounts, "nnarr").head(5)
    lowest_reps = build_rep_table(created_last_week, accounts, "nnarr").sort_values(
        ["pipeline_nnarr", "owner_name"], ascending=[True, True]
    ).head(5)

    attribution = workflow_outputs["attribution"].copy()
    attribution = attribution[attribution["account_id"].isin(report_account_ids)]
    attribution_rollup = (
        attribution.groupby("first_touch_source", dropna=False)
        .agg(opportunities=("opportunity_id", "count"), pipeline_nnarr=("nnarr", "sum"))
        .reset_index()
        .sort_values(["pipeline_nnarr", "opportunities"], ascending=[False, False])
        .head(5)
    )

    renewal_forms = workflow_outputs["renewal_forms"].copy()
    renewal_forms = renewal_forms[renewal_forms["account_id"].isin(report_account_ids)]
    free_tier = workflow_outputs["free_tier"].copy()
    free_tier = free_tier[free_tier["account_id"].isin(report_account_ids)]
    lead_enrichment = workflow_outputs["lead_enrichment"].copy()
    if "account_segment" in lead_enrichment.columns and report_key != "am":
        segment_map = {"smb": "SMB", "mm": "Mid-Market", "ent": "Enterprise"}
        lead_enrichment = lead_enrichment[lead_enrichment["account_segment"] == segment_map[report_key]]

    territory_note = ""
    if report_key == "am":
        improvement = workflow_outputs["territory_improvement"].copy()
        count_row = improvement[improvement["metric"] == "Accounts per AM"].iloc[0]
        total_mrr_row = improvement[improvement["metric"] == "Total MRR per AM"].iloc[0]
        territory_note = (
            f"- Account-count range tightened from `{format_int(count_row['range_before'])}` to "
            f"`{format_int(count_row['range_after'])}`.\n"
            f"- Total-MRR range tightened from `{format_currency(total_mrr_row['range_before'])}` to "
            f"`{format_currency(total_mrr_row['range_after'])}`.\n"
        )

    headline_metrics = pd.DataFrame(
        [
            {"Metric": "Accounts in scope", "Value": format_int(len(report_accounts))},
            {"Metric": "Current ARR in scope", "Value": format_currency(report_accounts["account_mrr"].sum() * 12)},
            {"Metric": "Pipeline created last week", "Value": format_currency(created_last_week["nnarr"].sum())},
            {
                "Metric": "Closed-won last week",
                "Value": format_currency(closed_last_week.loc[closed_last_week["stage_name"] == "Closed Won", "nnarr"].sum()),
            },
            {
                "Metric": "Closed-lost last week",
                "Value": format_currency(closed_last_week.loc[closed_last_week["stage_name"] == "Closed Lost", "nnarr"].sum()),
            },
            {"Metric": "Leads created last week", "Value": format_int(len(leads_last_week))},
        ]
    )

    last_week_table = pd.DataFrame(
        [
            {"Metric": "Opportunities created", "Value": format_int(len(created_last_week))},
            {"Metric": "NNARR created", "Value": format_currency(created_last_week["nnarr"].sum())},
            {"Metric": "Closed-won opportunities", "Value": format_int((closed_last_week["stage_name"] == "Closed Won").sum())},
            {"Metric": "Closed-lost opportunities", "Value": format_int((closed_last_week["stage_name"] == "Closed Lost").sum())},
            {"Metric": "Renewal forms processed", "Value": format_int((renewal_forms["status"] == "processed").sum())},
            {"Metric": "Renewal forms blocked", "Value": format_int((renewal_forms["status"] == "blocked").sum())},
            {"Metric": "Free-tier alert accounts", "Value": format_int(len(free_tier))},
            {"Metric": "Usage events last week", "Value": format_int(len(usage_last_week))},
        ]
    )

    workflow_highlights = [
        f"- Lead enrichment outcomes in scope: `{format_int(len(lead_enrichment))}`.",
        f"- Renewal forms processed in scope: `{format_int((renewal_forms['status'] == 'processed').sum())}`; blocked: `{format_int((renewal_forms['status'] == 'blocked').sum())}`.",
        f"- Free-tier alert accounts in scope: `{format_int(len(free_tier))}`.",
    ]
    if territory_note:
        workflow_highlights.insert(0, territory_note.rstrip())

    report = f"""# {report_title}

_Reporting window: {period_start.date().isoformat()} to {period_end.date().isoformat()}_

## Headline Metrics

{markdown_table(headline_metrics)}

## Last Week

{markdown_table(last_week_table)}

## Top Reps

{markdown_table(top_reps.rename(columns={"owner_name": "Rep", "accounts": "Accounts", "pipeline_nnarr": "Created NNARR"}))}

## Lowest Reps / Risks

{markdown_table(lowest_reps.rename(columns={"owner_name": "Rep", "accounts": "Accounts", "pipeline_nnarr": "Created NNARR"}))}

## Attribution Highlights

{markdown_table(attribution_rollup.rename(columns={"first_touch_source": "First-Touch Source", "opportunities": "Opps", "pipeline_nnarr": "Pipeline NNARR"}))}

## Workflow Highlights

{chr(10).join(workflow_highlights)}
"""
    return report


def main() -> None:
    datasets = load_sample_data(DATA_DIR)
    workflow_outputs = load_workflow_outputs()
    accounts = datasets["accounts"].copy()
    opportunities = datasets["opportunities"].copy()
    leads = datasets["leads"].copy()
    usage_events = datasets["product_usage_events"].copy()
    period_start, period_end = build_reporting_window(datasets)

    REPORTING_ROOT.mkdir(parents=True, exist_ok=True)
    for report_key, metadata in REPORTS.items():
        report_dir = REPORTING_ROOT / f"{report_key}_weekly_report"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_body = build_report_markdown(
            report_key=report_key,
            report_title=metadata["title"],
            accounts=accounts.copy(),
            opportunities=opportunities.copy(),
            leads=leads.copy(),
            usage_events=usage_events.copy(),
            workflow_outputs=workflow_outputs,
            period_start=period_start,
            period_end=period_end,
        )
        (report_dir / "README.md").write_text(report_body)
        print(f"Wrote {report_dir / 'README.md'}")


if __name__ == "__main__":
    main()
