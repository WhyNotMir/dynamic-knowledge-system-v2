'use client'

import { useEffect, useRef, useState } from 'react'
import type { ArticleBlock, ArticleDetail, BlockProvenance } from '@/lib/types'

interface ArticleBodyProps {
  article: ArticleDetail
  onOutlineChange: (id: string) => void
}

export function ArticleBody({ article, onOutlineChange }: ArticleBodyProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const [hoveredProvenance, setHoveredProvenance] = useState<BlockProvenance | BlockProvenance[] | null>(null)
  const visibleBlocks = article.blocks.filter(block => (
    !isGroupedCaptionBlock(block)
    && block.includeInArticle !== false
  ))
  const displayItems = groupAdjacentImages(visibleBlocks)

  useEffect(() => {
    const root = scrollRef.current
    if (!root || article.outline.length === 0) return

    const elements = article.outline
      .map(item => document.getElementById(`anchor-${item.id}`))
      .filter((element): element is HTMLElement => element !== null)

    if (elements.length === 0) return

    const observer = new IntersectionObserver(
      entries => {
        const visible = entries
          .filter(entry => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
        if (visible?.target.id) {
          onOutlineChange(visible.target.id.replace(/^anchor-/, ''))
        }
      },
      {
        root,
        rootMargin: '-12% 0px -72% 0px',
        threshold: [0, 1],
      },
    )

    elements.forEach(element => observer.observe(element))
    return () => observer.disconnect()
  }, [article.outline, onOutlineChange])

  return (
    <div
      ref={scrollRef}
      className="scroll"
      style={{
        overflowY: 'auto',
        padding: '28px 64px 80px',
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
          color: 'var(--ink)', maxWidth: '30ch',
        }}>
          {article.title}
        </h1>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--slate)', marginBottom: '22px', flexWrap: 'wrap' }}>
          {article.authors && <span>{article.authors}</span>}
          {article.authors && <span>·</span>}
          <span>Updated {article.updated}</span>
          <span>·</span>
          <span>{visibleBlocks.filter(block => block.type === 'p').length} paragraphs</span>
        </div>

        {article.summary && (
          <blockquote style={{
            fontFamily: 'var(--f-serif)',
            fontSize: '17px', lineHeight: 1.6,
            color: 'var(--ink-2)', margin: 0,
            maxWidth: '92ch',
            fontStyle: 'italic',
            borderLeft: '2px solid var(--brass)',
            padding: '4px 0 4px 18px',
          }}>
            {article.summary}
          </blockquote>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', maxWidth: '104ch' }}>
        {displayItems.map(item => (
          isImageGroup(item)
            ? (
              <ImageGroup
                key={item.id}
                group={item}
                onHover={setHoveredProvenance}
              />
            )
            : (
              <Block
                key={item.id}
                block={item}
                onHover={setHoveredProvenance}
              />
            )
        ))}
      </div>

      {hoveredProvenance && (
        <SourceHover provenance={hoveredProvenance} />
      )}
    </div>
  )
}

type DisplayItem = ArticleBlock | ImageBlockGroup

interface ImageBlockGroup {
  kind: 'image-group'
  id: string
  blocks: ArticleBlock[]
}

function groupAdjacentImages(blocks: ArticleBlock[]): DisplayItem[] {
  const items: DisplayItem[] = []
  let index = 0

  while (index < blocks.length) {
    const block = blocks[index]

    if (block.type !== 'image') {
      items.push(block)
      index += 1
      continue
    }

    const imageBlocks = [block]
    let nextIndex = index + 1
    while (nextIndex < blocks.length && shouldJoinImageBlock(imageBlocks[imageBlocks.length - 1], blocks[nextIndex])) {
      imageBlocks.push(blocks[nextIndex])
      nextIndex += 1
    }

    if (imageBlocks.length === 1) {
      items.push(block)
    } else {
      items.push({
        kind: 'image-group',
        id: imageBlocks.map(image => image.id).join(':'),
        blocks: imageBlocks,
      })
    }

    index = nextIndex
  }

  return items
}

function shouldJoinImageBlock(previous: ArticleBlock, next: ArticleBlock): boolean {
  if (next.type !== 'image') return false

  const previousProvenance = firstProvenance(previous.provenance)
  const nextProvenance = firstProvenance(next.provenance)
  if (!previousProvenance || !nextProvenance) return false

  const samePage = previousProvenance?.page === nextProvenance?.page
  const sameSection = previousProvenance?.section === nextProvenance?.section
  return samePage && sameSection
}

function isImageGroup(item: DisplayItem): item is ImageBlockGroup {
  return 'kind' in item && item.kind === 'image-group'
}

function firstProvenance(provenance: ArticleBlock['provenance']): BlockProvenance | null {
  if (!provenance) return null
  return Array.isArray(provenance) ? provenance[0] ?? null : provenance
}

function ImageGroup({
  group,
  onHover,
}: {
  group: ImageBlockGroup
  onHover: (provenance: BlockProvenance | BlockProvenance[] | null) => void
}) {
  const provenances = group.blocks
    .map(block => firstProvenance(block.provenance))
    .filter((provenance): provenance is BlockProvenance => Boolean(provenance))
  const caption = group.blocks.find(block => block.caption)?.caption

  const enter = () => onHover(provenances.length > 0 ? provenances : null)
  const leave = () => onHover(null)

  return (
    <figure
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{
        margin: '14px 0 18px',
        padding: '14px',
        border: '1px solid var(--rule)',
        background: 'var(--surface)',
      }}
    >
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${Math.min(group.blocks.length, 2)}, minmax(0, 1fr))`,
        gap: '14px',
        alignItems: 'start',
      }}>
        {group.blocks.map(block => (
          <div key={block.id} style={{ minWidth: 0 }}>
            <RenderedImage block={block} />
          </div>
        ))}
      </div>
      {caption && (
        <figcaption style={{
          margin: '12px auto 0',
          maxWidth: '82ch',
          fontSize: '12px',
          color: 'var(--slate)',
          lineHeight: 1.45,
          textAlign: 'center',
        }}>
          {caption}
        </figcaption>
      )}
    </figure>
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

  if (block.type === 'h3') return (
    <h4
      id={`anchor-${block.anchor ?? block.id}`}
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{
        fontSize: '14px',
        fontWeight: 600,
        margin: '14px 0 0',
        color: 'var(--ink-2)',
        letterSpacing: '0',
        scrollMarginTop: '24px',
      }}
    >
      {block.text}
    </h4>
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

  if (block.type === 'table') return (
    <figure
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{ margin: '8px 0 12px', overflowX: 'auto' }}
    >
      <RenderedTable block={block} />
      {block.caption && (
        <figcaption style={{ marginTop: 8, fontSize: '12px', color: 'var(--slate)', lineHeight: 1.45 }}>
          {block.caption}
        </figcaption>
      )}
    </figure>
  )

  if (block.type === 'image') return (
    <figure
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{
        margin: '12px 0 16px',
        padding: '14px',
        border: '1px solid var(--rule)',
        background: 'var(--surface)',
      }}
    >
      <RenderedImage block={block} />
      {block.caption && (
        <figcaption style={{
          margin: '12px auto 0',
          maxWidth: '82ch',
          fontSize: '12px',
          color: 'var(--slate)',
          lineHeight: 1.45,
          textAlign: 'center',
        }}>
          {block.caption}
        </figcaption>
      )}
    </figure>
  )

  if (block.type === 'caption') return (
    <p
      onMouseEnter={enter}
      onMouseLeave={leave}
      style={{
        fontSize: '12px',
        lineHeight: 1.55,
        margin: '-6px 0 4px',
        color: 'var(--slate)',
      }}
    >
      {block.text}
    </p>
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

function RenderedTable({ block }: { block: ArticleBlock }) {
  const rows = tableRows(block.meta)

  if (rows.length === 0) {
    return (
      <pre style={{
        margin: 0,
        whiteSpace: 'pre-wrap',
        fontFamily: 'var(--f-mono)',
        fontSize: '12px',
        lineHeight: 1.55,
        color: 'var(--ink)',
        background: 'var(--paper-2)',
        border: '1px solid var(--rule)',
        padding: '12px',
      }}>
        {block.text}
      </pre>
    )
  }

  const [head, ...body] = rows
  return (
    <table style={{
      width: '100%',
      borderCollapse: 'collapse',
      fontSize: '12.5px',
      lineHeight: 1.45,
      color: 'var(--ink)',
      background: 'var(--paper)',
      border: '1px solid var(--rule)',
    }}>
      <thead>
        <tr>
          {head.map((cell, index) => (
            <th key={index} style={{
              textAlign: 'left',
              fontWeight: 600,
              padding: '8px 10px',
              borderBottom: '1px solid var(--rule-strong)',
              background: 'var(--paper-2)',
            }}>
              {cell}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {body.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {row.map((cell, cellIndex) => (
              <td key={cellIndex} style={{
                padding: '8px 10px',
                borderTop: rowIndex === 0 ? 0 : '1px solid var(--rule)',
                verticalAlign: 'top',
              }}>
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function RenderedImage({ block }: { block: ArticleBlock }) {
  const src = imageSrc(block.meta)
  if (!src) {
    return (
      <div style={{
        minHeight: 160,
        display: 'grid',
        placeItems: 'center',
        border: '1px dashed var(--rule-strong)',
        color: 'var(--slate)',
        fontSize: '12px',
      }}>
        Source image unavailable
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={block.caption || block.text || 'Source image'}
      style={{
        display: 'block',
        maxWidth: '100%',
        maxHeight: 520,
        margin: '0 auto',
        objectFit: 'contain',
        background: 'white',
      }}
    />
  )
}

function tableRows(meta: ArticleBlock['meta']): string[][] {
  const table = meta?.table
  if (!table || typeof table !== 'object') return []
  const rows = (table as { rows?: unknown }).rows
  if (!Array.isArray(rows)) return []
  return rows
    .filter(row => Array.isArray(row))
    .map(row => row.map(cell => String(cell ?? '').trim()))
    .filter(row => row.some(Boolean))
}

function imageSrc(meta: ArticleBlock['meta']): string | null {
  const payload = meta?.image_base64
  if (typeof payload !== 'string' || !payload) return null
  const ext = typeof meta?.image_ext === 'string' ? meta.image_ext : 'png'
  return `data:image/${ext};base64,${payload}`
}

function isGroupedCaptionBlock(block: ArticleBlock): boolean {
  return block.type === 'caption' && typeof block.meta?.caption_group_id === 'string'
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
