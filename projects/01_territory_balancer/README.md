# Territory Balancing Algorithm

## Problem

Customer Success territories naturally drift out of balance over time. As accounts expand, churn, or change ownership, some CSMs end up managing:

- significantly more revenue
- more complex product footprints
- uneven renewal workloads

Manual rebalancing across multiple dimensions is difficult, especially when trying to simultaneously balance:

- account revenue
- product complexity
- ICP quality
- renewal timing

This project builds an algorithm that redistributes accounts across CSMs to create more balanced books.

---

# Dataset

Each account contains the following attributes:

| Field | Description |
|------|-------------|
| account_id | unique account identifier |
| Renewal Quarter | renewal timing (Q1–Q4) |
| Account MRR | monthly recurring revenue |
| Number of products used | product footprint complexity |
| ICP Tier | 1–5 tier representing ICP quality |
| Current owner | assigned CSM |
| Must keep with current owner | reassignment constraint |

Synthetic data is generated with:

- **300 accounts**
- **10 CSMs**
- **30 accounts per CSM**

---

# Optimization Objective

The model minimizes the difference between each CSM’s book and the overall population of accounts.

Specifically, it minimizes the **sum of Euclidean distances between:**

- average account MRR per CSM
- average number of products per CSM
- average ICP tier per CSM

and the **population averages** of those same metrics.

This ensures each CSM manages a book structurally similar to the overall customer population.

---

# Additional Constraints

### Fixed accounts

Accounts marked **Must keep with current owner** cannot be reassigned.

### Renewal distribution

Each CSM can only receive a limited number of accounts per renewal quarter.

The cap is calculated as:

max accounts per rep per quarter =
ceil(total accounts in quarter / number of CSMs)


This prevents renewal concentration within a single territory.

---

# Optimization Process

1. Generate the synthetic dataset
2. Calculate population averages
3. Assign accounts sequentially
4. For each account:
   - test assignment to every eligible CSM
   - calculate resulting territory balance
   - select the assignment that minimizes imbalance
5. Repeat the process multiple times with randomized account order
6. select the best resulting territory configuration

---

# Original Territory State

Before rebalancing:

| CSM | Avg MRR | Avg Products | Avg ICP | Q1 | Q2 | Q3 | Q4 |
|----|----|----|----|----|----|----|----|
| CSM_1 | 5825 | 3.20 | 4.17 | 11 | 6 | 8 | 5 |
| CSM_10 | 2625 | 2.20 | 3.17 | 8 | 6 | 7 | 9 |
| CSM_2 | 2740 | 2.17 | 2.80 | 7 | 6 | 12 | 5 |
| CSM_3 | 3152 | 2.40 | 3.30 | 7 | 8 | 4 | 11 |
| CSM_4 | 2917 | 2.67 | 3.37 | 11 | 9 | 5 | 5 |
| CSM_5 | 2941 | 2.47 | 3.43 | 5 | 6 | 7 | 12 |
| CSM_6 | 2954 | 2.50 | 3.37 | 11 | 10 | 5 | 4 |
| CSM_7 | 3115 | 2.30 | 3.10 | 4 | 6 | 9 | 11 |
| CSM_8 | 3604 | 2.80 | 3.53 | 6 | 10 | 7 | 7 |
| CSM_9 | 3561 | 2.30 | 3.37 | 5 | 8 | 7 | 10 |

Example problems:

- CSM_1 manages a much higher revenue book
- some reps carry 11–12 renewals in a single quarter
- ICP quality varies significantly across territories

---

# Optimized Territory State

After running the territory balancing algorithm:

| CSM | Avg MRR | Avg Products | Avg ICP | Q1 | Q2 | Q3 | Q4 |
|----|----|----|----|----|----|----|----|
| CSM_1 | 3413 | 2.50 | 3.27 | 7 | 7 | 8 | 8 |
| CSM_10 | 3185 | 2.40 | 3.30 | 7 | 8 | 7 | 8 |
| CSM_2 | 3492 | 2.57 | 3.50 | 8 | 8 | 6 | 8 |
| CSM_3 | 3161 | 2.47 | 3.30 | 8 | 6 | 8 | 8 |
| CSM_4 | 3297 | 2.53 | 3.37 | 8 | 8 | 6 | 8 |
| CSM_5 | 3372 | 2.53 | 3.37 | 8 | 6 | 8 | 8 |
| CSM_6 | 3495 | 2.50 | 3.33 | 8 | 6 | 8 | 8 |
| CSM_7 | 3260 | 2.47 | 3.53 | 8 | 10 | 5 | 7 |
| CSM_8 | 3397 | 2.53 | 3.30 | 6 | 8 | 8 | 8 |
| CSM_9 | 3357 | 2.50 | 3.33 | 7 | 8 | 7 | 8 |

Results:

- average revenue per territory converges
- product complexity becomes more consistent across books
- ICP quality becomes more evenly distributed
- renewal workload becomes significantly more balanced

---

# Files
territory_balancer.py

Main script that:

- generates the dataset
- performs territory rebalancing
- prints before and after statistics
- exports results for analysis
