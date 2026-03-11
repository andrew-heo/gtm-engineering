#!/usr/bin/env python3
"""Growth experiment simulation for a new out-of-the-box plan."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gtm_engineering.config import DATA_DIR, GROWTH_EXPERIMENT_DIR
from gtm_engineering.synthetic_data import load_sample_data


OUTPUT_DIR = GROWTH_EXPERIMENT_DIR / "output"
PRIMARY_WEDGE = "property_management_software"
SUCCESS_REPLY_RATE = 0.05
SUCCESS_POSITIVE_REPLY_RATE = 0.03
SUCCESS_MEETING_RATE = 0.015
SUCCESS_QUALIFICATION_RATE = 0.60

VERTICAL_RULES = {
    "Fintech": {"segment": "banking_software", "use_case": "embedded_accounts", "payment_flow_fit": 4, "urgency": 3},
    "Retail": {"segment": "commerce_platforms", "use_case": "merchant_payouts", "payment_flow_fit": 5, "urgency": 4},
    "Healthcare": {"segment": "healthcare_admin", "use_case": "patient_payments", "payment_flow_fit": 3, "urgency": 2},
    "Media": {"segment": "property_management_software", "use_case": "rent_payments", "payment_flow_fit": 5, "urgency": 5},
    "Manufacturing": {"segment": "b2b_erp", "use_case": "vendor_payments", "payment_flow_fit": 2, "urgency": 2},
    "SaaS": {"segment": "vertical_saas", "use_case": "platform_monetization", "payment_flow_fit": 4, "urgency": 4},
}

PERSONA_RULES = {
    "property_management_software": "CEO / GM",
    "commerce_platforms": "VP Payments",
    "vertical_saas": "Head of Product",
    "banking_software": "GM Embedded Finance",
    "healthcare_admin": "VP Strategy",
    "b2b_erp": "Head of Revenue",
}

VALUE_PROPS = {
    "rent_payments": ["launch embedded banking in weeks", "capture revenue from rent payment flows", "avoid heavy fintech buildouts"],
    "merchant_payouts": ["monetize merchant fund flows", "ship payments faster", "reduce bank-partner complexity"],
    "platform_monetization": ["add fintech monetization quickly", "turn payment flows into revenue", "launch without custom infrastructure"],
    "embedded_accounts": ["launch compliant banking products faster", "expand product monetization", "reduce implementation time"],
    "patient_payments": ["simplify payment experiences", "capture revenue on money movement", "ship with less operational lift"],
    "vendor_payments": ["modernize payables monetization", "reduce time to launch", "avoid custom fintech overhead"],
}


def build_growth_overlay(accounts: pd.DataFrame) -> pd.DataFrame:
    paying_accounts = accounts[(accounts["account_mrr"] > 0) & (accounts["plan_type"] != "Free")].copy()
    paying_accounts = paying_accounts.reset_index(drop=True)

    overlay_rows: list[dict[str, object]] = []
    for index, account in enumerate(paying_accounts.itertuples(index=False), start=1):
        rules = VERTICAL_RULES[account.industry]
        revenue_potential_score = min(
            5,
            max(
                1,
                round(
                    (
                        (account.account_mrr / 30000) * 2
                        + (account.products_used / 5)
                        + (6 - account.icp_tier) / 2
                        + rules["payment_flow_fit"] / 2
                    )
                ),
            ),
        )
        likelihood_score = min(
            5,
            max(
                1,
                round(
                    (
                        rules["payment_flow_fit"]
                        + rules["urgency"]
                        + (1 if account.account_segment in {"SMB", "Mid-Market"} else -1)
                        + (1 if account.products_used <= 4 else 0)
                    )
                    / 2
                ),
            ),
        )

        revenue_tier = "A" if revenue_potential_score >= 4 else ("B" if revenue_potential_score >= 3 else "C")
        likelihood_tier = "1" if likelihood_score >= 4 else ("2" if likelihood_score >= 3 else "3")
        icp_grade = f"{revenue_tier}{likelihood_tier}"
        wedge_priority = "primary" if rules["segment"] == PRIMARY_WEDGE else "comparison"

        overlay_rows.append(
            {
                "account_id": account.account_id,
                "account_name": account.account_name,
                "industry": account.industry,
                "account_segment": account.account_segment,
                "employee_band": account.employee_band,
                "segment_bucket": rules["segment"],
                "use_case_bucket": rules["use_case"],
                "payment_flow_fit_score": rules["payment_flow_fit"],
                "urgency_score": rules["urgency"],
                "revenue_potential_score": revenue_potential_score,
                "likelihood_to_buy_score": likelihood_score,
                "icp_grade": icp_grade,
                "buyer_persona": PERSONA_RULES[rules["segment"]],
                "wedge_priority": wedge_priority,
                "current_owner_name": account.owner_name,
            }
        )

    return pd.DataFrame(overlay_rows)


def build_segment_summary(overlay: pd.DataFrame) -> pd.DataFrame:
    return (
        overlay.groupby(["segment_bucket", "use_case_bucket", "wedge_priority"], dropna=False)
        .agg(
            accounts=("account_id", "count"),
            a1_accounts=("icp_grade", lambda values: (values == "A1").sum()),
            avg_revenue_potential=("revenue_potential_score", "mean"),
            avg_likelihood=("likelihood_to_buy_score", "mean"),
        )
        .reset_index()
        .sort_values(["wedge_priority", "a1_accounts", "accounts"], ascending=[True, False, False])
        .reset_index(drop=True)
    )


def build_target_accounts(overlay: pd.DataFrame) -> pd.DataFrame:
    priority = overlay[(overlay["segment_bucket"] == PRIMARY_WEDGE) & (overlay["icp_grade"].isin(["A1", "A2", "B1"]))].copy()
    comparison = overlay[(overlay["segment_bucket"] != PRIMARY_WEDGE) & (overlay["icp_grade"] == "A1")].copy()
    priority["cohort"] = "priority"
    comparison["cohort"] = "comparison"
    target_accounts = pd.concat([priority.head(50), comparison.head(25)], ignore_index=True)
    return target_accounts.sort_values(["cohort", "icp_grade", "revenue_potential_score"], ascending=[True, True, False]).reset_index(drop=True)


def build_persona_targeting(target_accounts: pd.DataFrame) -> pd.DataFrame:
    persona_df = target_accounts[
        ["account_id", "account_name", "segment_bucket", "use_case_bucket", "buyer_persona", "icp_grade", "cohort"]
    ].copy()
    persona_df["persona_reason"] = persona_df["use_case_bucket"].map(
        {
            "rent_payments": "Likely owns monetization and launch speed for platform revenue initiatives.",
            "merchant_payouts": "Likely evaluates payment monetization and bank-partner tradeoffs.",
            "platform_monetization": "Likely owns fintech roadmap and packaging decisions.",
            "embedded_accounts": "Likely owns banking product expansion.",
            "patient_payments": "Likely owns workflow and monetization efficiency.",
            "vendor_payments": "Likely owns payments monetization and operating leverage.",
        }
    )
    return persona_df


def build_value_prop_matrix(target_accounts: pd.DataFrame) -> pd.DataFrame:
    unique_use_cases = target_accounts[["segment_bucket", "use_case_bucket"]].drop_duplicates().reset_index(drop=True)
    rows: list[dict[str, str]] = []
    for use_case in unique_use_cases.itertuples(index=False):
        value_props = VALUE_PROPS[use_case.use_case_bucket]
        rows.append(
            {
                "segment_bucket": use_case.segment_bucket,
                "use_case_bucket": use_case.use_case_bucket,
                "value_prop_1": value_props[0],
                "value_prop_2": value_props[1],
                "value_prop_3": value_props[2],
                "short_message": (
                    "Launch embedded finance faster and monetize payment flows without a long custom build."
                ),
            }
        )
    return pd.DataFrame(rows)


def build_outbound_messages(target_accounts: pd.DataFrame) -> pd.DataFrame:
    sample_accounts = target_accounts.head(6).copy()
    messages: list[dict[str, str]] = []
    for account in sample_accounts.itertuples(index=False):
        company_short = account.account_name.replace(" Labs", "")
        use_case_phrase = account.use_case_bucket.replace("_", " ")
        messages.append(
            {
                "account_id": account.account_id,
                "account_name": account.account_name,
                "icp_grade": account.icp_grade,
                "buyer_persona": account.buyer_persona,
                "subject_line": f"Monetizing {use_case_phrase} at {company_short}",
                "message_variant": (
                    f"Saw you're building a {account.segment_bucket.replace('_', ' ')} platform.\n\n"
                    "Many teams like yours are looking for ways to capture revenue from payment flows "
                    "without taking on a long fintech build.\n\n"
                    "We recently launched an out-of-the-box program that helps platforms launch "
                    "embedded banking and payments in weeks instead of months.\n\n"
                    "Worth a quick conversation?"
                ),
            }
        )
    return pd.DataFrame(messages)


def build_experiment_scorecard(target_accounts: pd.DataFrame) -> pd.DataFrame:
    priority_accounts = target_accounts[target_accounts["cohort"] == "priority"].copy()
    comparison_accounts = target_accounts[target_accounts["cohort"] == "comparison"].copy()
    rows = [
        {
            "cohort": "priority",
            "accounts": len(priority_accounts),
            "reply_rate_target": SUCCESS_REPLY_RATE,
            "positive_reply_rate_target": SUCCESS_POSITIVE_REPLY_RATE,
            "meeting_rate_target": SUCCESS_MEETING_RATE,
            "qualification_rate_target": SUCCESS_QUALIFICATION_RATE,
            "success_criteria": "A1/A2 priority wedge should exceed reply and meeting thresholds.",
        },
        {
            "cohort": "comparison",
            "accounts": len(comparison_accounts),
            "reply_rate_target": SUCCESS_REPLY_RATE * 0.75,
            "positive_reply_rate_target": SUCCESS_POSITIVE_REPLY_RATE * 0.75,
            "meeting_rate_target": SUCCESS_MEETING_RATE * 0.75,
            "qualification_rate_target": SUCCESS_QUALIFICATION_RATE,
            "success_criteria": "Primary wedge should outperform comparison segments on reply and meeting rates.",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    datasets = load_sample_data(DATA_DIR)
    accounts = datasets["accounts"].copy()
    overlay = build_growth_overlay(accounts)
    segment_summary = build_segment_summary(overlay)
    target_accounts = build_target_accounts(overlay)
    persona_targeting = build_persona_targeting(target_accounts)
    value_prop_matrix = build_value_prop_matrix(target_accounts)
    outbound_messages = build_outbound_messages(target_accounts)
    experiment_scorecard = build_experiment_scorecard(target_accounts)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    overlay.to_csv(OUTPUT_DIR / "icp_scored_accounts.csv", index=False)
    segment_summary.to_csv(OUTPUT_DIR / "segment_summary.csv", index=False)
    target_accounts.to_csv(OUTPUT_DIR / "target_account_list.csv", index=False)
    persona_targeting.to_csv(OUTPUT_DIR / "persona_targeting.csv", index=False)
    value_prop_matrix.to_csv(OUTPUT_DIR / "value_prop_matrix.csv", index=False)
    outbound_messages.to_csv(OUTPUT_DIR / "outbound_message_variants.csv", index=False)
    experiment_scorecard.to_csv(OUTPUT_DIR / "experiment_scorecard.csv", index=False)

    print(target_accounts.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
