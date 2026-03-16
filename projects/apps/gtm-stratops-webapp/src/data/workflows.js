import FreeTierAlertsPage, { meta as freeTierMeta } from '../content/workflows/free-tier-alerts.mdx'
import LeadEnrichmentPage, { meta as leadEnrichmentMeta } from '../content/workflows/lead-enrichment.mdx'
import TerritoryBalancingPage from '../content/workflows/territory-balancing.mdx'
import { territoryMeta } from './territoryBalancingContent'

export const workflows = [
  {
    id: 'territory-balancing',
    status: 'live',
    title: territoryMeta.title,
    subtitle: territoryMeta.subtitle,
    badge: territoryMeta.badge,
    stage: territoryMeta.stage,
    Component: TerritoryBalancingPage,
  },
  {
    id: 'free-tier-alerts',
    status: 'next',
    title: freeTierMeta.title,
    subtitle: freeTierMeta.subtitle,
    badge: freeTierMeta.badge,
    stage: freeTierMeta.stage,
    Component: FreeTierAlertsPage,
  },
  {
    id: 'lead-enrichment',
    status: 'backlog',
    title: leadEnrichmentMeta.title,
    subtitle: leadEnrichmentMeta.subtitle,
    badge: leadEnrichmentMeta.badge,
    stage: leadEnrichmentMeta.stage,
    Component: LeadEnrichmentPage,
  },
]
