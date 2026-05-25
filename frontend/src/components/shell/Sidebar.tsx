'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  LayoutDashboard, Upload, Inbox, BookOpen, MessageSquare,
  ChevronDown, ChevronLeft, Check,
} from 'lucide-react'
import type { Project, TopicNode } from '@/lib/types'
import { listArticles } from '@/lib/api/articles'
import { listProjects } from '@/lib/api/projects'
import { buildTopicTree } from '@/lib/topic-tree'

interface SidebarProps {
  project: Project
  activeSection: string
}

const NAV_ITEMS = [
  { id: 'workspace', label: 'Workspace',  icon: LayoutDashboard },
  { id: 'sources',   label: 'Sources',    icon: Upload },
  { id: 'inbox',     label: 'Inbox',      icon: Inbox },
  { id: 'articles',  label: 'Articles',   icon: BookOpen },
  { id: 'qa',        label: 'Q & A',      icon: MessageSquare },
]

export function Sidebar({ project, activeSection }: SidebarProps) {
  const [projOpen, setProjOpen] = useState(false)

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  })
  const { data: articles } = useQuery({
    queryKey: ['articles', project.id],
    queryFn: () => listArticles(project.id),
  })
  const topicTree = buildTopicTree(articles ?? [])

  return (
    <aside
      className="topo-bg"
      style={{
        background: 'var(--vellum)',
        borderRight: '1px solid var(--rule)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
        position: 'relative',
        zIndex: 1,
      }}
    >
      {/* ── Project switcher ── */}
      <div style={{ padding: '14px 12px 12px', borderBottom: '1px solid var(--rule)', position: 'relative' }}>
        <button
          onClick={() => setProjOpen(v => !v)}
          style={{
            display: 'grid',
            gridTemplateColumns: '32px 1fr 12px',
            gap: '9px',
            alignItems: 'center',
            width: '100%',
            padding: '6px 8px 6px 6px',
            border: '1px solid transparent',
            borderRadius: '4px',
            background: 'transparent',
            cursor: 'pointer',
            textAlign: 'left',
          }}
          className={projOpen ? 'proj-sw-open' : ''}
        >
          <ProjectGlyph glyph={project.glyph} />
          <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, gap: '1px' }}>
            <span className="eyebrow" style={{ fontSize: '9.5px' }}>Project</span>
            <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {project.name}
            </span>
          </div>
          <ChevronDown size={11} color="var(--slate)" style={{ transform: projOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }} />
        </button>

        {projOpen && (
          <ProjectPopover
            projects={projects ?? []}
            currentId={project.id}
            onClose={() => setProjOpen(false)}
          />
        )}
      </div>

      {/* ── Nav items ── */}
      <nav style={{ display: 'flex', flexDirection: 'column', padding: '10px 8px', gap: '1px', borderBottom: '1px solid var(--rule)' }}>
        {NAV_ITEMS.map(item => {
          const Icon = item.icon
          const isActive = activeSection === item.id
          const href = `/${project.id}/${item.id === 'workspace' ? '' : item.id}`
          const badge = item.id === 'inbox'
            ? project.candidates > 0 ? project.candidates : undefined
            : undefined
          return (
            <Link key={item.id} href={href}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '16px 1fr auto',
                  gap: '10px',
                  alignItems: 'center',
                  padding: '6px 9px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  color: isActive ? 'var(--paper)' : 'var(--ink-2)',
                  background: isActive ? 'var(--ink)' : 'transparent',
                  fontSize: '12.5px',
                }}
              >
                <Icon size={14} color={isActive ? 'var(--paper)' : 'var(--graphite)'} />
                <span>{item.label}</span>
                {badge !== undefined && (
                  <span style={{
                    fontFamily: 'var(--f-mono)',
                    fontSize: '10px',
                    padding: '1px 6px',
                    borderRadius: '8px',
                    background: isActive ? 'oklch(0.32 0.018 260)' : 'var(--brass)',
                    color: 'var(--paper)',
                    letterSpacing: '0.02em',
                  }}>
                    {badge}
                  </span>
                )}
              </div>
            </Link>
          )
        })}
      </nav>

      {/* ── Atlas mini index ── */}
      <div className="scroll" style={{ padding: '14px 12px 10px', flex: 1, overflowY: 'auto', minHeight: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
          <span className="eyebrow">Atlas index</span>
          <Link href={`/${project.id}/articles`}>
            <span className="btn btn--ghost btn--xs" style={{ fontSize: '10.5px', color: 'var(--graphite)' }}>
              {topicTree.length > 0 ? 'View tree' : 'all'}
            </span>
          </Link>
        </div>
        <MiniTopicTree nodes={topicTree} projectId={project.id} depth={0} />
      </div>

      {/* ── Rail foot ── */}
      <div style={{ borderTop: '1px solid var(--rule)', padding: '10px 14px 12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
          <span style={{ fontSize: '10.5px', color: 'var(--slate)' }}>
            {project.sources} sources · {project.articles} articles
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'oklch(0.55 0.06 145)', color: 'var(--paper)', display: 'grid', placeItems: 'center', fontSize: '10.5px', fontWeight: 500 }}>
            M
          </div>
          <span style={{ fontSize: '11.5px', color: 'var(--ink-2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {project.name} workspace
          </span>
        </div>
      </div>
    </aside>
  )
}

// ── Sub-components ────────────────────────────────────────────────

function ProjectGlyph({ glyph, small }: { glyph: string; small?: boolean }) {
  const size = small ? 24 : 32
  return (
    <div style={{
      width: size, height: size,
      background: 'var(--ink)',
      color: 'var(--paper)',
      display: 'grid', placeItems: 'center',
      fontFamily: 'var(--f-mono)',
      fontSize: small ? 10 : 11,
      fontWeight: 600,
      letterSpacing: '0.04em',
      borderRadius: '2px',
      flexShrink: 0,
      position: 'relative',
    }}>
      {glyph}
    </div>
  )
}

function ProjectPopover({ projects, currentId, onClose }: {
  projects: Project[]
  currentId: string
  onClose: () => void
}) {
  return (
    <div style={{
      position: 'absolute',
      top: 'calc(100% - 4px)',
      left: 12, right: 12,
      background: 'var(--surface)',
      border: '1px solid var(--rule-strong)',
      borderRadius: '4px',
      boxShadow: '0 12px 32px oklch(0.2 0.02 260 / 0.12)',
      zIndex: 20,
      padding: '4px',
      width: '320px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 8px 6px', borderBottom: '1px solid var(--rule)', marginBottom: '4px' }}>
        <span className="eyebrow">Switch project</span>
        <Link href="/projects">
          <span style={{ fontSize: '10.5px', color: 'var(--slate)', cursor: 'pointer' }} onClick={onClose}>All projects</span>
        </Link>
      </div>
      {projects.map(p => (
        <Link key={p.id} href={`/${p.id}/`} onClick={onClose}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '24px 1fr 16px',
            gap: '10px',
            alignItems: 'center',
            padding: '6px 8px',
            borderRadius: '3px',
            cursor: 'pointer',
            background: p.id === currentId ? 'var(--brass-tint)' : 'transparent',
          }}
          onMouseEnter={e => { if (p.id !== currentId) (e.currentTarget as HTMLElement).style.background = 'var(--paper-2)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = p.id === currentId ? 'var(--brass-tint)' : 'transparent' }}
          >
            <ProjectGlyph glyph={p.glyph} small />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', minWidth: 0 }}>
              <span style={{ fontSize: '12.5px', fontWeight: 500, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
              <span style={{ fontSize: '10.5px', color: 'var(--slate)' }}>{p.articles} articles · {p.sources} sources</span>
            </div>
            {p.id === currentId && <Check size={12} color="var(--moss)" />}
          </div>
        </Link>
      ))}
      <div style={{ borderTop: '1px solid var(--rule)', padding: '6px 8px 2px', marginTop: '4px' }}>
        <Link href="/projects" onClick={onClose}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10.5px', color: 'var(--slate)', cursor: 'pointer', padding: '2px 0' }}>
            <ChevronLeft size={11} /> Back to projects
          </div>
        </Link>
      </div>
    </div>
  )
}

function MiniTopicTree({ nodes, projectId, depth }: { nodes: TopicNode[]; projectId: string; depth: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {nodes.map(node => (
        <MiniTopicNode key={node.id} node={node} projectId={projectId} depth={depth} />
      ))}
    </div>
  )
}

function MiniTopicNode({ node, projectId, depth }: { node: TopicNode; projectId: string; depth: number }) {
  const [open, setOpen] = useState(node.open ?? false)
  const hasChildren = node.children && node.children.length > 0
  const href = node.articleId ? `/${projectId}/articles/${node.articleId}` : `/${projectId}/articles`

  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '14px 1fr auto',
          gap: '6px',
          alignItems: 'center',
          padding: depth === 0 ? '3px 0' : '3px 0 3px 14px',
          fontSize: depth === 0 ? '12px' : '11.5px',
          color: node.muted ? 'var(--whisper)' : node.active ? 'var(--ink)' : 'var(--ink-2)',
          fontWeight: node.active ? 500 : 400,
          position: 'relative',
          cursor: 'pointer',
        }}
        onClick={() => {
          if (hasChildren) setOpen(v => !v)
        }}
      >
        {depth > 0 && (
          <div style={{ position: 'absolute', left: 4, top: 0, bottom: 0, borderLeft: '1px solid var(--rule)' }} />
        )}
        <div style={{
          width: 6, height: 6,
          border: '1px solid var(--slate)',
          background: depth === 0 ? 'var(--slate)' : node.active ? 'var(--brass)' : 'transparent',
          borderColor: node.active ? 'var(--brass)' : 'var(--slate)',
          flexShrink: 0,
        }} />
        {node.articleId
          ? <Link href={href} style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'inherit' }}>{node.label}</Link>
          : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{node.label}</span>
        }
        <span style={{ fontSize: '10.5px', color: 'var(--slate)' }}>{node.count}</span>
      </div>
      {hasChildren && open && (
        <MiniTopicTree nodes={node.children!} projectId={projectId} depth={depth + 1} />
      )}
    </div>
  )
}
