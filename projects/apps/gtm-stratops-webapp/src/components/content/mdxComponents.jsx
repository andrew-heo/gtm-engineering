import {
  InsightList,
  MetricBand,
  OutputTable,
  PromptPanel,
  SectionEyebrow,
  StoryCard,
  WorkflowSteps,
} from './ContentBlocks'
import { TerritoryBalanceViz } from './TerritoryBalanceViz'

export const mdxComponents = {
  h2: (props) => (
    <h2
      className="mt-14 text-[13px] font-semibold uppercase tracking-[0.22em] text-[var(--color-muted)]"
      {...props}
    />
  ),
  h3: (props) => (
    <h3 className="mt-5 text-[32px] font-semibold tracking-[-0.04em] text-[var(--color-ink)]" {...props} />
  ),
  p: (props) => <p className="mt-4 max-w-4xl text-[19px] leading-9 text-[var(--color-copy)]" {...props} />,
  ul: (props) => <ul className="mt-5 space-y-3 pl-6 text-[18px] leading-8 text-[var(--color-copy)]" {...props} />,
  li: (props) => <li className="pl-1" {...props} />,
  strong: (props) => <strong className="font-semibold text-[var(--color-ink)]" {...props} />,
  SectionEyebrow,
  StoryCard,
  MetricBand,
  WorkflowSteps,
  PromptPanel,
  TerritoryBalanceViz,
  OutputTable,
  InsightList,
}
