'use client'

import type { ArticleBlock, ArticleDetail, BlockProvenance } from '@/lib/types'

interface Props {
  article: ArticleDetail
  onCollapse: () => void
}

export function ArticleContextPanel({ article, onCollapse }: Props) {
  const sourceNames = uniqueSources(article)
  const pages = uniquePages(article)
  const composition = blockComposition(article.blocks)

  return (
    <aside
      className="scroll"
      style={{
        borderRight: '1px solid var(--rule)',
        background: 'var(--paper-2)',
        padding: '22px 16px 24px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        height: '100%',
      }}
    >
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', borderBottom: '1px solid var(--rule)', marginBottom: '10px' }}>
          <span className="eyebrow">Article context</span>
          <button
            type="button"
            onClick={onCollapse}
            title="Hide article context"
            style={{
              border: '1px solid var(--rule)',
              background: 'var(--surface)',
              color: 'var(--slate)',
              cursor: 'pointer',
              fontSize: '10.5px',
              padding: '2px 6px',
              borderRadius: 3,
            }}
          >
            Hide
          </button>
        </div>
        <h2 style={{ margin: '0 0 8px', fontSize: '15px', lineHeight: 1.3, fontWeight: 500, color: 'var(--ink)' }}>
          {article.title}
        </h2>
        <div style={{ fontSize: '11px', color: 'var(--slate)', lineHeight: 1.5 }}>
          Updated {article.updated}
        </div>
      </section>

      {article.topic.length > 0 && (
        <section>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Topic path</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {article.topic.map((topic, index) => (
              <div
                key={`${topic}-${index}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '14px 1fr',
                  gap: '8px',
                  alignItems: 'center',
                  fontSize: '12px',
                  color: index === article.topic.length - 1 ? 'var(--ink)' : 'var(--ink-2)',
                  paddingLeft: `${index * 10}px`,
                }}
              >
                <span style={{ width: 8, height: index === article.topic.length - 1 ? 2 : 1, background: index === article.topic.length - 1 ? 'var(--brass)' : 'var(--rule-strong)' }} />
                <span>{topic}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <div className="eyebrow" style={{ marginBottom: 8 }}>Source coverage</div>
        <dl style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '7px 12px', margin: 0, fontSize: '11.5px' }}>
          <dt style={{ color: 'var(--slate)' }}>Documents</dt>
          <dd style={{ margin: 0, color: 'var(--ink)' }}>{sourceNames.length}</dd>
          <dt style={{ color: 'var(--slate)' }}>Pages</dt>
          <dd style={{ margin: 0, color: 'var(--ink)' }}>{pages.length || 'unknown'}</dd>
          <dt style={{ color: 'var(--slate)' }}>Blocks</dt>
          <dd style={{ margin: 0, color: 'var(--ink)' }}>{article.blocks.length}</dd>
        </dl>
      </section>

      <section>
        <div className="eyebrow" style={{ marginBottom: 8 }}>Block mix</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11.5px' }}>
          {composition.map(item => (
            <div key={item.label} style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8 }}>
              <span style={{ color: 'var(--ink-2)' }}>{item.label}</span>
              <span style={{ fontFamily: 'var(--f-mono)', color: 'var(--slate)' }}>{item.count}</span>
            </div>
          ))}
        </div>
      </section>

      {sourceNames.length > 0 && (
        <section>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Documents</div>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {sourceNames.map(source => (
              <li key={source} style={{ fontSize: '11.5px', color: 'var(--ink-2)', lineHeight: 1.45, borderBottom: '1px solid var(--rule-soft)', paddingBottom: '6px' }}>
                {source}
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  )
}

function uniqueSources(article: ArticleDetail): string[] {
  const names = new Set<string>()
  for (const block of article.blocks) {
    for (const item of provenanceItems(block.provenance)) names.add(item.source)
  }
  return Array.from(names).sort()
}

function uniquePages(article: ArticleDetail): number[] {
  const pages = new Set<number>()
  for (const block of article.blocks) {
    for (const item of provenanceItems(block.provenance)) {
      if (typeof item.page === 'number') pages.add(item.page)
    }
  }
  return Array.from(pages).sort((a, b) => a - b)
}

function blockComposition(blocks: ArticleBlock[]): Array<{ label: string; count: number }> {
  const labels: Record<ArticleBlock['type'], string> = {
    h1: 'Headings',
    h2: 'Subheadings',
    h3: 'Nested headings',
    p: 'Paragraphs',
    eq: 'Equations',
    table: 'Tables',
    image: 'Images',
    caption: 'Captions',
  }

  const counts = new Map<string, number>()
  for (const block of blocks) {
    const label = labels[block.type] ?? 'Other'
    counts.set(label, (counts.get(label) ?? 0) + 1)
  }

  return Array.from(counts.entries())
    .map(([label, count]) => ({ label, count }))
    .filter(item => item.count > 0)
}

function provenanceItems(provenance: ArticleBlock['provenance']): BlockProvenance[] {
  if (!provenance) return []
  return Array.isArray(provenance) ? provenance : [provenance]
}
