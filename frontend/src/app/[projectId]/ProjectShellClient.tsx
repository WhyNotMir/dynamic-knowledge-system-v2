'use client'

import { usePathname } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { AppShell } from '@/components/shell/AppShell'
import type { Project } from '@/lib/types'
import { listArticles } from '@/lib/api/articles'
import { listInboxItems } from '@/lib/api/inbox'
import { listSources } from '@/lib/api/sources'

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
  const { data: sources } = useQuery({
    queryKey: ['sources', project.id],
    queryFn: () => listSources(project.id),
  })
  const { data: articles } = useQuery({
    queryKey: ['articles', project.id],
    queryFn: () => listArticles(project.id),
  })
  const { data: candidates } = useQuery({
    queryKey: ['inbox-items', project.id],
    queryFn: () => listInboxItems(project.id),
  })
  const hydratedProject: Project = {
    ...project,
    sources: sources?.length ?? project.sources,
    articles: articles?.length ?? project.articles,
    candidates: candidates?.filter(candidate => candidate.status === 'proposed').length ?? project.candidates,
  }
  return (
    <AppShell project={hydratedProject} activeSection={section} breadcrumbs={crumbs}>
      {children}
    </AppShell>
  )
}
