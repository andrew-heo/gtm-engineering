import { territoryBalanceVisual } from '../../data/territoryBalanceVisual'

function formatDelta(value) {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value}`
}

export function TerritoryBalanceViz() {
  const maxAccounts = Math.max(
    ...territoryBalanceVisual.before.map((item) => item.accounts),
    ...territoryBalanceVisual.after.map((item) => item.accounts),
  )

  return (
    <div className="rounded-[24px] border border-[var(--color-line-strong)] bg-[var(--color-panel)] p-6 md:p-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-[13px] font-semibold uppercase tracking-[0.22em] text-[var(--color-muted)]">
            What changed mathematically
          </p>
          <h3 className="mt-3 text-[32px] font-semibold tracking-[-0.04em] text-[var(--color-ink)]">
            Account load tightened from a 5-account spread to 1.
          </h3>
        </div>
        <div className="grid grid-cols-2 gap-3 md:w-[330px]">
          {territoryBalanceVisual.summary.map((item) => (
            <div
              key={item.label}
              className="rounded-[16px] border border-[var(--color-line)] bg-white px-4 py-3"
            >
              <p className="text-[12px] uppercase tracking-[0.18em] text-[var(--color-muted)]">
                {item.label}
              </p>
              <p className="mt-2 text-[24px] font-semibold tracking-[-0.04em] text-[var(--color-ink)]">
                {item.value}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        {[
          { label: 'Before rebalance', rows: territoryBalanceVisual.before },
          { label: 'After rebalance', rows: territoryBalanceVisual.after },
        ].map((group) => (
          <div key={group.label} className="rounded-[20px] border border-[var(--color-line)] bg-white p-5">
            <div className="flex items-center justify-between">
              <p className="text-[18px] font-medium text-[var(--color-ink)]">{group.label}</p>
              <p className="text-sm text-[var(--color-subtle)]">Accounts per AM</p>
            </div>
            <div className="mt-5 space-y-3">
              {group.rows.map((row) => (
                <div key={row.owner} className="grid grid-cols-[64px_minmax(0,1fr)_58px] items-center gap-3">
                  <span className="font-mono text-[13px] text-[var(--color-subtle)]">{row.owner}</span>
                  <div className="h-8 overflow-hidden rounded-full bg-[var(--color-bg)]">
                    <div
                      className={`flex h-full items-center rounded-full px-3 text-sm font-medium ${
                        group.label === 'Before rebalance'
                          ? 'bg-[var(--color-ink)] text-white'
                          : 'bg-[var(--color-accent)] text-white'
                      }`}
                      style={{ width: `${(row.accounts / maxAccounts) * 100}%` }}
                    >
                      {row.accounts}
                    </div>
                  </div>
                  <span
                    className={`text-sm font-medium ${
                      row.delta < 0
                        ? 'text-[var(--color-accent-deep)]'
                        : row.delta > 0
                          ? 'text-[var(--color-warm)]'
                          : 'text-[var(--color-subtle)]'
                    }`}
                  >
                    {formatDelta(row.delta)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
