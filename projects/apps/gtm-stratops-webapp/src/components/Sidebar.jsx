export function Sidebar({ siteCopy, workflows, activeWorkflowId, onSelectWorkflow }) {
  return (
    <aside className="border-b border-[var(--color-line)] lg:w-[438px] lg:shrink-0 lg:border-b-0 lg:border-r">
      <div className="flex h-full min-h-[320px] flex-col">
        <div className="border-b border-[var(--color-line)] px-8 py-10">
          <h1 className="text-[28px] font-semibold leading-none text-[var(--color-ink)]">{siteCopy.title}</h1>
          <p className="mt-3 text-[19px] leading-none text-[var(--color-ink)]">{siteCopy.author}</p>
        </div>

        <div className="flex-1 px-8 py-6">
          <p className="text-[18px] uppercase tracking-[0.08em] text-[var(--color-muted)]">
            {siteCopy.workflowsLabel}
          </p>
          <nav className="mt-4 space-y-2">
            {workflows.map((workflow) => {
              const isActive = workflow.id === activeWorkflowId

              return (
                <button
                  key={workflow.id}
                  type="button"
                  onClick={() => onSelectWorkflow(workflow.id)}
                  className={`flex w-full items-center gap-4 rounded-[18px] px-5 py-4 text-left transition ${
                    isActive
                      ? 'border border-[var(--color-line-strong)] bg-white'
                      : 'border border-transparent hover:border-[var(--color-line)] hover:bg-white/50'
                  }`}
                >
                  <span
                    className={`h-3 w-3 shrink-0 rounded-full ${
                      isActive ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-dot)]'
                    }`}
                  />
                  <span className="flex-1 text-[20px] leading-[1.2] text-[var(--color-copy)]">
                    {workflow.title}
                  </span>
                  {siteCopy.statusLabels[workflow.status] ? (
                    <span className="text-sm text-[var(--color-subtle)]">
                      {siteCopy.statusLabels[workflow.status]}
                    </span>
                  ) : null}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="border-t border-[var(--color-line)] px-8 py-8">
          <div className="flex items-center gap-4 text-[18px] text-[var(--color-copy)]">
            <span className="h-3 w-3 rounded-full bg-[var(--color-dot)]" />
            <span>{siteCopy.aboutLabel}</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
