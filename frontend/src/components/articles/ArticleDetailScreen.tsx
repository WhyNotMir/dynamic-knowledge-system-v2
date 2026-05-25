'use client'

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getArticle } from '@/lib/api/articles'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { ArticleContextPanel } from './ArticleContextPanel'
import { ArticleOutline } from './ArticleOutline'
import { ArticleBody } from './ArticleBody'

interface Props { projectId: string; articleId: string }

export function ArticleDetailScreen({ projectId, articleId }: Props) {
  const [activeOutline, setActiveOutline] = useState<string>('ov')
  const [contextOpen, setContextOpen] = useState(true)

  const { data: article, isLoading, error, refetch } = useQuery({
    queryKey: ['article', projectId, articleId],
    queryFn: () => getArticle(projectId, articleId),
  })

  useEffect(() => {
    if (article?.outline[0]) setActiveOutline(article.outline[0].id)
  }, [article?.id, article?.outline])

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
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `${contextOpen ? '286px' : '32px'} minmax(0, 1fr) 244px`,
        height: '100%',
        minHeight: 0,
        transition: 'grid-template-columns 0.18s ease',
      }}
    >
      {/* Left: article context. The global topic tree lives in the app sidebar. */}
      {contextOpen ? (
        <ArticleContextPanel article={article} onCollapse={() => setContextOpen(false)} />
      ) : (
        <button
          type="button"
          onClick={() => setContextOpen(true)}
          title="Show article context"
          style={{
            height: '100%',
            border: 0,
            borderRight: '1px solid var(--rule)',
            background: 'var(--paper-2)',
            color: 'var(--slate)',
            cursor: 'pointer',
            writingMode: 'vertical-rl',
            textOrientation: 'mixed',
            fontSize: '10.5px',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            fontFamily: 'var(--f-mono)',
          }}
        >
          Context
        </button>
      )}

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
