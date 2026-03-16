export const workflows = [
  {
    id: 'territory-balancing',
    status: 'live',
    title: 'Territory balancing',
    subtitle: 'How to stop territories from drifting and killing quota attainment',
    badge: 'AI-assisted',
    problemLead:
      'At scale, territories drift. Reps leave, accounts grow, new logos land in the wrong segment. Without a systematic rebalance, some AEs carry 2x the workload of others and your forecast accuracy tanks because coverage is uneven, not because the market changed.',
    aiSteps: [
      {
        step: '01',
        title: 'Define constraints',
        description: 'Revenue thresholds, language match, rep capacity',
      },
      {
        step: '02',
        title: 'AI groups accounts',
        description: 'Hypothesis grouping by workflow, segment, signals',
        active: true,
      },
      {
        step: '03',
        title: 'Score + assign',
        description: 'Balance load, write back to Salesforce',
      },
      {
        step: '04',
        title: 'Weekly review',
        description: 'Drift report surfaces imbalances before they compound',
      },
    ],
    promptFileName: 'territory_balancer_prompt.txt',
    promptStructure: `Given {account_list} with {arr}, {segment},
and {language_req}, group accounts into balanced
territory buckets that respect:

1. revenue thresholds for proactive coverage
2. rep capacity ceilings
3. language-to-owner compatibility
4. minimal disruption to current ownership

Return:
- grouped accounts by recommended owner
- rationale for each move
- risk flags where a move should be reviewed
- summary of expected balance improvement`,
    sampleOutputs: {
      reassignments: [
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
          reason: 'Preserves German-language support while reducing Q3 renewal concentration on the current book.',
        },
        {
          account: 'Pixel Harbor',
          from: 'APJ SMB Pod D',
          to: 'APJ SMB Pod A',
          reason: 'Keeps the account in-segment and opens room on an overloaded owner book.',
        },
      ],
      metrics: [
        {
          label: 'Proactively managed MRR',
          value: '+20% QoQ',
          detail: 'More revenue landed on books with real capacity for proactive management.',
        },
        {
          label: 'Customer base',
          value: '10K+',
          detail: 'Global customers reviewed in the quarterly balancing cycle.',
        },
        {
          label: 'Decision speed',
          value: 'Minutes',
          detail: 'Recommendations replaced manual spreadsheet triage.',
        },
      ],
    },
  },
  {
    id: 'freetier-alerts',
    status: 'next',
    title: 'Free tier alerts',
    subtitle: 'Which free users are signaling sales-ready intent',
    badge: 'Queued',
    problemLead: 'This page is the next workflow to build.',
    aiSteps: [],
    promptFileName: 'usage_alert_prompt.txt',
    promptStructure: 'Next workflow page not built yet.',
    sampleOutputs: { reassignments: [], metrics: [] },
  },
  {
    id: 'lead-enrichment',
    status: 'backlog',
    title: 'Lead enrichment',
    subtitle: 'How to standardize bad inbound data before it hits routing',
    badge: 'Planned',
    problemLead: 'This page is reserved for a later workflow.',
    aiSteps: [],
    promptFileName: 'lead_enrichment_prompt.txt',
    promptStructure: 'Reserved.',
    sampleOutputs: { reassignments: [], metrics: [] },
  },
  {
    id: 'renewal-automation',
    status: 'backlog',
    title: 'Renewal automation',
    subtitle: 'How renewal intake gets validated and routed without spreadsheet cleanup',
    badge: 'Planned',
    problemLead: 'This page is reserved for a later workflow.',
    aiSteps: [],
    promptFileName: 'renewal_prompt.txt',
    promptStructure: 'Reserved.',
    sampleOutputs: { reassignments: [], metrics: [] },
  },
  {
    id: 'marketing-attribution',
    status: 'backlog',
    title: 'Marketing attribution',
    subtitle: 'How to build a source of truth for funnel influence',
    badge: 'Planned',
    problemLead: 'This page is reserved for a later workflow.',
    aiSteps: [],
    promptFileName: 'marketing_attribution_prompt.txt',
    promptStructure: 'Reserved.',
    sampleOutputs: { reassignments: [], metrics: [] },
  },
  {
    id: 'growth-experiments',
    status: 'backlog',
    title: 'Growth experiments',
    subtitle: 'How to connect segmentation, hypotheses, and measurable GTM learning',
    badge: 'Planned',
    problemLead: 'This page is reserved for a later workflow.',
    aiSteps: [],
    promptFileName: 'growth_experiment_prompt.txt',
    promptStructure: 'Reserved.',
    sampleOutputs: { reassignments: [], metrics: [] },
  },
]
