import { useMemo, useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { WorkflowPage } from './components/WorkflowPage'
import { workflows } from './data/workflows'

export default function App() {
  const [activeWorkflowId, setActiveWorkflowId] = useState(workflows[0].id)

  const activeWorkflow = useMemo(
    () => workflows.find((workflow) => workflow.id === activeWorkflowId) ?? workflows[0],
    [activeWorkflowId],
  )

  return (
    <div className="min-h-screen bg-[var(--color-bg)] px-0 py-0 text-[var(--color-ink)] lg:p-0">
      <div className="mx-auto min-h-screen max-w-[1440px] overflow-hidden border border-[var(--color-line)] bg-[var(--color-bg)] lg:flex lg:rounded-[18px]">
        <Sidebar
          workflows={workflows}
          activeWorkflowId={activeWorkflow.id}
          onSelectWorkflow={setActiveWorkflowId}
        />
        <main className="min-w-0 flex-1">
          <WorkflowPage workflow={activeWorkflow} />
        </main>
      </div>
    </div>
  )
}
