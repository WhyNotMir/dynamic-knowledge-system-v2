'use client'

import { useState } from 'react'
import type { ArticleBlock, ArticleDetail, BlockProvenance } from '@/lib/types'

interface ArticleBodyProps {
  article: ArticleDetail
  onOutlineChange: (id: string) => void
}

export function ArticleBody({ article }: ArticleBodyProps) {
  const [hoveredProvenance, setHoveredProvenance] = useState<BlockProvenance | BlockProvenance[] | null>(null)

  return (
    <div
      className="scroll"
      style={{
        overflowY: 'auto',
        padding: '28px 56px 80px',
        background: 'var(--paper)',
        height: '100%',
        position: 'relative',
      }}
    >
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '11px', color: 'var(--slate)', marginBottom: '12px', letterSpacing: '0.04em' }}>
          {article.topic.map((topic, index) => (
            <span key={topic} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {index > 0 && <span style={{ color: 'var(--whisper)' }}>›</span>}
              <span>{topic}</span>
            </span>
          ))}
        </div>

        <h1 style={{
          fontFamily: 'var(--f-serif)',
          fontSize: '38px', lineHeight: 1.1, fontWeight: 400,
          letterSpacing: '-0.018em', margin: '0 0 14px',
          color: 'var(--ink)', maxWidth: '22ch',
        }}>
          {article.title}
        </h1>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--slate)', marginBottom: '22px', flexWrap: 'wrap' }}>
          {article.authors && <span>{article.authors}</span>}
          {article.authors && <span>·</span>}
          <span>Updated {article.updated}</span>
          <span>·</span>
          <span>{article.blocks.filter(block => block.type === 'p').length} paragraphs</span>
        </div>

        {article.summary && (
          <blockquote style={{
            fontFamily: 'var(--f-serif)',
            fontSize: '17px', lineHeight: 1.6,
            color: 'var(--ink-2)', margin: 0,
            maxWidth: '64ch',
            fontStyle: 'italic',
            borderLeft: '2px solid var(--brass)',
            padding: '4px 0 4px 18px',
          }}>
            {article.summary}
          </blockquote>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '64ch' }}>
        {article.blocks.map(block => (
          <Block
            key={block.id}
            block={block}
            onHover={setHoveredProvenance}
          />
        ))}
      </div>

      {hoveredProvenance && (
        <SourceHover provenance={hoveredProvenance} />
      )}
    </div>
  )
}

function Block({
  block,
  onHover,
}: {
  block: ArticleBlock
  onHover: (provenance: BlockProvenance | BlockProvenance[] | null) => void
}) {
  const enter = () => onHover(block.provenance ?? null)
  const leave = () => onHover(null)

  if (block.type === 'h1') return (
    <h2
      id={`anchor-${block.anchor ?? block.id}`}
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{
        fontSize: '22px', fontWeight: 500, margin: '32px 0 6px',
        letterSpacing: '-0.008em', color: 'var(--ink)',
        paddingBottom: '6px', borderBottom: '1px solid var(--rule)',
        scrollMarginTop: '24px',
      }}
    >
      {block.text}
    </h2>
  )

  if (block.type === 'h2') return (
    <h3
      id={`anchor-${block.anchor ?? block.id}`}
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{ fontSize: '17px', fontWeight: 500, margin: '20px 0 4px', color: 'var(--ink)', letterSpacing: '-0.005em', scrollMarginTop: '24px' }}
    >
      {block.text}
    </h3>
  )

  if (block.type === 'eq') return (
    <div
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{
        padding: '14px 22px', background: 'var(--paper-2)',
        borderLeft: '2px solid var(--rule-strong)',
        display: 'flex', flexDirection: 'column', gap: '8px',
        margin: '4px 0', position: 'relative',
      }}
    >
      <div style={{ fontFamily: 'var(--f-serif)', fontStyle: 'italic', fontSize: '19px', letterSpacing: '0.005em', color: 'var(--ink)', textAlign: 'center', padding: '4px 0' }}>
        {block.text}
      </div>
      {block.caption && (
        <div style={{ fontSize: '11.5px', color: 'var(--graphite)', textAlign: 'center', fontStyle: 'normal' }}>
          {block.caption}
        </div>
      )}
    </div>
  )

  return (
    <p
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{
        fontFamily: 'var(--f-serif)',
        fontSize: '16px',
        lineHeight: 1.65,
        margin: 0,
        color: 'var(--ink)',
      }}
    >
      {block.text}
    </p>
  )
}

function SourceHover({ provenance }: { provenance: BlockProvenance | BlockProvenance[] }) {
  const first = Array.isArray(provenance) ? provenance[0] : provenance

  return (
    <div style={{
      position: 'fixed',
      right: 28,
      bottom: 28,
      maxWidth: 360,
      background: 'var(--surface)',
      border: '1px solid var(--rule-strong)',
      boxShadow: '0 14px 34px oklch(0.2 0.02 260 / 0.14)',
      padding: '10px 12px',
      zIndex: 30,
      fontSize: '11.5px',
      color: 'var(--ink-2)',
      lineHeight: 1.45,
    }}>
      <div className="eyebrow" style={{ marginBottom: 4 }}>Source</div>
      <div style={{ fontWeight: 500, color: 'var(--ink)' }}>{first.source}</div>
      <div style={{ color: 'var(--slate)' }}>
        {first.page ? `p.${first.page}` : 'page unknown'}
        {first.section ? ` · ${first.section}` : ''}
      </div>
    </div>
  )
}
