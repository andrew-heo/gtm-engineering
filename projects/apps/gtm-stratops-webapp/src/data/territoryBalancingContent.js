export const territoryMeta = {
  title: 'Territory balancing',
  subtitle: 'How to stop territories from drifting and killing quota attainment',
  badge: 'AI-assisted',
  stage: 'Live workflow',
}

export const heroMetrics = [
  {
    label: 'Managed customer base',
    value: '10K+',
    detail: 'Quarterly account ownership decisions were evaluated globally instead of rep by rep.',
  },
  {
    label: 'Managed MRR impact',
    value: '+20%',
    detail: 'Proactively managed MRR increased after low-value ownership drift was corrected.',
  },
  {
    label: 'Planning speed',
    value: 'Minutes',
    detail: 'The workflow replaced spreadsheet cleanup with a repeatable rebalance motion.',
  },
]

export const workflowSteps = [
  { step: '01', title: 'Define constraints', description: 'Revenue thresholds, language matching, and rep capacity ceilings.' },
  { step: '02', title: 'AI groups accounts', description: 'AI surfaces the cleanest move candidates from a pre-qualified set.', active: true },
  { step: '03', title: 'Score + assign', description: 'Rules validate every move before writeback into operational systems.' },
  { step: '04', title: 'Weekly review', description: 'A drift review closes the loop before imbalance compounds into quarter-end pain.' },
]

export const sampleRows = [
  {
    account: 'Acme Logistics',
    from: 'West SMB Pod A',
    to: 'Central SMB Pod B',
    reason: 'Moves a low-MRR account to an under-capacity rep without breaking language coverage.',
  },
  {
    account: 'Nordlicht GmbH',
    from: 'EMEA MM Pod C',
    to: 'EMEA MM Pod F',
    reason: 'Preserves German-language support while reducing renewal concentration on the current book.',
  },
  {
    account: 'Pixel Harbor',
    from: 'APJ SMB Pod D',
    to: 'APJ SMB Pod A',
    reason: 'Keeps the account in-segment and opens room on an overloaded owner book.',
  },
]

export const impactCards = [
  {
    label: 'Account-count variance',
    value: '-80%',
    detail: 'The spread across books shrank from 5 accounts to 1, which made workload more predictable.',
  },
  {
    label: 'Total MRR range',
    value: '-53%',
    detail: 'MRR distribution by owner compressed materially, improving fairness without flattening every account.',
  },
  {
    label: 'Q1 renewal skew',
    value: '-88%',
    detail: 'The highest-risk renewal quarter became materially more balanced across the AM team.',
  },
]

export const territoryPrompt = `Given {account_list} with {arr}, {segment}, {language_req}, and {current_owner},
group accounts into balanced territory recommendations that respect:

1. revenue thresholds for proactive coverage
2. rep capacity ceilings by owner
3. language-to-owner compatibility
4. minimal disruption to current ownership

Return:
- grouped accounts by recommended owner
- rationale for each move
- risk flags requiring manager review
- expected balance improvement by account count and MRR`
