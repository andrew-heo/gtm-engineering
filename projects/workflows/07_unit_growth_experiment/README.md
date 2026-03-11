# Unit Growth Experiment

## Introduction

This project simulates a Growth Manager experiment for Unit’s new out-of-the-box plan. The business problem is that current revenue is concentrated in large custom-plan customers, while the future of the company depends on opening a faster-moving growth wedge around a more standardized plan.

## Business Problem

The custom plan likely wins larger, slower enterprise deals. The out-of-the-box plan should create a different motion: faster adoption, lighter implementation, and clearer monetization for platforms that want embedded finance without a long custom build.

## Experiment Hypothesis

If Unit targets software platforms with strong payment-flow monetization potential and clear product fit for an out-of-the-box embedded-finance program, then messaging centered on **speed to launch** and **revenue capture from payment flows** should outperform generic embedded-finance messaging on:

- reply rate
- positive reply rate
- meetings booked
- qualification rate

## ICP Model

The project uses an explicit `A1` ICP model:

- `A` = high revenue potential
- `1` = high likelihood to purchase

### A: Revenue Potential

Revenue potential is scored from deterministic sub-signals:

- payment-flow fit
- current platform revenue scale
- product footprint / complexity
- ICP quality

### 1: Likelihood To Purchase

Likelihood to purchase is scored from:

- urgency of the use case
- product fit for an out-of-the-box plan
- implementation simplicity
- segment attractiveness for a faster self-serve / lighter-sales motion

Accounts are then graded as:

- `A1` = highest priority
- `A2` / `B1` = next best expansion candidates
- lower grades = comparison or deprioritized cohorts

## Segmentation Logic

The market is segmented into use-case-driven wedges:

- `property_management_software` → `rent_payments`
- `commerce_platforms` → `merchant_payouts`
- `vertical_saas` → `platform_monetization`
- `banking_software` → `embedded_accounts`
- `healthcare_admin` → `patient_payments`
- `b2b_erp` → `vendor_payments`

The **primary wedge** for the experiment is:

- `property_management_software`

This creates a focused test instead of trying to message every possible embedded-finance use case at once.

## Targeting Logic

The target cohort is built in two layers:

1. **Priority cohort**
   - accounts in the primary wedge
   - ICP grades of `A1`, `A2`, or `B1`
2. **Comparison cohort**
   - strong accounts outside the primary wedge
   - used to measure whether the primary wedge actually outperforms

## Persona Targeting

The project assigns likely buyer personas by use case:

- property management software → `CEO / GM`
- commerce platforms → `VP Payments`
- vertical SaaS → `Head of Product`
- banking software → `GM Embedded Finance`
- healthcare admin → `VP Strategy`
- B2B ERP → `Head of Revenue`

The goal is to align messaging with the owner of monetization, launch speed, or fintech roadmap decisions.

## Message Strategy

The project prioritizes three value props:

- launch speed
- monetization of payment flows
- less custom fintech implementation overhead

### Example Email

**Subject:** Monetizing rent payments at {{Company}}

Saw you're building a property management platform.

Many teams like yours are looking for ways to capture revenue from payment flows without taking on a long fintech build.

Unit recently launched an out-of-the-box program that helps platforms launch embedded banking and payments in weeks instead of months.

Worth a quick conversation?

## Experiment Metrics

The scorecard defines explicit success thresholds:

- reply rate target: `5%`
- positive reply rate target: `3%`
- meetings booked target: `1.5%`
- qualification rate target: `60%`

The experiment is successful if the primary wedge clears those thresholds and outperforms comparison cohorts.

## Outputs

- `output/icp_scored_accounts.csv`
- `output/segment_summary.csv`
- `output/target_account_list.csv`
- `output/persona_targeting.csv`
- `output/value_prop_matrix.csv`
- `output/outbound_message_variants.csv`
- `output/experiment_scorecard.csv`

## Technical

- deterministic ICP scoring using the `A1` model
- wedge-based market segmentation and use-case mapping
- target account selection for primary vs comparison cohorts
- persona targeting and message strategy generation
- experiment scorecard with explicit success thresholds

Run:

```bash
python3 projects/workflows/07_unit_growth_experiment/unit_growth_experiment.py
```
