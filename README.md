# Andrew Heo - GTM Engineering Portfolio

## Problem Statement

GTM breaks when account ownership, product signals, and CRM data stop lining up.

## Output

| Project | Business Output | Why It Matters |
|---|---|---|
| `01_gtm_data_foundations` | One operating picture of the company | Every workflow runs off the same data |
| `02_territory_balancer` | Before vs after AM imbalance view | Shows where ownership can be rebalanced |
| `03_freetier_usage_alert` | AE-ready free-product signal | Turns usage into action |
| `04_lead_enrichment` | Matched and enriched lead outcome | Speeds up routing and follow-up |

## Logic

```mermaid
flowchart LR
    A[Shared GTM data] --> B[Territory balancing]
    A --> C[Free-tier usage alert]
    A --> D[Lead enrichment]
```

One shared dataset. Multiple revenue workflows.

## Technical

- Python
- pandas / numpy
- Salesforce-style object model
- Clay-style enrichment
- Slack-style alerts
- Datadog-style usage signals

Run order:

```bash
python3 -m pip install -r requirements.txt
python3 projects/01_gtm_data_foundations/generate_data.py
python3 projects/02_territory_balancer/territory_balancer.py
python3 projects/03_freetier_usage_alert/freetier_usage_alert.py
python3 projects/04_lead_enrichment/lead_enrichment.py --scenario all
```
