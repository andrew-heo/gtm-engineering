import { mdxComponents } from './content/mdxComponents'

export function WorkflowPage({ workflow }) {
  const Content = workflow.Component

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--color-line)] px-8 py-9 md:px-12">
        <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-[13px] font-semibold uppercase tracking-[0.22em] text-[var(--color-muted)]">
              {workflow.stage}
            </p>
            <h2 className="mt-4 text-[46px] font-semibold leading-[1.02] tracking-[-0.05em] text-[var(--color-ink)] md:text-[64px]">
              {workflow.title}
            </h2>
            <p className="mt-4 max-w-4xl text-[24px] leading-[1.2] tracking-[-0.03em] text-[var(--color-copy)] md:text-[30px]">
              {workflow.subtitle}
            </p>
          </div>
          <div className="inline-flex rounded-[18px] bg-[var(--color-accent-bg)] px-5 py-4 text-[18px] font-medium text-[var(--color-accent-deep)]">
            {workflow.badge}
          </div>
        </div>
      </header>

      <div className="px-8 py-10 md:px-12 md:py-12">
        <div className="mx-auto max-w-[1120px]">
          <Content components={mdxComponents} />
        </div>
      </div>
    </div>
  )
}
