"""Synthetic GTM data generation shared across portfolio projects."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from .config import DATASET_FILENAMES, DEFAULT_RANDOM_SEED

FREE_PLAN = "Free"
PRO_PLAN = "Pro"
ENTERPRISE_PLAN = "Enterprise"
PAID_PLANS = [PRO_PLAN, ENTERPRISE_PLAN]
PERSONAL_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"}

OWNER_COUNT_PER_ROLE = 10
PAID_ACCOUNT_COUNT = 300
FREE_PRODUCT_ACCOUNT_COUNT = 300
LEAD_COUNT = 180
OPPORTUNITY_COUNT = 210
PRODUCT_USAGE_EVENT_COUNT = 5000

TARGET_COMPANY_ARR = 50_000_000
TARGET_ANNUAL_GROWTH_RATE = 0.30
TARGET_PIPELINE_WIN_RATE = 0.30
TARGET_ACCOUNT_MRR_MEDIAN = 11_500
ACCOUNT_MRR_GEOMETRIC_STANDARD_DEVIATION = 1.55
MIN_ACCOUNT_MRR = 2_500
MAX_ACCOUNT_MRR = 120_000

SEGMENT_OPTIONS = ["SMB", "Mid-Market", "Enterprise"]
SEGMENT_SMB = "SMB"
SEGMENT_MID_MARKET = "Mid-Market"
SEGMENT_ENTERPRISE = "Enterprise"
AM_OWNER_SEGMENT_COUNTS = {
    SEGMENT_SMB: 5,
    SEGMENT_MID_MARKET: 5,
    SEGMENT_ENTERPRISE: 0,
}
AE_OWNER_SEGMENT_COUNTS = {
    SEGMENT_SMB: 4,
    SEGMENT_MID_MARKET: 3,
    SEGMENT_ENTERPRISE: 3,
}
AM_ROLE = "AM"
AE_ROLE = "AE"

INDUSTRY_OPTIONS = ["SaaS", "Fintech", "Retail", "Healthcare", "Media", "Manufacturing"]
EMPLOYEE_BAND_OPTIONS = ["1-50", "51-200", "201-500", "501-2000", "2000+"]
EMPLOYEE_BAND_WEIGHTS = [0.25, 0.30, 0.20, 0.15, 0.10]
RENEWAL_QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
RENEWAL_QUARTER_WEIGHTS = [0.22, 0.24, 0.25, 0.29]

LOW_MRR_THRESHOLD = 8_000
MID_MRR_THRESHOLD = 22_000
LOW_MRR_PRODUCT_OPTIONS = [1, 2]
LOW_MRR_PRODUCT_WEIGHTS = [0.65, 0.35]
MID_MRR_PRODUCT_OPTIONS = [2, 3, 4]
MID_MRR_PRODUCT_WEIGHTS = [0.25, 0.45, 0.30]
HIGH_MRR_PRODUCT_OPTIONS = [3, 4, 5]
HIGH_MRR_PRODUCT_WEIGHTS = [0.20, 0.45, 0.35]
LOW_MRR_ICP_OPTIONS = [1, 2, 3]
LOW_MRR_ICP_WEIGHTS = [0.55, 0.30, 0.15]
MID_MRR_ICP_OPTIONS = [2, 3, 4]
MID_MRR_ICP_WEIGHTS = [0.25, 0.50, 0.25]
HIGH_MRR_ICP_OPTIONS = [3, 4, 5]
HIGH_MRR_ICP_WEIGHTS = [0.20, 0.45, 0.35]
LOCKED_ACCOUNT_COUNT_PER_BIASED_OWNER = 2
AM_COUNT_VARIATION_OPTIONS = [-3, -2, -1, 0, 1, 2, 3]
AM_COUNT_VARIATION_WEIGHTS = [0.08, 0.12, 0.18, 0.24, 0.18, 0.12, 0.08]

FREE_ACCOUNT_PRODUCT_OPTIONS = [0, 1]
FREE_ACCOUNT_PRODUCT_WEIGHTS = [0.30, 0.70]
FREE_ACCOUNT_ICP_OPTIONS = [1, 2, 3]
FREE_ACCOUNT_ICP_WEIGHTS = [0.55, 0.30, 0.15]
FREE_ACCOUNT_OWNERLESS_AM_ID = ""
FREE_ACCOUNT_MRR = 0
FREE_ACCOUNT_RENEWAL_QUARTER = ""
FREE_ACCOUNT_NAME_PREFIX = "Free"
EMPTY_OWNER_ID = ""
EMPTY_OWNER_NAME = ""
EMPTY_OWNER_ROLE = ""

LEAD_ACCOUNT_MATCH_RATE = 0.75
LEAD_JOB_TITLE_OPTIONS = ["Head of Ops", "RevOps Manager", "Marketing Director", "CTO", "VP Sales"]
LEAD_COUNTRY_OPTIONS = ["US", "UK", "SG", "AU", "DE"]
LEAD_COUNTRY_WEIGHTS = [0.55, 0.15, 0.10, 0.10, 0.10]
LEAD_SOURCE_OPTIONS = ["Inbound", "Demo Request", "Event", "Partner"]
LEAD_STATUS_OPTIONS = ["Open", "Working", "Qualified"]
LEAD_STATUS_WEIGHTS = [0.45, 0.35, 0.20]
LEAD_MODELED_TIMEFRAME_DAYS = 180

OPPORTUNITY_STAGE_OPTIONS = ["Prospecting", "Discovery", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
OPPORTUNITY_STAGE_WEIGHTS = [0.20, 0.20, 0.20, 0.15, 0.15, 0.10]
MIN_OPPORTUNITY_NNARR = 40_000
MAX_OPPORTUNITY_NNARR = 600_000
OPPORTUNITY_CREATED_LOOKBACK_DAYS = 120
MIN_CLOSE_DATE_OFFSET_DAYS = 30
MAX_CLOSE_DATE_OFFSET_DAYS = 365
OPPORTUNITY_MODELED_TIMEFRAME_DAYS = 365

USAGE_EVENT_TYPES = ["page_view", "dashboard_view", "integration_setup", "alert_created", "api_call"]
USAGE_EVENT_TYPE_WEIGHTS = [0.45, 0.20, 0.10, 0.10, 0.15]
FREE_PLAN_USAGE_WEIGHT = 3
PAID_PLAN_USAGE_WEIGHT = 2
USAGE_EVENT_MODELED_TIMEFRAME_DAYS = 7
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
MAX_USERS_PER_ACCOUNT_FOR_USAGE = 4


def _build_segment_sequence(segment_counts: dict[str, int]) -> list[str]:
    segment_sequence = []
    for segment_name in SEGMENT_OPTIONS:
        segment_sequence.extend([segment_name] * segment_counts[segment_name])
    np.random.shuffle(segment_sequence)
    return segment_sequence


def _account_segment_from_mrr(account_mrr: int) -> str:
    if account_mrr < LOW_MRR_THRESHOLD:
        return SEGMENT_SMB
    if account_mrr < MID_MRR_THRESHOLD:
        return SEGMENT_MID_MARKET
    return SEGMENT_ENTERPRISE


def _owner_lookup(owners: pd.DataFrame, owner_role: str, segment: str) -> pd.DataFrame:
    return owners[(owners["owner_role"] == owner_role) & (owners["segment"] == segment)].reset_index(drop=True)


def _allocate_scaled_mrr(raw_mrr_values: list[int], target_total_mrr: int) -> list[int]:
    scaled_values = np.array(raw_mrr_values, dtype=float)
    scaled_values *= target_total_mrr / scaled_values.sum()
    scaled_values = np.clip(np.rint(scaled_values), MIN_ACCOUNT_MRR, MAX_ACCOUNT_MRR).astype(int)

    difference = int(target_total_mrr - scaled_values.sum())
    adjustable_indices = np.argsort(-scaled_values)
    step = 1 if difference > 0 else -1
    remaining = abs(difference)

    while remaining > 0:
        adjusted = False
        for index in adjustable_indices:
            proposed = scaled_values[index] + step
            if MIN_ACCOUNT_MRR <= proposed <= MAX_ACCOUNT_MRR:
                scaled_values[index] = proposed
                remaining -= 1
                adjusted = True
                if remaining == 0:
                    break
        if not adjusted:
            break

    return scaled_values.astype(int).tolist()


def _allocate_nnarr_values(opportunity_count: int, target_pipeline_nnarr: int) -> list[int]:
    weights = np.random.dirichlet(np.ones(opportunity_count))
    nnarr_values = np.rint(weights * target_pipeline_nnarr).astype(int)
    nnarr_values = np.clip(nnarr_values, MIN_OPPORTUNITY_NNARR, MAX_OPPORTUNITY_NNARR)

    difference = int(target_pipeline_nnarr - nnarr_values.sum())
    adjustable_indices = np.argsort(-nnarr_values)
    step = 1 if difference > 0 else -1
    remaining = abs(difference)

    while remaining > 0:
        adjusted = False
        for index in adjustable_indices:
            proposed = nnarr_values[index] + step
            if MIN_OPPORTUNITY_NNARR <= proposed <= MAX_OPPORTUNITY_NNARR:
                nnarr_values[index] = proposed
                remaining -= 1
                adjusted = True
                if remaining == 0:
                    break
        if not adjusted:
            break

    return nnarr_values.astype(int).tolist()


def _build_owners() -> pd.DataFrame:
    rows = []
    am_segments = _build_segment_sequence(AM_OWNER_SEGMENT_COUNTS)
    ae_segments = _build_segment_sequence(AE_OWNER_SEGMENT_COUNTS)

    for index in range(OWNER_COUNT_PER_ROLE):
        rows.append(
            {
                "owner_id": f"005CSM{index + 1:05d}",
                "owner_name": f"AM_{index + 1}",
                "owner_role": AM_ROLE,
                "segment": am_segments[index],
                "slack_destination": f"UAM{index + 1:07d}",
            }
        )

    for index in range(OWNER_COUNT_PER_ROLE):
        rows.append(
            {
                "owner_id": f"005AE{index + 1:06d}",
                "owner_name": f"AE_{index + 1}",
                "owner_role": AE_ROLE,
                "segment": ae_segments[index],
                "slack_destination": f"UAE{index + 1:07d}",
            }
        )

    return pd.DataFrame(rows)


def _build_paid_accounts(owners: pd.DataFrame, account_count: int) -> pd.DataFrame:
    rows = []
    lognormal_mean = np.log(TARGET_ACCOUNT_MRR_MEDIAN)
    lognormal_sigma = np.log(ACCOUNT_MRR_GEOMETRIC_STANDARD_DEVIATION)
    raw_mrr_values = [
        int(
            np.clip(
                np.random.lognormal(mean=lognormal_mean, sigma=lognormal_sigma),
                MIN_ACCOUNT_MRR,
                MAX_ACCOUNT_MRR,
            )
        )
        for _ in range(account_count)
    ]
    target_total_mrr = TARGET_COMPANY_ARR // 12
    scaled_mrr_values = _allocate_scaled_mrr(raw_mrr_values, target_total_mrr=target_total_mrr)

    am_owners = owners[owners["owner_role"] == AM_ROLE].copy().sort_values("owner_name").reset_index(drop=True)
    am_target_counts = _build_am_target_counts(am_owners=am_owners, account_count=account_count)
    am_assigned_counts = {owner_id: 0 for owner_id in am_owners["owner_id"]}

    for index in range(account_count):
        company_slug = f"company{index + 1:03d}"
        account_mrr = scaled_mrr_values[index]
        account_segment = _account_segment_from_mrr(account_mrr)

        if account_segment == SEGMENT_SMB:
            products_used = int(np.random.choice(LOW_MRR_PRODUCT_OPTIONS, p=LOW_MRR_PRODUCT_WEIGHTS))
            icp_tier = int(np.random.choice(LOW_MRR_ICP_OPTIONS, p=LOW_MRR_ICP_WEIGHTS))
            plan_type = PRO_PLAN
        elif account_segment == SEGMENT_MID_MARKET:
            products_used = int(np.random.choice(MID_MRR_PRODUCT_OPTIONS, p=MID_MRR_PRODUCT_WEIGHTS))
            icp_tier = int(np.random.choice(MID_MRR_ICP_OPTIONS, p=MID_MRR_ICP_WEIGHTS))
            plan_type = PRO_PLAN
        else:
            products_used = int(np.random.choice(HIGH_MRR_PRODUCT_OPTIONS, p=HIGH_MRR_PRODUCT_WEIGHTS))
            icp_tier = int(np.random.choice(HIGH_MRR_ICP_OPTIONS, p=HIGH_MRR_ICP_WEIGHTS))
            plan_type = ENTERPRISE_PLAN

        segment_aes = _owner_lookup(owners, AE_ROLE, account_segment)
        ae_owner = segment_aes.sample(1).iloc[0]

        if account_segment == SEGMENT_ENTERPRISE:
            am_owner = None
            owner_id = ae_owner["owner_id"]
            owner_name = ae_owner["owner_name"]
            owner_role = AE_ROLE
        else:
            segment_ams = owners[owners["owner_role"] == AM_ROLE].copy().reset_index(drop=True)
            segment_ams["remaining_capacity"] = segment_ams["owner_id"].map(
                lambda owner_id: am_target_counts[owner_id] - am_assigned_counts[owner_id]
            )
            available_ams = segment_ams[segment_ams["remaining_capacity"] > 0]
            if available_ams.empty:
                available_ams = segment_ams
            if available_ams["remaining_capacity"].sum() > 0:
                am_owner = available_ams.sample(1, weights="remaining_capacity").iloc[0]
            else:
                am_owner = available_ams.sample(1).iloc[0]
            owner_id = am_owner["owner_id"]
            owner_name = am_owner["owner_name"]
            owner_role = AM_ROLE
            am_assigned_counts[owner_id] += 1

        rows.append(
            {
                "account_id": f"001{index + 1:09d}",
                "account_name": f"{company_slug.title()} Labs",
                "domain": f"{company_slug}.com",
                "industry": np.random.choice(INDUSTRY_OPTIONS),
                "employee_band": np.random.choice(
                    EMPLOYEE_BAND_OPTIONS,
                    p=EMPLOYEE_BAND_WEIGHTS,
                ),
                "account_segment": account_segment,
                "plan_type": plan_type,
                "account_mrr": account_mrr,
                "products_used": products_used,
                "icp_tier": icp_tier,
                "renewal_quarter": np.random.choice(RENEWAL_QUARTERS, p=RENEWAL_QUARTER_WEIGHTS),
                "am_owner_id": am_owner["owner_id"] if am_owner is not None else EMPTY_OWNER_ID,
                "ae_owner_id": ae_owner["owner_id"],
                "owner_id": owner_id,
                "owner_name": owner_name,
                "owner_role": owner_role,
                "must_keep_with_owner": False,
                "last_interesting_moment": "",
            }
        )

    accounts = pd.DataFrame(rows)

    am_owner_ids = am_owners["owner_id"].tolist()
    am_total_mrr = (
        accounts[accounts["owner_role"] == AM_ROLE].groupby("owner_id")["account_mrr"].sum().sort_values(ascending=False)
    )
    locked_owner_ids = am_total_mrr.head(2).index.tolist()

    for owner_id in locked_owner_ids:
        locked = (
            accounts[accounts["owner_id"] == owner_id]
            .sort_values("account_mrr", ascending=False)
            .head(LOCKED_ACCOUNT_COUNT_PER_BIASED_OWNER)
            .index
        )
        accounts.loc[locked, "must_keep_with_owner"] = True

    return accounts


def _build_am_target_counts(am_owners: pd.DataFrame, account_count: int) -> dict[str, int]:
    owner_ids = am_owners["owner_id"].tolist()
    base_count = account_count // len(owner_ids)
    remainder = account_count % len(owner_ids)
    target_counts = {owner_id: base_count for owner_id in owner_ids}

    for owner_id in owner_ids[:remainder]:
        target_counts[owner_id] += 1

    planned_deltas = np.random.choice(AM_COUNT_VARIATION_OPTIONS, size=len(owner_ids), p=AM_COUNT_VARIATION_WEIGHTS)
    planned_deltas = planned_deltas - int(planned_deltas.sum() / len(owner_ids))
    adjusted_counts = np.array([target_counts[owner_id] for owner_id in owner_ids], dtype=int) + planned_deltas
    adjusted_counts = np.clip(adjusted_counts, base_count - 4, base_count + 4)

    difference = account_count - int(adjusted_counts.sum())
    step = 1 if difference > 0 else -1
    remaining = abs(difference)
    order = np.argsort(adjusted_counts if step > 0 else -adjusted_counts)

    while remaining > 0:
        for index in order:
            proposed = adjusted_counts[index] + step
            if base_count - 4 <= proposed <= base_count + 4:
                adjusted_counts[index] = proposed
                remaining -= 1
                if remaining == 0:
                    break

    return dict(zip(owner_ids, adjusted_counts.tolist()))


def _build_free_product_accounts(
    owners: pd.DataFrame,
    starting_account_number: int,
    free_account_count: int,
) -> pd.DataFrame:
    rows = []

    for index in range(free_account_count):
        account_number = starting_account_number + index + 1
        company_slug = f"freeworkspace{index + 1:03d}"
        ae_owner = owners[owners["owner_role"] == AE_ROLE].sample(1).iloc[0]
        account_segment = ae_owner["segment"]

        rows.append(
            {
                "account_id": f"001{account_number:09d}",
                "account_name": f"{FREE_ACCOUNT_NAME_PREFIX} {company_slug.title()}",
                "domain": f"{company_slug}.com",
                "industry": np.random.choice(INDUSTRY_OPTIONS),
                "employee_band": np.random.choice(EMPLOYEE_BAND_OPTIONS, p=EMPLOYEE_BAND_WEIGHTS),
                "account_segment": account_segment,
                "plan_type": FREE_PLAN,
                "account_mrr": FREE_ACCOUNT_MRR,
                "products_used": int(np.random.choice(FREE_ACCOUNT_PRODUCT_OPTIONS, p=FREE_ACCOUNT_PRODUCT_WEIGHTS)),
                "icp_tier": int(np.random.choice(FREE_ACCOUNT_ICP_OPTIONS, p=FREE_ACCOUNT_ICP_WEIGHTS)),
                "renewal_quarter": FREE_ACCOUNT_RENEWAL_QUARTER,
                "am_owner_id": FREE_ACCOUNT_OWNERLESS_AM_ID,
                "ae_owner_id": ae_owner["owner_id"],
                "owner_id": ae_owner["owner_id"],
                "owner_name": ae_owner["owner_name"],
                "owner_role": AE_ROLE,
                "must_keep_with_owner": False,
                "last_interesting_moment": "",
            }
        )

    return pd.DataFrame(rows)


def _build_accounts(owners: pd.DataFrame) -> pd.DataFrame:
    paid_accounts = _build_paid_accounts(owners=owners, account_count=PAID_ACCOUNT_COUNT)
    free_accounts = _build_free_product_accounts(
        owners=owners,
        starting_account_number=PAID_ACCOUNT_COUNT,
        free_account_count=FREE_PRODUCT_ACCOUNT_COUNT,
    )
    return pd.concat([paid_accounts, free_accounts], ignore_index=True)


def _build_leads(accounts: pd.DataFrame, lead_count: int) -> pd.DataFrame:
    rows = []

    for index in range(lead_count):
        if np.random.random() < LEAD_ACCOUNT_MATCH_RATE:
            account = accounts.sample(1).iloc[0]
            domain = account["domain"]
            account_id = account["account_id"]
            company_name = account["account_name"]
            owner_id = account["owner_id"]
        else:
            domain = f"prospect{index + 1:03d}.com"
            account_id = None
            company_name = f"Prospect {index + 1}"
            owner_id = None

        rows.append(
            {
                "lead_id": f"00Q{index + 1:09d}",
                "first_name": f"Lead{index + 1}",
                "last_name": "Contact",
                "email": f"lead{index + 1}@{domain}",
                "company_name": company_name,
                "job_title": np.random.choice(LEAD_JOB_TITLE_OPTIONS),
                "country": np.random.choice(LEAD_COUNTRY_OPTIONS, p=LEAD_COUNTRY_WEIGHTS),
                "lead_source": np.random.choice(LEAD_SOURCE_OPTIONS),
                "status": np.random.choice(LEAD_STATUS_OPTIONS, p=LEAD_STATUS_WEIGHTS),
                "matched_account_id": account_id,
                "owner_id": owner_id,
                "request_timestamp": (
                    datetime.now(timezone.utc)
                    - timedelta(days=int(np.random.randint(0, LEAD_MODELED_TIMEFRAME_DAYS)))
                ).isoformat(),
            }
        )

    return pd.DataFrame(rows)


def _build_opportunities(accounts: pd.DataFrame, opportunity_count: int) -> pd.DataFrame:
    rows = []
    now = datetime.now(timezone.utc)
    current_arr = int(accounts["account_mrr"].sum() * 12)
    target_won_nnarr = int(round(current_arr * TARGET_ANNUAL_GROWTH_RATE))
    target_pipeline_nnarr = int(round(target_won_nnarr / TARGET_PIPELINE_WIN_RATE))
    nnarr_values = _allocate_nnarr_values(opportunity_count=opportunity_count, target_pipeline_nnarr=target_pipeline_nnarr)

    for index, nnarr in enumerate(nnarr_values):
        account = accounts.sample(1).iloc[0]
        stage = np.random.choice(OPPORTUNITY_STAGE_OPTIONS, p=OPPORTUNITY_STAGE_WEIGHTS)
        created_date = (now - timedelta(days=int(np.random.randint(0, OPPORTUNITY_CREATED_LOOKBACK_DAYS)))).date()
        close_offset_days = int(np.random.randint(MIN_CLOSE_DATE_OFFSET_DAYS, MAX_CLOSE_DATE_OFFSET_DAYS))
        close_date = (now + timedelta(days=close_offset_days)).date()
        rows.append(
            {
                "opportunity_id": f"006{index + 1:09d}",
                "account_id": account["account_id"],
                "opportunity_name": f"{account['account_name']} - FY27 Growth Plan",
                "owner_id": account["ae_owner_id"],
                "stage_name": stage,
                "nnarr": nnarr,
                "is_open": stage not in {"Closed Won", "Closed Lost"},
                "created_date": created_date.isoformat(),
                "close_date": close_date.isoformat(),
            }
        )

    return pd.DataFrame(rows)


def _build_usage_events(accounts: pd.DataFrame, event_count: int) -> pd.DataFrame:
    rows = []
    now = datetime.now(timezone.utc)
    weighted_accounts = []
    for _, account in accounts.iterrows():
        weight = FREE_PLAN_USAGE_WEIGHT if account["plan_type"] == FREE_PLAN else PAID_PLAN_USAGE_WEIGHT
        weighted_accounts.extend([account["account_id"]] * weight)

    account_lookup = accounts.set_index("account_id").to_dict("index")

    for index in range(event_count):
        account_id = np.random.choice(weighted_accounts)
        account = account_lookup[account_id]
        timestamp = now - timedelta(
            days=int(np.random.randint(0, USAGE_EVENT_MODELED_TIMEFRAME_DAYS)),
            hours=int(np.random.randint(0, HOURS_PER_DAY)),
            minutes=int(np.random.randint(0, MINUTES_PER_HOUR)),
        )
        actor_number = int(np.random.randint(1, MAX_USERS_PER_ACCOUNT_FOR_USAGE + 1))
        rows.append(
            {
                "event_id": f"evt_{index + 1:06d}",
                "event_timestamp": timestamp.isoformat(),
                "account_id": account_id,
                "user_email": f"user{actor_number}@{account['domain']}",
                "event_type": np.random.choice(USAGE_EVENT_TYPES, p=USAGE_EVENT_TYPE_WEIGHTS),
                "source": "datadog_rum",
            }
        )

    return pd.DataFrame(rows)


def generate_synthetic_gtm_data(seed: int = DEFAULT_RANDOM_SEED) -> Dict[str, pd.DataFrame]:
    """Create internally consistent synthetic GTM dataframes."""

    np.random.seed(seed)

    owners = _build_owners()
    accounts = _build_accounts(owners=owners)
    leads = _build_leads(accounts=accounts, lead_count=LEAD_COUNT)
    paid_accounts = accounts[accounts["account_mrr"] > 0].copy()
    opportunities = _build_opportunities(accounts=paid_accounts, opportunity_count=OPPORTUNITY_COUNT)
    product_usage_events = _build_usage_events(accounts=accounts, event_count=PRODUCT_USAGE_EVENT_COUNT)

    return {
        "owners": owners,
        "accounts": accounts,
        "leads": leads,
        "opportunities": opportunities,
        "product_usage_events": product_usage_events,
    }


def save_synthetic_gtm_data(output_dir: Path, seed: int = DEFAULT_RANDOM_SEED) -> Dict[str, pd.DataFrame]:
    """Generate and save the synthetic dataset to CSV."""

    dataframes = generate_synthetic_gtm_data(seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    for dataset_name, dataframe in dataframes.items():
        dataframe.to_csv(output_dir / DATASET_FILENAMES[dataset_name], index=False)

    return dataframes


def load_sample_data(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load sample CSVs from disk while preserving CRM-style ID fields."""

    dtype_overrides = {
        "owners": {
            "owner_id": "string",
            "owner_name": "string",
            "owner_role": "string",
            "segment": "string",
            "slack_destination": "string",
        },
            "accounts": {
                "account_id": "string",
                "account_name": "string",
                "domain": "string",
                "industry": "string",
                "employee_band": "string",
                "account_segment": "string",
                "plan_type": "string",
                "renewal_quarter": "string",
                "am_owner_id": "string",
                "ae_owner_id": "string",
                "owner_id": "string",
                "owner_name": "string",
                "owner_role": "string",
                "last_interesting_moment": "string",
            },
        "leads": {
            "lead_id": "string",
            "first_name": "string",
            "last_name": "string",
            "email": "string",
            "company_name": "string",
            "job_title": "string",
            "country": "string",
            "lead_source": "string",
            "status": "string",
            "matched_account_id": "string",
            "owner_id": "string",
            "request_timestamp": "string",
        },
        "opportunities": {
            "opportunity_id": "string",
            "account_id": "string",
            "opportunity_name": "string",
            "owner_id": "string",
            "stage_name": "string",
            "nnarr": "string",
            "created_date": "string",
            "close_date": "string",
        },
        "product_usage_events": {
            "event_id": "string",
            "event_timestamp": "string",
            "account_id": "string",
            "user_email": "string",
            "event_type": "string",
            "source": "string",
        },
    }

    loaded = {}
    for dataset_name, filename in DATASET_FILENAMES.items():
        dataframe = pd.read_csv(data_dir / filename, dtype=dtype_overrides.get(dataset_name))
        if dataset_name == "accounts":
            dataframe["account_mrr"] = pd.to_numeric(dataframe["account_mrr"])
            dataframe["products_used"] = pd.to_numeric(dataframe["products_used"])
            dataframe["icp_tier"] = pd.to_numeric(dataframe["icp_tier"])
            dataframe["must_keep_with_owner"] = dataframe["must_keep_with_owner"].map(
                lambda value: str(value).lower() == "true"
            )
            dataframe["last_interesting_moment"] = dataframe["last_interesting_moment"].fillna("").astype(str)
        if dataset_name == "opportunities":
            dataframe["nnarr"] = pd.to_numeric(dataframe["nnarr"])
            dataframe["is_open"] = dataframe["is_open"].map(lambda value: str(value).lower() == "true")
        loaded[dataset_name] = dataframe
    return loaded
