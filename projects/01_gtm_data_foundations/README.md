# GTM Data Foundations

## Problem Statement

Every GTM workflow is weaker if teams are looking at different versions of the business.

## Output

This project creates one operating picture of the company.

| Metric | Value |
|---|---:|
| Total owners | 20 |
| Paying accounts | 300 |
| Non-paying accounts | 300 |
| Leads | 180 |
| Opportunities | 210 |
| Product usage events | 5,000 |

### Modeled Timeframe

| Dataset | Modeled Window |
|---|---|
| Leads | Past 180 days |
| Opportunities | Past 365 days of pipeline creation |
| Usage events | Past 7 days |

This means the lead file shows recent demand, the opportunity file shows the last year of pipeline creation, and the usage file shows the last week of product engagement.

### Account Counts

| Segment | Paying Accounts | Non-Paying Accounts |
|---|---:|---:|
| SMB | 80 | 121 |
| Mid-Market | 202 | 94 |
| Enterprise | 18 | 85 |

### Account Percentages

| Segment | Paying % of Paying Accounts | Non-Paying % of Non-Paying Accounts |
|---|---:|---:|
| SMB | 26.7% | 40.3% |
| Mid-Market | 67.3% | 31.3% |
| Enterprise | 6.0% | 28.3% |

The paying base is concentrated in Mid-Market. The free-product base is broader, with SMB the largest slice.

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
