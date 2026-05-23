'use client'

import { usePathname } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import type { Project } from '@/lib/types'

function useActiveSection(projectId: string): string {
  const pathname = usePathname()
  if (pathname.includes('/sources')) return 'sources'
  if (pathname.includes('/inbox'))   return 'inbox'
  if (pathname.includes('/articles'))return 'articles'
  if (pathname.includes('/qa'))      return 'qa'
  return 'workspace'
}

function useBreadcrumbs(projectId: string, project: Project) {
  const pathname = usePathname()
  const crumbs: { label: string; href?: string }[] = []

  if (pathname.includes('/sources')) {
    const parts = pathname.split('/sources')
    if (parts[1] && parts[1].length > 1) {
      crumbs.push({ label: 'Sources', href: `/${projectId}/sources` })
      crumbs.push({ label: 'Source detail' })
    } else {
      crumbs.push({ label: 'Sources' })
    }
  } else if (pathname.includes('/inbox')) {
    crumbs.push({ label: 'Inbox' })
  } else if (pathname.includes('/articles')) {
    const parts = pathname.split('/articles')
    if (parts[1] && parts[1].length > 1) {
      crumbs.push({ label: 'Articles', href: `/${projectId}/articles` })
      crumbs.push({ label: 'Article' })
    } else {
      crumbs.push({ label: 'Articles' })
    }
  } else if (pathname.includes('/qa')) {
    crumbs.push({ label: 'Q & A' })
  } else {
    crumbs.push({ label: 'Workspace' })
  }

  return crumbs
}

export function ProjectShellClient({ project, children }: { project: Project; children: React.ReactNode }) {
  const section = useActiveSection(project.id)
  const crumbs  = useBreadcrumbs(project.id, project)
  return (
    <AppShell project={project} activeSection={section} breadcrumbs={crumbs}>
      {children}
    </AppShell>
  )
}
