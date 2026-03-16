export function SectionEyebrow({ children }) {
  return (
    <p className="text-[13px] font-semibold uppercase tracking-[0.22em] text-[var(--color-muted)]">
      {children}
    </p>
  )
}

export function StoryCard({ children, tone = 'default' }) {
  const toneClass =
    tone === 'accent'
      ? 'border-[var(--color-accent-soft)] bg-[var(--color-accent-bg)]'
      : 'border-[var(--color-line-strong)] bg-white'

  return <div className={`rounded-[24px] border p-6 md:p-8 ${toneClass}`}>{children}</div>
}

export function MetricBand({ items }) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-[20px] border border-[var(--color-line-strong)] bg-white px-5 py-5"
        >
          <p className="text-sm uppercase tracking-[0.14em] text-[var(--color-muted)]">{item.label}</p>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-[var(--color-ink)]">
            {item.value}
          </p>
          <p className="mt-3 text-[15px] leading-7 text-[var(--color-copy)]">{item.detail}</p>
        </div>
      ))}
    </div>
  )
}

export function WorkflowSteps({ steps }) {
  return (
    <div className="grid gap-4 xl:grid-cols-4">
      {steps.map((step) => (
        <article
          key={step.step}
          className={`rounded-[20px] border p-6 ${
            step.active
              ? 'border-[var(--color-accent-soft)] bg-[var(--color-accent-bg)]'
              : 'border-[var(--color-line-strong)] bg-white'
          }`}
        >
          <p className="text-base text-[var(--color-subtle)]">{step.step}</p>
          <h3
            className={`mt-3 text-[25px] font-medium leading-[1.1] tracking-[-0.03em] ${
              step.active ? 'text-[var(--color-accent-deep)]' : 'text-[var(--color-ink)]'
            }`}
          >
            {step.title}
          </h3>
          <p className="mt-4 text-[17px] leading-8 text-[var(--color-copy)]">{step.description}</p>
        </article>
      ))}
    </div>
  )
}

export function PromptPanel({ fileName, prompt }) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-[var(--color-line-strong)] bg-white">
      <div className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-panel)] px-6 py-4">
        <p className="text-[17px] text-[var(--color-copy)]">{fileName}</p>
        <span className="text-[16px] text-[var(--color-subtle)]">structured prompt</span>
      </div>
      <pre className="overflow-x-auto whitespace-pre-wrap px-6 py-6 font-mono text-[15px] leading-7 text-[var(--color-ink)]">
        {prompt}
      </pre>
    </div>
  )
}

export function OutputTable({ rows }) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-[var(--color-line-strong)] bg-white">
      <table className="min-w-full text-left">
        <thead className="border-b border-[var(--color-line)] bg-[var(--color-panel)]">
          <tr className="text-[13px] uppercase tracking-[0.18em] text-[var(--color-muted)]">
            <th className="px-5 py-4 font-medium">Account</th>
            <th className="px-5 py-4 font-medium">From</th>
            <th className="px-5 py-4 font-medium">To</th>
            <th className="px-5 py-4 font-medium">Reason</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.account} className="border-b border-[var(--color-line)] last:border-b-0">
              <td className="px-5 py-5 text-[16px] font-medium text-[var(--color-ink)]">{row.account}</td>
              <td className="px-5 py-5 text-[16px] text-[var(--color-copy)]">{row.from}</td>
              <td className="px-5 py-5 text-[16px] text-[var(--color-copy)]">{row.to}</td>
              <td className="px-5 py-5 text-[16px] leading-7 text-[var(--color-copy)]">{row.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function InsightList({ items }) {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-[18px] border border-[var(--color-line-strong)] bg-white px-5 py-4"
        >
          <div className="flex items-end justify-between gap-4">
            <p className="text-[17px] text-[var(--color-copy)]">{item.label}</p>
            <p className="text-[26px] font-semibold tracking-[-0.04em] text-[var(--color-ink)]">
              {item.value}
            </p>
          </div>
          <p className="mt-3 text-[15px] leading-7 text-[var(--color-subtle)]">{item.detail}</p>
        </div>
      ))}
    </div>
  )
}
