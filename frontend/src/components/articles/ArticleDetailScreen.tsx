'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getArticle } from '@/lib/api/articles'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { TopicTreePanel } from './TopicTreePanel'
import { ArticleOutline } from './ArticleOutline'
import { ArticleBody } from './ArticleBody'

interface Props { projectId: string; articleId: string }

export function ArticleDetailScreen({ projectId, articleId }: Props) {
  const [activeOutline, setActiveOutline] = useState<string>('ov')

  const { data: article, isLoading, error, refetch } = useQuery({
    queryKey: ['article', projectId, articleId],
    queryFn: () => getArticle(projectId, articleId),
  })

  if (isLoading) return (
    <div style={{ display: 'grid', gridTemplateColumns: '256px 1fr 244px', height: '100%' }}>
      <div style={{ borderRight: '1px solid var(--rule)', background: 'var(--paper-2)' }} />
      <div style={{ padding: '80px 56px' }}><LoadingState /></div>
      <div style={{ borderLeft: '1px solid var(--rule)' }} />
    </div>
  )

  if (error || !article) return (
    <div style={{ padding: '24px 32px' }}>
      <ErrorState onRetry={() => refetch()} />
    </div>
  )

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '256px minmax(0, 1fr) 244px', height: '100%', minHeight: 0 }}>
      {/* Left: topic tree */}
      <TopicTreePanel
        projectId={projectId}
        articleId={articleId}
        nodes={[]}
      />

      {/* Center: article body */}
      <ArticleBody
        article={article}
        onOutlineChange={setActiveOutline}
      />

      {/* Right: outline */}
      <ArticleOutline
        outline={article.outline}
        activeId={activeOutline}
        onSelect={id => {
          setActiveOutline(id)
          const el = document.getElementById(`anchor-${id}`)
          el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }}
        sourceRefs={article.sourceRefs}
        relatedArticles={article.relatedArticles}
        projectId={projectId}
      />
    </div>
  )
}
