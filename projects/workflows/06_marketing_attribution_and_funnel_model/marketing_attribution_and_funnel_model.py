#!/usr/bin/env python3
"""Marketing attribution and funnel source-of-truth demo."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gtm_engineering.config import DATA_DIR, MARKETING_ATTRIBUTION_DIR
from gtm_engineering.synthetic_data import load_sample_data


OUTPUT_DIR = MARKETING_ATTRIBUTION_DIR / "output"
FIRST_TOUCH_LOOKBACK_DAYS = 365
LAST_TOUCH_LOOKBACK_DAYS = 90
DEFAULT_TOUCH_TYPE = "marketing_touch"

FIRST_TOUCH_SOURCE_BY_LEAD_SOURCE = {
    "Inbound": ("Organic Search", "organic_search", "SEO - Nonbrand"),
    "Demo Request": ("Paid Search", "paid_search", "Google Search - Demo"),
    "Event": ("Field Event", "field_event", "Executive Dinner"),
    "Partner": ("Partner", "partner", "Channel Partner"),
}

LAST_TOUCH_SEQUENCE = [
    ("Paid Social", "paid_social", "LinkedIn Retargeting"),
    ("Email", "email", "Lifecycle Nurture"),
    ("Direct", "direct", "Direct Visit"),
    ("Webinar", "webinar", "Pipeline Webinar"),
]


def build_touchpoints(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    leads = datasets["leads"].copy()
    leads["request_timestamp"] = pd.to_datetime(leads["request_timestamp"], utc=True)
    rows: list[dict[str, object]] = []

    for position, lead in enumerate(leads.itertuples(index=False), start=1):
        first_source, first_subsource, first_campaign = FIRST_TOUCH_SOURCE_BY_LEAD_SOURCE.get(
            lead.lead_source,
            ("Direct", "direct", "Direct Visit"),
        )
        first_touch_timestamp = lead.request_timestamp - timedelta(days=45 + (position % 75))
        rows.append(
            {
                "touch_id": f"touch_{position:06d}_ft",
                "lead_id": lead.lead_id,
                "account_id": lead.matched_account_id if pd.notna(lead.matched_account_id) else "",
                "touch_timestamp": first_touch_timestamp,
                "touch_type": DEFAULT_TOUCH_TYPE,
                "source": first_source,
                "subsource": first_subsource,
                "campaign": first_campaign,
            }
        )

        last_source, last_subsource, last_campaign = LAST_TOUCH_SEQUENCE[position % len(LAST_TOUCH_SEQUENCE)]
        last_touch_timestamp = lead.request_timestamp - timedelta(days=(position % 14) + 1)
        rows.append(
            {
                "touch_id": f"touch_{position:06d}_lt",
                "lead_id": lead.lead_id,
                "account_id": lead.matched_account_id if pd.notna(lead.matched_account_id) else "",
                "touch_timestamp": last_touch_timestamp,
                "touch_type": DEFAULT_TOUCH_TYPE,
                "source": last_source,
                "subsource": last_subsource,
                "campaign": last_campaign,
            }
        )

        if position % 5 == 0:
            nurture_timestamp = lead.request_timestamp - timedelta(days=position % 30 + 7)
            rows.append(
                {
                    "touch_id": f"touch_{position:06d}_nu",
                    "lead_id": lead.lead_id,
                    "account_id": lead.matched_account_id if pd.notna(lead.matched_account_id) else "",
                    "touch_timestamp": nurture_timestamp,
                    "touch_type": "nurture_touch",
                    "source": "Email",
                    "subsource": "email",
                    "campaign": "Mid-Funnel Nurture",
                }
            )

    touchpoints = pd.DataFrame(rows).sort_values("touch_timestamp").reset_index(drop=True)
    return touchpoints


def build_opportunity_attribution(datasets: dict[str, pd.DataFrame], touchpoints: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    opportunities = datasets["opportunities"].copy()
    accounts = datasets["accounts"].copy()
    leads = datasets["leads"].copy()
    opportunities["created_date"] = pd.to_datetime(opportunities["created_date"], utc=True)
    opportunities["close_date"] = pd.to_datetime(opportunities["close_date"], utc=True)
    leads["request_timestamp"] = pd.to_datetime(leads["request_timestamp"], utc=True)

    account_lookup = accounts.set_index("account_id").to_dict("index")
    leads_by_account = (
        leads[leads["matched_account_id"].notna()].groupby("matched_account_id")["lead_id"].apply(list).to_dict()
    )

    attribution_rows: list[dict[str, object]] = []
    hygiene_rows: list[dict[str, object]] = []

    for opportunity in opportunities.itertuples(index=False):
        account_id = str(opportunity.account_id)
        lead_ids = leads_by_account.get(account_id, [])
        candidate_touches = touchpoints[touchpoints["lead_id"].isin(lead_ids)].copy()
        candidate_touches = candidate_touches[candidate_touches["touch_timestamp"] <= opportunity.created_date]

        first_touch_floor = opportunity.created_date - pd.Timedelta(days=FIRST_TOUCH_LOOKBACK_DAYS)
        last_touch_floor = opportunity.created_date - pd.Timedelta(days=LAST_TOUCH_LOOKBACK_DAYS)
        first_touch_candidates = candidate_touches[candidate_touches["touch_timestamp"] >= first_touch_floor]
        last_touch_candidates = candidate_touches[candidate_touches["touch_timestamp"] >= last_touch_floor]

        if first_touch_candidates.empty:
            hygiene_rows.append(
                {
                    "entity_type": "opportunity",
                    "entity_id": opportunity.opportunity_id,
                    "exception_type": "missing_first_touch",
                    "detail": "No eligible marketing touch in the 365-day first-touch window before opportunity creation.",
                }
            )
        if last_touch_candidates.empty:
            hygiene_rows.append(
                {
                    "entity_type": "opportunity",
                    "entity_id": opportunity.opportunity_id,
                    "exception_type": "missing_last_touch",
                    "detail": "No eligible marketing touch in the 90-day last-touch window before opportunity creation.",
                }
            )

        first_touch = (
            first_touch_candidates.sort_values("touch_timestamp").iloc[0]
            if not first_touch_candidates.empty
            else None
        )
        last_touch = (
            last_touch_candidates.sort_values("touch_timestamp").iloc[-1]
            if not last_touch_candidates.empty
            else None
        )

        account = account_lookup.get(account_id, {})
        attribution_rows.append(
            {
                "opportunity_id": opportunity.opportunity_id,
                "account_id": account_id,
                "account_name": account.get("account_name", ""),
                "created_date": opportunity.created_date.date().isoformat(),
                "close_date": opportunity.close_date.date().isoformat(),
                "stage_name": opportunity.stage_name,
                "nnarr": int(opportunity.nnarr),
                "first_touch_source": first_touch["source"] if first_touch is not None else "Unattributed",
                "first_touch_campaign": first_touch["campaign"] if first_touch is not None else "",
                "first_touch_timestamp": (
                    first_touch["touch_timestamp"].isoformat() if first_touch is not None else ""
                ),
                "last_touch_source": last_touch["source"] if last_touch is not None else "Unattributed",
                "last_touch_campaign": last_touch["campaign"] if last_touch is not None else "",
                "last_touch_timestamp": last_touch["touch_timestamp"].isoformat() if last_touch is not None else "",
            }
        )

    return pd.DataFrame(attribution_rows), pd.DataFrame(hygiene_rows)


def build_funnel_summary(opportunity_attribution: pd.DataFrame) -> pd.DataFrame:
    summary = (
        opportunity_attribution.groupby(["first_touch_source", "last_touch_source"], dropna=False)
        .agg(
            opportunities=("opportunity_id", "count"),
            pipeline_nnarr=("nnarr", "sum"),
            won_nnarr=("nnarr", lambda series: opportunity_attribution.loc[series.index, "nnarr"][
                opportunity_attribution.loc[series.index, "stage_name"] == "Closed Won"
            ].sum()),
        )
        .reset_index()
        .sort_values(["pipeline_nnarr", "opportunities"], ascending=[False, False])
        .reset_index(drop=True)
    )
    return summary


def build_funnel_stage_summary(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    leads = datasets["leads"].copy()
    opportunities = datasets["opportunities"].copy()
    accounts = datasets["accounts"].copy()

    paying_accounts = accounts[accounts["account_mrr"] > 0]
    summary_rows = [
        {"stage": "Leads", "record_count": int(len(leads)), "matched_accounts": int(leads["matched_account_id"].notna().sum())},
        {"stage": "Opportunities", "record_count": int(len(opportunities)), "matched_accounts": int(opportunities["account_id"].nunique())},
        {"stage": "Customers", "record_count": int(len(paying_accounts)), "matched_accounts": int(len(paying_accounts))},
    ]
    return pd.DataFrame(summary_rows)


def main() -> None:
    datasets = load_sample_data(DATA_DIR)
    touchpoints = build_touchpoints(datasets)
    opportunity_attribution, hygiene_exceptions = build_opportunity_attribution(datasets, touchpoints)
    attribution_summary = build_funnel_summary(opportunity_attribution)
    funnel_stage_summary = build_funnel_stage_summary(datasets)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    touchpoints.to_csv(OUTPUT_DIR / "marketing_touchpoints.csv", index=False)
    opportunity_attribution.to_csv(OUTPUT_DIR / "opportunity_attribution.csv", index=False)
    attribution_summary.to_csv(OUTPUT_DIR / "attribution_summary.csv", index=False)
    funnel_stage_summary.to_csv(OUTPUT_DIR / "funnel_stage_summary.csv", index=False)
    hygiene_exceptions.to_csv(OUTPUT_DIR / "tracking_hygiene_exceptions.csv", index=False)

    print(opportunity_attribution.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
