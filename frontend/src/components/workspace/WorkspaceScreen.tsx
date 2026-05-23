'use client'

import Link from 'next/link'
import { Upload, Inbox, BookOpen, MessageSquare, AlertTriangle, Clock, CheckCircle, FileText } from 'lucide-react'
import type { Source, ArticleCandidate, ActivityItem, ActivityKind } from '@/lib/types'
import { StatusPill } from '@/components/ui/StatusPill'
import { SOURCE_COLORS } from '@/lib/ui/constants'

interface WorkspaceStats {
  totalSources: number
  totalFragments: number
  pendingReview: number
  totalArticles: number
}

interface WorkspaceScreenProps {
  projectId: string
  stats: WorkspaceStats
  sources: Source[]
  candidates: ArticleCandidate[]
  activity: ActivityItem[]
  todayLabel: string
}

export function WorkspaceScreen({ projectId, stats, sources, candidates, activity, todayLabel }: WorkspaceScreenProps) {
  const processingCount = sources.filter(s => s.status === 'processing' || s.status === 'pending').length
  const failedCount = sources.filter(s => s.status === 'failed').length

  return (
    <div style={{ padding: '24px 32px 64px', maxWidth: '100%' }}>
      {/* coord strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: '12px', alignItems: 'center', marginBottom: '20px' }}>
        <span className="coord">atlas.workspace</span>
        <div style={{ borderTop: '1px dashed var(--rule-strong)' }} />
        <span style={{ fontFamily: 'var(--f-mono)', fontSize: '10.5px', color: 'var(--slate)' }}>
          {todayLabel}
        </span>
      </div>

      {/* Hero */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '32px', alignItems: 'stretch', borderBottom: '1px solid var(--rule)', paddingBottom: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
          <h1 style={{ fontFamily: 'var(--f-serif)', fontSize: '38px', lineHeight: 1.05, fontWeight: 400, letterSpacing: '-0.018em', margin: '0 0 12px', color: 'var(--ink)' }}>
            Knowledge base
          </h1>
          <p style={{ margin: '0 0 18px', fontSize: '14px', color: 'var(--ink-2)', maxWidth: '56ch', lineHeight: 1.55 }}>
            Document-derived articles, organized for deep reading and precise Q&A.
            {processingCount > 0 && ` ${processingCount} source${processingCount > 1 ? 's' : ''} currently processing.`}
          </p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link href={`/${projectId}/sources`}>
              <button className="btn btn--primary"><Upload size={13} /> Upload sources</button>
            </Link>
            {stats.pendingReview > 0 && (
              <Link href={`/${projectId}/inbox`}>
                <button className="btn"><Inbox size={13} /> Review {stats.pendingReview} candidates</button>
              </Link>
            )}
          </div>
        </div>

        {/* Terrain / stats chart */}
        <div style={{ display: 'flex', flexDirection: 'column', border: '1px solid var(--rule)', background: 'var(--surface)' }}>
          <TerrainChart sources={sources} />
          <div style={{ borderTop: '1px solid var(--rule)', padding: '8px 10px' }}>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', fontFamily: 'var(--f-mono)', fontSize: '10px', color: 'var(--ink-2)' }}>
              <span><i style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: 'var(--moss)', marginRight: 4, verticalAlign: '-1px' }} />done</span>
              <span><i style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: 'var(--azure)', marginRight: 4, verticalAlign: '-1px' }} />processing</span>
              <span><i style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: 'var(--rule-strong)', marginRight: 4, verticalAlign: '-1px' }} />pending</span>
              <span><i style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: 'var(--rust)', marginRight: 4, verticalAlign: '-1px' }} />failed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Ledger stats */}
      <div style={{ borderBottom: '1px solid var(--rule)', padding: '8px 0 10px', marginBottom: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
          {[
            { val: stats.totalSources,      sub: 'Sources',             cls: '' },
            { val: stats.totalFragments,    sub: 'Extracted fragments', cls: '' },
            { val: stats.pendingReview,     sub: 'Pending review',      cls: stats.pendingReview > 0 ? 'stat-val--brass' : '' },
            { val: stats.totalArticles,     sub: 'Articles',            cls: '' },
          ].map(({ val, sub, cls }, i) => (
            <div key={i} style={{ borderRight: i < 3 ? '1px dashed var(--rule)' : 'none', paddingRight: i < 3 ? 24 : 0, paddingTop: 10, paddingBottom: 10 }}>
              <div className={`stat-val ${cls}`}>{val.toLocaleString()}</div>
              <div className="stat-sub">{sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Body grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '28px', alignItems: 'start' }}>
        {/* Action list */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: '8px', borderBottom: '1px solid var(--rule)', marginBottom: '4px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 500, margin: 0, color: 'var(--ink)' }}>Next actions</h2>
          </div>
          <div>
            {failedCount > 0 && (
              <ActionRow
                icon={<AlertTriangle size={13} />}
                variant="failed"
                href={`/${projectId}/sources`}
                title={`${failedCount} source${failedCount > 1 ? 's' : ''} failed to process`}
                hint="Check error details and retry or re-upload"
                action="View sources"
              />
            )}
            {processingCount > 0 && (
              <ActionRow
                icon={<Clock size={13} />}
                variant="process"
                href={`/${projectId}/sources`}
                title={`${processingCount} source${processingCount > 1 ? 's' : ''} processing`}
                hint="Fragment extraction in progress"
                action="Monitor"
              />
            )}
            {stats.pendingReview > 0 && (
              <ActionRow
                icon={<Inbox size={13} />}
                variant="review"
                href={`/${projectId}/inbox`}
                title={`${stats.pendingReview} article candidate${stats.pendingReview > 1 ? 's' : ''} awaiting review`}
                hint="Confirm or reject proposed articles"
                action="Open inbox"
              />
            )}
            {processingCount === 0 && failedCount === 0 && stats.pendingReview === 0 && (
              <ActionRow
                icon={<CheckCircle size={13} />}
                variant="ok"
                href={`/${projectId}/qa`}
                title="All caught up"
                hint="Ask questions to explore your knowledge base"
                action="Open Q&A"
              />
            )}
            <ActionRow
              icon={<Upload size={13} />}
              variant="ok"
              href={`/${projectId}/sources`}
              title="Upload more sources"
              hint="PDF documents to expand your knowledge base"
              action="Upload"
            />
            <ActionRow
              icon={<MessageSquare size={13} />}
              variant="qa"
              href={`/${projectId}/qa`}
              title="Ask a question"
              hint="Get cited answers from your articles"
              action="Open Q&A"
            />
          </div>
        </div>

        {/* Activity */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: '8px', borderBottom: '1px solid var(--rule)', marginBottom: '4px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 500, margin: 0, color: 'var(--ink)' }}>Recent activity</h2>
          </div>
          <div style={{ paddingTop: '6px' }}>
            {activity.map((item, i) => (
              <ActivityRow key={i} item={item} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────

function ActionRow({ icon, variant, href, title, hint, action }: {
  icon: React.ReactNode
  variant: 'review' | 'failed' | 'process' | 'qa' | 'ok'
  href: string
  title: string
  hint: string
  action: string
}) {
  const iconColors: Record<string, string> = {
    review:  'color: oklch(0.45 0.12 70); borderColor: oklch(0.78 0.08 70)',
    failed:  'color: oklch(0.45 0.12 32); borderColor: oklch(0.78 0.07 32); background: var(--rust-tint)',
    process: 'color: var(--azure)',
    qa:      'color: var(--ink)',
    ok:      'color: var(--moss); borderColor: oklch(0.78 0.06 145); background: var(--moss-tint)',
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '28px 1fr auto', gap: '12px', alignItems: 'center', padding: '14px 4px', borderBottom: '1px solid var(--rule-soft)' }}>
      <div style={{
        width: 22, height: 22,
        display: 'grid', placeItems: 'center',
        border: '1px solid var(--rule)',
        borderRadius: '50%',
        color: 'var(--graphite)',
        background: 'var(--surface)',
        flexShrink: 0,
        // Override per variant
        ...(variant === 'failed' ? { color: 'oklch(0.45 0.12 32)', borderColor: 'oklch(0.78 0.07 32)', background: 'var(--rust-tint)' } : {}),
        ...(variant === 'review' ? { color: 'oklch(0.45 0.12 70)', borderColor: 'oklch(0.78 0.08 70)' } : {}),
        ...(variant === 'ok'     ? { color: 'var(--moss)', borderColor: 'oklch(0.78 0.06 145)', background: 'var(--moss-tint)' } : {}),
        ...(variant === 'process'? { color: 'var(--azure)' } : {}),
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '13.5px', color: 'var(--ink)', lineHeight: 1.4 }}>{title}</div>
        <div style={{ fontSize: '10.5px', color: 'var(--slate)', marginTop: '2px' }}>{hint}</div>
      </div>
      <Link href={href}>
        <button className="btn btn--sm">{action} →</button>
      </Link>
    </div>
  )
}

const ACTIVITY_ICON: Record<ActivityKind, { icon: React.ElementType; colorClass: string }> = {
  process:   { icon: FileText,     colorClass: 't-azure' },
  candidate: { icon: Inbox,        colorClass: 't-brass' },
  confirm:   { icon: CheckCircle,  colorClass: 't-moss' },
  ask:       { icon: MessageSquare,colorClass: 't-ink' },
  upload:    { icon: Upload,       colorClass: 't-azure' },
  fail:      { icon: AlertTriangle,colorClass: 't-rust' },
  reject:    { icon: AlertTriangle,colorClass: 't-rust' },
}

const ACTIVITY_COLORS: Record<string, string> = {
  't-moss':  'var(--moss)',
  't-brass': 'var(--brass)',
  't-azure': 'var(--azure)',
  't-rust':  'var(--rust)',
  't-ink':   'var(--ink)',
}

function ActivityRow({ item }: { item: ActivityItem }) {
  const { icon: Icon, colorClass } = ACTIVITY_ICON[item.kind] ?? ACTIVITY_ICON.process
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '18px 1fr', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--rule-soft)' }}>
      <div style={{ width: 16, height: 16, display: 'grid', placeItems: 'center', marginTop: '1px', color: ACTIVITY_COLORS[colorClass] ?? 'var(--graphite)' }}>
        <Icon size={12} />
      </div>
      <div>
        <div style={{ fontSize: '12.5px', color: 'var(--ink-2)', lineHeight: 1.45 }}>
          {item.text}<span style={{ color: 'var(--ink)', fontWeight: 500 }}>{item.target}</span>
        </div>
        <div style={{ fontSize: '10.5px', color: 'var(--slate)', marginTop: '2px' }}>{item.meta} · {item.when}</div>
      </div>
    </div>
  )
}

function TerrainChart({ sources }: { sources: Source[] }) {
  const total = Math.max(sources.length, 1)
  const barW = 300 / total
  const statusColor: Record<string, string> = {
    done: 'var(--moss)', processing: 'var(--azure)',
    pending: 'var(--rule-strong)', failed: 'var(--rust)',
  }

  return (
    <svg width="100%" height="120" viewBox="0 0 360 120" preserveAspectRatio="none" style={{ display: 'block' }}>
      <rect width="360" height="120" fill="var(--surface)" />
      {sources.map((s, i) => {
        const x = (i / total) * 340 + 10
        const h = s.status === 'done'       ? 60 + (s.fragments / 10)
                : s.status === 'processing' ? 40 + (s.progress ?? 0.3) * 30
                : s.status === 'pending'    ? 25
                : 20
        const clampedH = Math.min(h, 95)
        const color = statusColor[s.status] ?? 'var(--rule)'
        return (
          <g key={s.id}>
            <rect
              x={x}
              y={120 - clampedH}
              width={Math.max(barW - 3, 6)}
              height={clampedH}
              fill={color}
              opacity={0.7}
            />
          </g>
        )
      })}
      {/* baseline */}
      <line x1="0" y1="119" x2="360" y2="119" stroke="var(--rule)" strokeWidth="1" />
    </svg>
  )
}
