'use client'

import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import type { Project } from '@/lib/types'

interface AppShellProps {
  project: Project
  activeSection: string
  breadcrumbs?: { label: string; href?: string }[]
  children: React.ReactNode
}

export function AppShell({ project, activeSection, breadcrumbs, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <Sidebar project={project} activeSection={activeSection} />
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0, overflow: 'hidden' }}>
        <TopBar project={project} breadcrumbs={breadcrumbs} />
        <main
          className="scroll"
          style={{
            flex: 1,
            overflow: 'auto',
            minHeight: 0,
            position: 'relative',
            background: 'var(--paper)',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  )
}
