function SectionLabel({ children }) {
  return (
    <p className="text-[18px] uppercase tracking-[0.06em] text-[var(--color-muted)]">{children}</p>
  )
}

function StepCard({ step }) {
  return (
    <article
      className={`rounded-[18px] border p-6 ${
        step.active
          ? 'border-[var(--color-accent-soft)] bg-[var(--color-accent-bg)]'
          : 'border-[var(--color-line-strong)] bg-white'
      }`}
    >
      <p className="text-[18px] leading-none text-[var(--color-subtle)]">{step.step}</p>
      <h3
        className={`mt-3 text-[23px] font-medium leading-[1.15] ${
          step.active ? 'text-[var(--color-accent-deep)]' : 'text-[var(--color-ink)]'
        }`}
      >
        {step.title}
      </h3>
      <p className="mt-4 text-[18px] leading-[1.45] text-[var(--color-copy)]">{step.description}</p>
    </article>
  )
}

function MetricCard({ metric }) {
  return (
    <div className="rounded-[18px] border border-[var(--color-line-strong)] bg-white px-5 py-4">
      <div className="flex items-end justify-between gap-4">
        <p className="text-[18px] text-[var(--color-copy)]">{metric.label}</p>
        <p className="text-[26px] font-semibold text-[var(--color-ink)]">{metric.value}</p>
      </div>
      <p className="mt-3 text-[16px] leading-[1.5] text-[var(--color-subtle)]">{metric.detail}</p>
    </div>
  )
}

export function WorkflowPage({ workflow }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--color-line)] px-8 py-8 md:px-12">
        <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
          <div>
            <h2 className="text-[42px] font-semibold leading-[1.02] tracking-[-0.04em] text-[var(--color-ink)] md:text-[56px]">
              {workflow.title}
            </h2>
            <p className="mt-4 max-w-4xl text-[24px] leading-[1.2] tracking-[-0.03em] text-[var(--color-copy)] md:text-[28px]">
              {workflow.subtitle}
            </p>
          </div>
          <div className="inline-flex rounded-[18px] bg-[var(--color-accent-bg)] px-5 py-4 text-[18px] font-medium text-[var(--color-accent-deep)]">
            {workflow.badge}
          </div>
        </div>
      </header>

      <div className="space-y-12 px-8 py-10 md:px-12">
        <section>
          <SectionLabel>THE PROBLEM</SectionLabel>
          <div className="mt-4 rounded-[22px] border border-[var(--color-line-strong)] bg-[var(--color-panel)] px-8 py-7">
            <p className="max-w-5xl text-[22px] leading-[1.6] tracking-[-0.03em] text-[var(--color-ink)] md:text-[29px]">
              {workflow.problemLead}
            </p>
          </div>
        </section>

        <section>
          <SectionLabel>HOW AI FITS IN</SectionLabel>
          <div className="mt-4 grid gap-4 xl:grid-cols-4">
            {workflow.aiSteps.map((step) => (
              <StepCard key={step.step} step={step} />
            ))}
          </div>
        </section>

        <section>
          <SectionLabel>PROMPT STRUCTURE</SectionLabel>
          <div className="mt-4 overflow-hidden rounded-[22px] border border-[var(--color-line-strong)] bg-white">
            <div className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-panel)] px-7 py-4">
              <p className="text-[18px] text-[var(--color-copy)]">{workflow.promptFileName}</p>
              <button type="button" className="text-[18px] text-[var(--color-copy)]">
                copy
              </button>
            </div>
            <div className="px-7 py-7">
              <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-[17px] leading-[1.6] text-[var(--color-ink)]">
                {workflow.promptStructure}
              </pre>
            </div>
          </div>
        </section>

        <section className="grid gap-8 xl:grid-cols-[minmax(0,1.15fr)_360px]">
          <div>
            <SectionLabel>SAMPLE OUTPUTS</SectionLabel>
            <div className="mt-4 overflow-hidden rounded-[22px] border border-[var(--color-line-strong)] bg-white">
              <table className="min-w-full text-left">
                <thead className="border-b border-[var(--color-line)] bg-[var(--color-panel)]">
                  <tr className="text-[14px] uppercase tracking-[0.06em] text-[var(--color-muted)]">
                    <th className="px-6 py-4 font-medium">Account</th>
                    <th className="px-6 py-4 font-medium">Current owner</th>
                    <th className="px-6 py-4 font-medium">Recommended owner</th>
                    <th className="px-6 py-4 font-medium">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {workflow.sampleOutputs.reassignments.map((row) => (
                    <tr key={row.account} className="border-b border-[var(--color-line)] last:border-b-0">
                      <td className="px-6 py-5 text-[17px] font-medium text-[var(--color-ink)]">
                        {row.account}
                      </td>
                      <td className="px-6 py-5 text-[17px] text-[var(--color-copy)]">{row.from}</td>
                      <td className="px-6 py-5 text-[17px] text-[var(--color-copy)]">{row.to}</td>
                      <td className="px-6 py-5 text-[17px] leading-[1.5] text-[var(--color-copy)]">
                        {row.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <SectionLabel>OUTPUT METRICS</SectionLabel>
            <div className="mt-4 space-y-4">
              {workflow.sampleOutputs.metrics.map((metric) => (
                <MetricCard key={metric.label} metric={metric} />
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
