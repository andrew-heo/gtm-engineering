# GTM Data Foundations

## Introduction

This project creates the shared datasets used by the downstream workflows. In production, this would be the layer where core GTM inputs from systems like Salesforce and product telemetry are ingested and normalized into a canonical operating dataset.

## Output

This project acts as the shared GTM data layer for the portfolio, creating a canonical operating dataset that downstream workflows can consume. The dataset simulates a growth-stage SaaS company at roughly `$50M ARR`, with future `NNARR` pipeline sized to support about `30%` growth over the next 12 months at a `30%` win rate.

| Metric | Value |
|---|---:|
| Total owners | 20 |
| Paying accounts | 300 |
| Non-paying accounts | 300 |
| Leads | 180 |
| Opportunities | 210 |
| Product usage events | 5,000 |
| Current paid ARR | `$50.0M` |
| Future `NNARR` pipeline | `$50.0M` |
| Expected won `NNARR` at 30% win rate | `$15.0M` |

### Modeled Timeframe

| Dataset | Modeled Window |
|---|---|
| Leads | Past 180 days |
| Opportunities | Next 365 days of `NNARR` pipeline close dates |
| Usage events | Past 7 days |

This means the lead file shows recent demand, the opportunity file shows the next year of planned `NNARR` growth pipeline, and the usage file shows the last week of product engagement in one normalized operating view.

### Account Counts

| Segment | Paying Accounts | Non-Paying Accounts |
|---|---:|---:|
| SMB | 48 | 117 |
| Mid-Market | 225 | 94 |
| Enterprise | 27 | 89 |

### Account Percentages

| Segment | Paying % of Paying Accounts | Non-Paying % of Non-Paying Accounts |
|---|---:|---:|
| SMB | 16.0% | 39.0% |
| Mid-Market | 75.0% | 31.3% |
| Enterprise | 9.0% | 29.7% |

The paying base is concentrated in Mid-Market, which is consistent with a growth-stage SaaS company scaling toward enterprise complexity while still carrying a broad SMB free-product base.

## Logic

```mermaid
flowchart LR
    A[Owners] --> F[Shared GTM dataset]
    B[Accounts] --> F
    C[Leads] --> F
    D[Opportunities] --> F
    E[Usage events] --> F
```

Business rules:
- paying SMB and Mid-Market accounts are AM-owned
- paying Enterprise accounts are AE-owned
- free-product accounts are AE-owned

## Technical

- synthetic GTM source generation
- canonical dataset creation across owners, accounts, leads, opportunities, and usage events
- opportunity planning centered on `NNARR` as the core growth metric
- normalized CSV outputs with modeled time windows for downstream workflows
- `owners.csv`
- `accounts.csv`
- `leads.csv`
- `opportunities.csv`
- `product_usage_events.csv`
- `output/data_summary.csv`

Run:

```bash
python3 projects/01_gtm_data_foundations/generate_data.py
```
