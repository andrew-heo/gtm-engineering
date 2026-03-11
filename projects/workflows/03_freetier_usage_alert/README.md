# Free-Tier Usage Alert For AEs

## Introduction

Product usage signals are most valuable when they can be activated through the external tools GTM teams use every day.

## Output

This project represents a product-signal workflow on top of the shared GTM data layer, turning free-tier usage into AE-ready Slack alerts and Salesforce task payloads.

```text
Top free-tier usage accounts: 2026-03-05 to 2026-03-11
1. Free Freeworkspace099 | owner=AE_5 | owner_role=AE | events=7 | users=4 | top user=user2@freeworkspace099.com (43%)
2. Free Freeworkspace186 | owner=AE_8 | owner_role=AE | events=7 | users=4 | top user=user1@freeworkspace186.com (43%)
3. Free Freeworkspace002 | owner=AE_4 | owner_role=AE | events=7 | users=3 | top user=user3@freeworkspace002.com (43%)
4. Free Freeworkspace003 | owner=AE_7 | owner_role=AE | events=7 | users=3 | top user=user4@freeworkspace003.com (71%)
5. Free Freeworkspace175 | owner=AE_8 | owner_role=AE | events=6 | users=4 | top user=user2@freeworkspace175.com (33%)
```

The output is simple: who is active, who owns it, who the most engaged user is, and what follow-up actions should be created.

## Logic

```mermaid
flowchart LR
    A[Free-product usage events] --> B[Match to free accounts]
    B --> C[Rank by activity]
    C --> D[Identify top user]
    D --> E[Route to AE owner]
```

Free-product accounts resolve to AEs through canonical ownership.

## Technical

- usage signal detection, Slack alerting, and Salesforce task creation
- 7-day lookback
- free-product accounts only
- ranks by total events and active users
- exports:
  - `output/free_tier_usage_alerts.csv`
  - `output/slack_message_payload.csv`
  - `output/salesforce_tasks.csv`

Run:

```bash
python3 projects/workflows/03_freetier_usage_alert/freetier_usage_alert.py
```
