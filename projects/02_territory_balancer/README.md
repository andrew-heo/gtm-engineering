# Territory Balancer For AMs

## Problem Statement

SMB and Mid-Market books drift. Some AMs inherit too much revenue, too much complexity, or too many renewals in the same quarter. That creates uneven coverage.

## Output

- `output/territory_summary_before.csv`
- `output/territory_summary_after.csv`
- `output/territory_reassignment_recommendations.csv`
- `output/salesforce_update_payloads.csv`

What comes out:
- before/after owner book summaries
- account-level reassignment recommendations
- a dry-run Salesforce `OwnerId` update file

## Logic

```mermaid
flowchart LR
    A[Paying SMB/MM accounts] --> B[Keep locked accounts fixed]
    B --> C[Score each AM assignment]
    C --> D[Choose lowest imbalance]
    D --> E[Export recommended owner changes]
```

The script only touches paying SMB and Mid-Market accounts. Enterprise is out of scope here.

The balancing logic tries to make each AM book look closer to the overall customer base on:
- MRR
- product footprint
- ICP tier
- renewal mix by quarter

## Technical

- filters to paying accounts only
- filters to `SMB` and `Mid-Market` only
- treats canonical `owner_id` / `owner_role = AM` as the live book owner
- preserves `must_keep_with_owner`
- exports owner changes as Salesforce payloads

Run:

```bash
python3 projects/02_territory_balancer/territory_balancer.py
```
