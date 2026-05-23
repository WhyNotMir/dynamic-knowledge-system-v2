import { WorkspaceScreen } from '@/components/workspace/WorkspaceScreen'
import { listSources } from '@/lib/api/sources'
import { listInboxItems } from '@/lib/api/inbox'
import { listArticles } from '@/lib/api/articles'

export const metadata = { title: 'Workspace' }

export default async function WorkspacePage({ params }: { params: { projectId: string } }) {
  const [sources, candidates, articles] = await Promise.all([
    listSources(params.projectId),
    listInboxItems(params.projectId),
    listArticles(params.projectId),
  ])
  const stats = {
    totalSources: sources.length,
    totalFragments: sources.reduce((sum, source) => sum + source.fragments, 0),
    pendingReview: candidates.filter(c => c.status === 'proposed').length,
    totalArticles: articles.length,
  }

  return (
    <WorkspaceScreen
      projectId={params.projectId}
      stats={stats}
      sources={sources.slice(0, 6)}
      candidates={candidates.filter(c => c.status === 'proposed').slice(0, 5)}
      activity={[]}
      todayLabel="Today"
    />
  )
}
