'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { BookOpen } from 'lucide-react'
import { listArticles } from '@/lib/api/articles'
import { StatusPill } from '@/components/ui/StatusPill'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import type { ArticleStatus } from '@/lib/types'

type Filter = 'all' | ArticleStatus

interface Props { projectId: string }

export function ArticlesListScreen({ projectId }: Props) {
  const [filter, setFilter] = useState<Filter>('all')

  const { data: articles, isLoading, error, refetch } = useQuery({
    queryKey: ['articles', projectId],
    queryFn: () => listArticles(projectId),
  })

  const filtered = (articles ?? []).filter(a => filter === 'all' || a.status === filter)
  const counts: Record<string, number> = { all: articles?.length ?? 0 }
  articles?.forEach(a => { counts[a.status] = (counts[a.status] ?? 0) + 1 })

  if (isLoading) return <div style={{ padding: '24px 32px' }}><LoadingState /></div>
  if (error) return <div style={{ padding: '24px 32px' }}><ErrorState onRetry={() => refetch()} /></div>

  return (
    <div style={{ padding: '24px 32px 64px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '18px' }}>
        <div>
          <span className="eyebrow">Articles</span>
          <h1 style={{ fontSize: '28px', fontWeight: 400, letterSpacing: '-0.012em', color: 'var(--ink)', margin: '4px 0 6px' }}>
            Knowledge base
          </h1>
          <p style={{ margin: 0, fontSize: '13.5px', color: 'var(--graphite)' }}>
            {articles?.length ?? 0} articles compiled from your sources.
          </p>
        </div>
        <div className="segmented">
          {(['all', 'draft'] as Filter[]).map(s => (
            <button key={s} className={filter === s ? 'is-active' : ''} onClick={() => setFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
              {' '}
              <span style={{ opacity: 0.7 }}>{counts[s] ?? 0}</span>
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={BookOpen} title="No articles yet" body="Confirm candidates in the Inbox and build articles to populate this library." />
      ) : (
        <div>
          {/* Table header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 2.6fr) 200px 60px 70px 60px 90px 90px',
            gap: '16px', padding: '10px 8px',
            borderTop: '1px solid var(--rule)', borderBottom: '1px solid var(--rule)',
            fontFamily: 'var(--f-mono)', fontSize: '10.5px', letterSpacing: '0.06em',
            textTransform: 'uppercase', color: 'var(--graphite)',
          }}>
            <span>Article</span><span>Topic</span>
            <span style={{ textAlign: 'right' }}>Blocks</span>
            <span style={{ textAlign: 'right' }}>Sources</span>
            <span style={{ textAlign: 'right' }}>Cites</span>
            <span>Status</span><span>Updated</span>
          </div>

          {filtered.map((article, i) => (
            <Link key={article.id} href={`/${projectId}/articles/${article.id}`}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'minmax(0, 2.6fr) 200px 60px 70px 60px 90px 90px',
                  gap: '16px', padding: '14px 8px',
                  borderBottom: '1px solid var(--rule-soft)',
                  cursor: 'pointer', fontSize: '12.5px', color: 'var(--ink-2)',
                  alignItems: 'center',
                }}
                className="art-row"
                onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = 'var(--surface)'}
                onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = 'transparent'}
              >
                {/* Title */}
                <div style={{ display: 'grid', gridTemplateColumns: '30px 1fr', gap: '10px', alignItems: 'flex-start', minWidth: 0 }}>
                  <span style={{ fontSize: '11px', color: 'var(--slate)', paddingTop: '3px', letterSpacing: '0.04em', fontFamily: 'var(--f-mono)' }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div>
                    <h3 style={{ fontSize: '15px', fontWeight: 400, margin: 0, color: 'var(--ink)', letterSpacing: '-0.005em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {article.title}
                    </h3>
                    <p style={{ fontSize: '12px', color: 'var(--graphite)', margin: '4px 0 0', lineHeight: 1.45, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', maxWidth: '64ch' }}>
                      {article.excerpt}
                    </p>
                  </div>
                </div>

                <span style={{ fontSize: '11px', color: 'var(--ink-2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{article.topic}</span>
                <span style={{ textAlign: 'right' }}>{article.blocks}</span>
                <span style={{ textAlign: 'right' }}>{article.sources}</span>
                <span style={{ textAlign: 'right' }}>{article.citations}</span>
                <span><StatusPill status={article.status} /></span>
                <span style={{ fontSize: '11px', color: 'var(--slate)' }}>{article.updated}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
