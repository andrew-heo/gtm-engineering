# Territory Balancer For AMs

## Problem Statement

Some AMs end up carrying too much revenue, too much complexity, or too many renewals at once.

## Output

This project produces reassignment recommendations and Salesforce update payloads to rebalance AM books.

### Before State

| Metric | Low | High |
|---|---:|---:|
| Accounts per AM | 10 | 46 |
| Avg MRR per AM | 1,445 | 3,581 |
| Avg products per AM | 1.2 | 3.3 |
| Avg ICP per AM | 1.2 | 3.1 |

### After State

| Metric | Low | High |
|---|---:|---:|
| Accounts per AM | 10 | 46 |
| Avg MRR per AM | 2,510 | 3,125 |
| Avg products per AM | 2.3 | 3.1 |
| Avg ICP per AM | 2.1 | 3.0 |

The book becomes materially tighter after rebalancing, especially on revenue and product complexity, while preserving locked accounts.

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
  - `output/territory_reassignment_recommendations.csv`
  - `output/salesforce_update_payloads.csv`

Run:

```bash
python3 projects/02_territory_balancer/territory_balancer.py
```
