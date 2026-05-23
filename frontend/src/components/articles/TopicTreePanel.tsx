'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import type { TopicNode } from '@/lib/types'

interface Props {
  projectId: string
  articleId: string
  nodes: TopicNode[]
}

export function TopicTreePanel({ projectId, articleId, nodes }: Props) {
  return (
    <div
      className="scroll"
      style={{
        borderRight: '1px solid var(--rule)',
        background: 'var(--paper-2)',
        padding: '22px 16px 24px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: '8px', borderBottom: '1px solid var(--rule)', marginBottom: '10px' }}>
        <span className="eyebrow">Topics</span>
        <Link href={`/${projectId}/articles`}>
          <span style={{ fontSize: '10.5px', color: 'var(--slate)', cursor: 'pointer' }}>all articles</span>
        </Link>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1px', flex: 1 }}>
        {nodes.map(node => (
          <TreeNode key={node.id} node={node} projectId={projectId} currentArticleId={articleId} depth={0} />
        ))}
      </div>

      {/* Source provenance summary */}
      <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid var(--rule)' }}>
        <div style={{ fontSize: '10.5px', color: 'var(--ink-2)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <div>
            <span style={{ display: 'inline-block', minWidth: '90px', color: 'var(--slate)', textTransform: 'uppercase', letterSpacing: '0.04em', fontSize: '10px' }}>Last edited</span>
            <span>yesterday</span>
          </div>
          <div>
            <span style={{ display: 'inline-block', minWidth: '90px', color: 'var(--slate)', textTransform: 'uppercase', letterSpacing: '0.04em', fontSize: '10px' }}>Sources</span>
            <span>3 documents</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function TreeNode({ node, projectId, currentArticleId, depth }: {
  node: TopicNode
  projectId: string
  currentArticleId: string
  depth: number
}) {
  const [open, setOpen] = useState(node.open ?? false)
  const hasChildren = node.children && node.children.length > 0
  const isCurrent = node.articleId === currentArticleId

  const paddingLeft = depth === 0 ? 0 : depth === 1 ? 16 : 32
  const fontSize = depth === 0 ? '12.5px' : depth === 1 ? '12px' : '11.5px'
  const color = node.muted ? 'var(--whisper)' : isCurrent ? 'var(--paper)' : 'var(--ink-2)'

  const inner = (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '12px 1fr auto',
        gap: '6px',
        alignItems: 'center',
        padding: `4px 4px 4px ${paddingLeft}px`,
        borderRadius: '3px',
        cursor: 'pointer',
        fontSize,
        color,
        background: isCurrent ? 'var(--ink)' : 'transparent',
        position: 'relative',
      }}
      onMouseEnter={e => { if (!isCurrent) (e.currentTarget as HTMLElement).style.background = 'var(--surface)' }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = isCurrent ? 'var(--ink)' : 'transparent' }}
      onClick={() => { if (hasChildren) setOpen(v => !v) }}
    >
      {depth === 2 && <div style={{ position: 'absolute', left: 20, top: 0, bottom: 0, borderLeft: '1px solid var(--rule)' }} />}
      <span style={{ fontSize: '8px', color: isCurrent ? 'oklch(0.85 0.01 80)' : 'var(--slate)', textAlign: 'center', transform: hasChildren && open ? 'rotate(90deg)' : 'none', transition: 'transform 0.12s' }}>
        {hasChildren ? '▶' : '·'}
      </span>
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{node.label}</span>
      <span style={{ fontFamily: 'var(--f-mono)', fontSize: '10.5px', color: isCurrent ? 'oklch(0.85 0.01 80)' : 'var(--slate)' }}>{node.count}</span>
    </div>
  )

  return (
    <div>
      {node.articleId
        ? <Link href={`/${projectId}/articles/${node.articleId}`}>{inner}</Link>
        : inner
      }
      {hasChildren && open && (
        <div>
          {node.children!.map(child => (
            <TreeNode key={child.id} node={child} projectId={projectId} currentArticleId={currentArticleId} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}
