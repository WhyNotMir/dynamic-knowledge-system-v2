'use client'

import Link from 'next/link'
import type { OutlineItem, SourceRef, RelatedArticle } from '@/lib/types'

interface Props {
  outline: OutlineItem[]
  activeId: string
  onSelect: (id: string) => void
  sourceRefs?: SourceRef[]
  relatedArticles?: RelatedArticle[]
  projectId: string
}

export function ArticleOutline({ outline, activeId, onSelect, sourceRefs, relatedArticles, projectId }: Props) {
  return (
    <div
      className="scroll"
      style={{
        borderLeft: '1px solid var(--rule)',
        padding: '22px 16px 24px',
        overflowY: 'auto',
        background: 'var(--paper)',
        height: '100%',
      }}
    >
      <div style={{ paddingBottom: '8px', borderBottom: '1px solid var(--rule)', marginBottom: '10px' }}>
        <span className="eyebrow">On this page</span>
      </div>

      <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {outline.map(item => {
          const isActive = item.id === activeId
          return (
            <li
              key={item.id}
              style={{
                display: 'grid',
                gridTemplateColumns: '12px 1fr',
                gap: '8px',
                alignItems: 'center',
                fontSize: item.level === 1 ? '12px' : '11.5px',
                color: isActive ? 'var(--ink)' : 'var(--ink-2)',
                fontWeight: isActive ? 500 : 400,
                paddingLeft: item.level === 2 ? '14px' : 0,
                cursor: 'pointer',
                padding: `4px ${item.level === 2 ? '0 4px 14px' : '0 4px 4px'} 4px`,
              }}
              onClick={() => onSelect(item.id)}
            >
              <div style={{
                width: 8, height: isActive ? 2 : 1,
                background: isActive ? 'var(--brass)' : 'var(--rule-strong)',
                display: 'inline-block',
              }} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.label}</span>
            </li>
          )
        })}
      </ul>

      {/* Sources */}
      {sourceRefs && sourceRefs.length > 0 && (
        <div style={{ marginTop: '24px', paddingTop: '14px', borderTop: '1px solid var(--rule)' }}>
          <div className="eyebrow" style={{ marginBottom: '8px' }}>Sources</div>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, fontSize: '12px', color: 'var(--ink-2)' }}>
            {sourceRefs.map(s => (
              <li key={s.id} style={{ padding: '6px 0', borderBottom: '1px solid var(--rule-soft)', lineHeight: 1.45 }}>
                {s.authors} ({s.year}). <em>{s.title}</em>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Related */}
      {relatedArticles && relatedArticles.length > 0 && (
        <div style={{ marginTop: '18px' }}>
          <div className="eyebrow" style={{ marginBottom: '8px' }}>Related articles</div>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {relatedArticles.map(a => (
              <li key={a.id} style={{ padding: '4px 0' }}>
                <Link href={`/${projectId}/articles/${a.id}`}>
                  <span style={{ fontSize: '12px', color: 'var(--ink)', borderBottom: '1px solid var(--rule-strong)', cursor: 'pointer' }}>
                    {a.title}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
