# Territory Balancer For AMs

## Introduction

Territory management is a core BAU workflow in a GTM ecosystem, and it breaks down when account coverage becomes uneven across AM books.

## Output

This project represents a BAU ownership and coverage workflow built on the shared GTM data layer, producing reassignment recommendations and Salesforce update payloads to rebalance AM books.

### Before State

| Metric | Low | High | Mean | Sum |
|---|---:|---:|---:|---:|
| Accounts per AM | 25 | 30 | 27.3 | 273 |
| Avg MRR per AM | 11,774 | 13,177 | 12,438 | 124,378 |
| Total MRR per AM | 294,362 | 372,043 | 339,856 | 3,398,559 |
| Q1 renewals per AM | 3 | 11 | 5.9 | 59 |
| Q2 renewals per AM | 3 | 10 | 6.1 | 61 |
| Q3 renewals per AM | 3 | 9 | 6.5 | 65 |
| Q4 renewals per AM | 6 | 11 | 8.8 | 88 |

### After State

| Metric | Low | High | Mean | Sum |
|---|---:|---:|---:|---:|
| Accounts per AM | 27 | 28 | 27.3 | 273 |
| Avg MRR per AM | 11,471 | 13,248 | 12,453 | 124,532 |
| Total MRR per AM | 321,197 | 357,689 | 339,856 | 3,398,559 |
| Q1 renewals per AM | 5 | 6 | 5.9 | 59 |
| Q2 renewals per AM | 1 | 7 | 6.1 | 61 |
| Q3 renewals per AM | 5 | 11 | 6.5 | 65 |
| Q4 renewals per AM | 7 | 11 | 8.8 | 88 |

The book becomes measurably tighter after rebalancing while preserving locked accounts. Account-count range drops from `5` to `1` (`80%` tighter), total-MRR range drops from `77,681` to `36,492` (`53%` tighter), and renewal concentration improves most in `Q1`, where the per-AM range drops from `8` to `1`.

## Logic

```mermaid
flowchart LR
    A[Paying SMB/MM accounts] --> B[Keep locked accounts fixed]
    B --> C[Score each AM assignment]
    C --> D[Choose lowest imbalance]
    D --> E[Export recommended owner changes]
```

Only paying SMB and Mid-Market accounts are included. Enterprise stays out of scope.

## Technical

- territory balancing, reassignment, and Salesforce writeback payload generation
- uses canonical `owner_id` with `owner_role = AM`
- preserves `must_keep_with_owner`
- exports:
  - `output/territory_summary_before.csv`
  - `output/territory_summary_after.csv`
  - `output/territory_balance_improvement_summary.csv`
  - `output/territory_reassignment_recommendations.csv`
  - `output/salesforce_update_payloads.csv`

Run:

```bash
python3 projects/02_territory_balancer/territory_balancer.py
```
