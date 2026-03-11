"""Dry-run integration clients used by the portfolio demos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd

from .config import CLAY_CONFIG, DEFAULT_DRY_RUN, PARABOLA_CONFIG, SALESFORCE_CONFIG, SLACK_CONFIG, USAGE_EVENTS_CONFIG

LAST_INTERESTING_MOMENT_COLUMN = "last_interesting_moment"
SALESFORCE_ACCOUNT_ID_PREFIX = "001"
SALESFORCE_LEAD_ID_PREFIX = "00Q"
SALESFORCE_ID_PADDING = 9
INTEGRATION_STATUS_DRY_RUN = "dry_run"
INTEGRATION_STATUS_SIMULATED_LIVE = "simulated_live"
MESSAGE_ACCOUNT_UPDATE = "Account update prepared for Salesforce."
MESSAGE_ACCOUNT_CREATE = "Account create prepared for Salesforce."
MESSAGE_LEAD_CREATE = "Lead create prepared for Salesforce."
MESSAGE_TASK_CREATE = "Task create prepared for Salesforce."
MESSAGE_CLAY_ENRICHMENT = "Clay enrichment prepared."
MESSAGE_PARABOLA_FLOW = "Parabola flow run prepared."
MESSAGE_SLACK_POST = "Slack message prepared."
DEFAULT_CLAY_JOB_TITLE = "Operations Leader"
DEFAULT_CLAY_INDUSTRY = "SaaS"
DEFAULT_CLAY_COMPANY_SIZE = "201-500"
DEFAULT_CLAY_HQ_COUNTRY = "US"
EMAIL_DOMAIN_SEPARATOR = "@"
DOMAIN_SEGMENT_SEPARATOR = "."
WORD_SEPARATOR = " "
SLUG_SEPARATOR = "-"
EMAIL_NAME_SEPARATOR = "."
DEFAULT_USAGE_LOOKBACK_DAYS = 7


@dataclass
class IntegrationResult:
    status: str
    payload: Dict[str, Any]
    message: str


def _integration_status(dry_run: bool) -> str:
    return INTEGRATION_STATUS_DRY_RUN if dry_run else INTEGRATION_STATUS_SIMULATED_LIVE


class SalesforceClient:
    """Minimal Salesforce-like wrapper backed by local dataframes."""

    def __init__(
        self,
        datasets: Dict[str, pd.DataFrame],
        dry_run: bool = DEFAULT_DRY_RUN,
        config: Optional[Dict[str, str]] = None,
    ) -> None:
        self.dry_run = dry_run
        self.config = config or SALESFORCE_CONFIG
        self.datasets = {name: dataframe.copy() for name, dataframe in datasets.items()}
        if LAST_INTERESTING_MOMENT_COLUMN in self.datasets["accounts"].columns:
            self.datasets["accounts"][LAST_INTERESTING_MOMENT_COLUMN] = (
                self.datasets["accounts"][LAST_INTERESTING_MOMENT_COLUMN].fillna("").astype(str)
            )
        self._account_counter = len(self.datasets["accounts"]) + 1
        self._lead_counter = len(self.datasets["leads"]) + 1
        self._opportunity_counter = len(self.datasets["opportunities"]) + 1

    def find_lead_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        leads = self.datasets["leads"]
        matches = leads[leads["email"].str.lower() == email.lower()]
        return None if matches.empty else matches.iloc[0].to_dict()

    def find_account_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        accounts = self.datasets["accounts"]
        matches = accounts[accounts["domain"].str.lower() == domain.lower()]
        return None if matches.empty else matches.iloc[0].to_dict()

    def update_account(self, account_id: str, payload: Dict[str, Any]) -> IntegrationResult:
        mask = self.datasets["accounts"]["account_id"] == account_id
        if mask.any():
            for column, value in payload.items():
                if column in self.datasets["accounts"].columns:
                    self.datasets["accounts"].loc[mask, column] = value

        return IntegrationResult(
            status=_integration_status(self.dry_run),
            payload={"account_id": account_id, **payload},
            message=MESSAGE_ACCOUNT_UPDATE,
        )

    def create_account(self, payload: Dict[str, Any]) -> IntegrationResult:
        account_id = f"{SALESFORCE_ACCOUNT_ID_PREFIX}{self._account_counter:0{SALESFORCE_ID_PADDING}d}"
        self._account_counter += 1
        account_payload = {"account_id": account_id, **payload}
        self.datasets["accounts"] = pd.concat(
            [self.datasets["accounts"], pd.DataFrame([account_payload])],
            ignore_index=True,
        )
        return IntegrationResult(
            status=_integration_status(self.dry_run),
            payload=account_payload,
            message=MESSAGE_ACCOUNT_CREATE,
        )

    def create_lead(self, payload: Dict[str, Any]) -> IntegrationResult:
        lead_id = f"{SALESFORCE_LEAD_ID_PREFIX}{self._lead_counter:0{SALESFORCE_ID_PADDING}d}"
        self._lead_counter += 1
        lead_payload = {"lead_id": lead_id, **payload}
        self.datasets["leads"] = pd.concat(
            [self.datasets["leads"], pd.DataFrame([lead_payload])],
            ignore_index=True,
        )
        return IntegrationResult(
            status=_integration_status(self.dry_run),
            payload=lead_payload,
            message=MESSAGE_LEAD_CREATE,
        )

    def create_task(self, payload: Dict[str, Any]) -> IntegrationResult:
        return IntegrationResult(
            status=_integration_status(self.dry_run),
            payload=payload,
            message=MESSAGE_TASK_CREATE,
        )

    def create_opportunity(self, payload: Dict[str, Any]) -> IntegrationResult:
        opportunity_id = f"006{self._opportunity_counter:0{SALESFORCE_ID_PADDING}d}"
        self._opportunity_counter += 1
        opportunity_payload = {"opportunity_id": opportunity_id, **payload}
        self.datasets["opportunities"] = pd.concat(
            [self.datasets["opportunities"], pd.DataFrame([opportunity_payload])],
            ignore_index=True,
        )
        return IntegrationResult(
            status=_integration_status(self.dry_run),
            payload=opportunity_payload,
            message="Opportunity create prepared for Salesforce.",
        )


class ClayClient:
    """Portfolio-safe Clay enrichment wrapper."""

    def __init__(self, dry_run: bool = DEFAULT_DRY_RUN, config: Optional[Dict[str, str]] = None) -> None:
        self.dry_run = dry_run
        self.config = config or CLAY_CONFIG

    def enrich_person_company(self, email: str, company_name: Optional[str] = None) -> IntegrationResult:
        domain = email.split(EMAIL_DOMAIN_SEPARATOR)[-1].lower()
        company_guess = (
            company_name
            or domain.split(DOMAIN_SEGMENT_SEPARATOR)[0].replace(SLUG_SEPARATOR, WORD_SEPARATOR).title()
        )
        payload = {
            "email": email,
            "full_name": (
                f"{email.split(EMAIL_DOMAIN_SEPARATOR)[0].replace(EMAIL_NAME_SEPARATOR, WORD_SEPARATOR).title()}"
            ),
            "job_title": DEFAULT_CLAY_JOB_TITLE,
            "company_name": company_guess,
            "industry": DEFAULT_CLAY_INDUSTRY,
            "company_size": DEFAULT_CLAY_COMPANY_SIZE,
            "hq_country": DEFAULT_CLAY_HQ_COUNTRY,
        }
        return IntegrationResult(
            status=_integration_status(self.dry_run),
            payload=payload,
            message=MESSAGE_CLAY_ENRICHMENT,
        )


class ParabolaClient:
    """Portfolio-safe Parabola wrapper for form automation workflows."""

    def __init__(self, dry_run: bool = DEFAULT_DRY_RUN, config: Optional[Dict[str, str]] = None) -> None:
        self.dry_run = dry_run
        self.config = config or PARABOLA_CONFIG

    def run_flow(self, flow_name: str, payload: Dict[str, Any]) -> IntegrationResult:
        return IntegrationResult(
            status=_integration_status(self.dry_run),
            payload={"flow_name": flow_name, **payload},
            message=MESSAGE_PARABOLA_FLOW,
        )


class SlackClient:
    """Slack wrapper that returns payloads for demo review."""

    def __init__(self, dry_run: bool = DEFAULT_DRY_RUN, config: Optional[Dict[str, str]] = None) -> None:
        self.dry_run = dry_run
        self.config = config or SLACK_CONFIG

    def post_message(self, destination: str, text: str) -> IntegrationResult:
        return IntegrationResult(
            status=_integration_status(self.dry_run),
            payload={"channel": destination, "text": text},
            message=MESSAGE_SLACK_POST,
        )


class UsageEventsClient:
    """Simple usage event accessor."""

    def __init__(self, datasets: Dict[str, pd.DataFrame], config: Optional[Dict[str, str]] = None) -> None:
        self.datasets = datasets
        self.config = config or USAGE_EVENTS_CONFIG

    def fetch_recent_events(self, lookback_days: int = DEFAULT_USAGE_LOOKBACK_DAYS) -> pd.DataFrame:
        events = self.datasets["product_usage_events"].copy()
        events["event_timestamp"] = pd.to_datetime(events["event_timestamp"], utc=True)
        cutoff = pd.Timestamp(datetime.now(timezone.utc) - pd.Timedelta(days=lookback_days))
        return events[events["event_timestamp"] >= cutoff].copy()
