# Territory Balancing Algorithm

## Problem

Sales territories often become uneven over time as accounts close, expand, churn, or get reassigned manually. This creates unfair books across reps and makes coverage, planning, and performance comparisons less reliable.

## Solution

I built a territory balancing approach that reallocates accounts across reps to reduce imbalance in book value while preserving practical assignment constraints.

## What the model does

The algorithm takes a set of accounts and rep assignments, measures how imbalanced the books are, and recommends reassignment scenarios that bring each rep closer to a target level of coverage.

## Inputs

- Account-level territory data
- Current rep assignments
- Book value metric (ARR, potential ARR, or weighted score)
- Optional assignment constraints

## Outputs

- Recommended account reassignments
- Before vs. after balance by rep
- Summary of territory variance reduction
- Exportable reassignment table for review

## Tools

- Python
- Pandas
- NumPy
- CSV / spreadsheet exports

## Why it matters

Balanced territories improve planning quality, reduce rep frustration, and create a more reliable basis for forecasting and performance management.

## Next steps

Future versions can add:
- geographic constraints
- segment constraints
- account relationship rules
- optimization-based assignment logic
