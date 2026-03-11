# Marketing Attribution And Funnel Model

## Introduction

Marketing attribution only becomes useful when the touch data is standardized, joined to the CRM cleanly, and applied consistently across the funnel.

## Output

This project represents a source-of-truth attribution workflow that models prospect activity from lead to opportunity and assigns both first-touch and last-touch credit at the opportunity level.

### Logic

The attribution logic is intentionally simple and explicit:

1. Each lead gets a normalized set of marketing touchpoints.
2. Touchpoints are joined from `lead_id` to `matched_account_id`.
3. Opportunities inherit eligible touches from leads associated to the same account.
4. **First-touch attribution** is the earliest eligible touch in the `365-day` window before opportunity creation.
5. **Last-touch attribution** is the latest eligible touch in the `90-day` window before opportunity creation.
6. Touches after opportunity creation do not get credit.
7. Opportunities missing a valid first-touch or last-touch get written to a hygiene exception file.

This keeps the model explainable: earliest pre-opportunity touch gets first-touch credit, latest meaningful pre-opportunity touch gets last-touch credit.

## Outputs

- `output/marketing_touchpoints.csv`
- `output/opportunity_attribution.csv`
- `output/attribution_summary.csv`
- `output/funnel_stage_summary.csv`
- `output/tracking_hygiene_exceptions.csv`

## Technical

- first-touch attribution at the opportunity level
- last-touch attribution at the opportunity level
- explicit `365-day` first-touch and `90-day` last-touch lookback windows
- funnel source-of-truth reporting for `lead -> opportunity -> customer`
- tracking hygiene exception handling for unattributed opportunities

Run:

```bash
python3 projects/06_marketing_attribution_and_funnel_model/marketing_attribution_and_funnel_model.py
```
