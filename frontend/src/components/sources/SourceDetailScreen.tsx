'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { AlertTriangle, RefreshCw, ChevronLeft, FileText } from 'lucide-react'
import { toast } from 'sonner'
import { getSource, listSourceFragments, retrySource } from '@/lib/api/sources'
import { StatusPill } from '@/components/ui/StatusPill'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { SOURCE_COLORS } from '@/lib/ui/constants'
import type { Source, SourceFragment } from '@/lib/types'

interface Props { projectId: string; sourceId: string }

export function SourceDetailScreen({ projectId, sourceId }: Props) {
  const qc = useQueryClient()
  const [showFragments, setShowFragments] = useState(true)

  const { data: source, isLoading, error, refetch } = useQuery({
    queryKey: ['source', projectId, sourceId],
    queryFn: () => getSource(projectId, sourceId),
    refetchInterval: query => {
      const currentSource = query.state.data as Source | undefined
      return currentSource?.status === 'pending' || currentSource?.status === 'processing'
        ? 2000
        : false
    },
    refetchOnWindowFocus: true,
  })

  const { data: fragments, isLoading: fragsLoading } = useQuery({
    queryKey: ['fragments', projectId, sourceId],
    queryFn: () => listSourceFragments(projectId, sourceId),
    enabled: source?.status === 'done',
  })

  const retryMut = useMutation({
    mutationFn: () => retrySource(projectId, sourceId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['source', projectId, sourceId] })
      toast.success('Source queued for retry')
    },
  })

  if (isLoading) return <div style={{ padding: '24px 32px' }}><LoadingState /></div>
  if (error || !source) return <div style={{ padding: '24px 32px' }}><ErrorState onRetry={() => refetch()} /></div>

  const fragmentCount = fragments?.length ?? source.fragments
  const pageCount = source.pages ?? new Set((fragments ?? []).map(fragment => fragment.page).filter(Boolean)).size

  return (
    <div style={{ padding: '24px 32px 80px' }}>
      {/* Back */}
      <Link href={`/${projectId}/sources`}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--slate)', marginBottom: '16px', cursor: 'pointer' }}>
          <ChevronLeft size={12} /> Sources
        </span>
      </Link>

      {/* Detail header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--rule)', paddingBottom: '18px', marginBottom: '20px', gap: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <div style={{ width: 4, height: 40, borderRadius: '1px', background: SOURCE_COLORS[source.color] ?? 'var(--slate)' }} />
            <div>
              <h1 style={{ fontSize: '28px', fontWeight: 400, letterSpacing: '-0.012em', color: 'var(--ink)', margin: '0 0 4px' }}>
                {source.title}
              </h1>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '11.5px', color: 'var(--slate)' }}>
                {source.authors && <span>{source.authors}</span>}
                {source.year && <span>·</span>}
                {source.year && <span>{source.year}</span>}
                <span>·</span>
                <span>{source.filename}</span>
              </div>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexShrink: 0 }}>
          <StatusPill status={source.status} />
          {source.status === 'failed' && (
            <button className="btn btn--sm" onClick={() => retryMut.mutate()} disabled={retryMut.isPending}>
              <RefreshCw size={12} /> {retryMut.isPending ? 'Retrying…' : 'Retry'}
            </button>
          )}
        </div>
      </div>

      {/* Failed error card */}
      {source.status === 'failed' && source.error && (
        <div style={{ border: '1px solid oklch(0.80 0.07 32)', background: 'var(--rust-tint)', borderRadius: '3px', padding: '18px 20px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <div style={{ width: 26, height: 26, border: '1px solid oklch(0.75 0.10 32)', background: 'var(--surface)', color: 'oklch(0.45 0.12 32)', borderRadius: '50%', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <AlertTriangle size={13} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '14px', color: 'oklch(0.38 0.12 32)', fontWeight: 500 }}>Processing failed</div>
              <div style={{ fontSize: '10.5px', color: 'var(--slate)', marginTop: '2px' }}>Uploaded {source.uploaded} · {source.filename}</div>
              <p style={{ fontSize: '13px', color: 'var(--ink-2)', margin: '14px 0 10px', maxWidth: '70ch' }}>{source.error}</p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 24px', padding: '10px 0 0', borderTop: '1px dashed oklch(0.80 0.05 32)', fontSize: '11.5px', color: 'var(--ink-2)' }}>
                <span><span style={{ color: 'oklch(0.5 0.1 32)', marginRight: '6px' }}>File</span>{source.filename}</span>
                <span><span style={{ color: 'oklch(0.5 0.1 32)', marginRight: '6px' }}>Size</span>{source.size}</span>
                <span><span style={{ color: 'oklch(0.5 0.1 32)', marginRight: '6px' }}>Pages</span>{source.pages}</span>
                <span><span style={{ color: 'oklch(0.5 0.1 32)', marginRight: '6px' }}>Uploaded</span>{source.uploaded}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      {source.status === 'done' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', borderTop: '1px solid var(--rule)', borderBottom: '1px solid var(--rule)', marginBottom: '24px', gap: '24px', padding: '4px 0' }}>
          {[
            { val: pageCount,               sub: 'Pages' },
            { val: fragmentCount,           sub: 'Fragments' },
            { val: source.candidates,       sub: 'Candidates',  cls: source.candidates > 0 ? 'stat-val--brass' : '' },
            { val: source.articles,         sub: 'In articles', cls: source.articles    > 0 ? 'stat-val--moss'  : '' },
          ].map(({ val, sub, cls }, i) => (
            <div key={i} style={{ padding: '10px 0', borderRight: i < 3 ? '1px dashed var(--rule)' : 'none', paddingRight: i < 3 ? '24px' : 0 }}>
              <div className={`stat-val ${cls ?? ''}`}>{val.toLocaleString()}</div>
              <div className="stat-sub">{sub}</div>
            </div>
          ))}
        </div>
      )}

      {/* Fragments */}
      {source.status === 'done' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 500, margin: 0, color: 'var(--ink)' }}>Extracted fragments</h2>
            <button className="btn btn--ghost btn--sm" onClick={() => setShowFragments(v => !v)}>
              {showFragments ? 'Collapse' : 'Expand'}
            </button>
          </div>

          {showFragments && (
            fragsLoading ? <LoadingState label="Loading fragments…" /> :
            <div>
              {(fragments ?? []).map(frag => (
                <FragmentRow key={frag.id} fragment={frag} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Processing state */}
      {source.status === 'processing' && (
        <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--graphite)' }}>
          <div style={{ marginBottom: '12px' }}>
            <div className="bar bar--azure" style={{ width: '240px', margin: '0 auto', height: '3px' }}>
              <i style={{ width: `${(source.progress ?? 0.3) * 100}%` }} />
            </div>
          </div>
          <p style={{ fontSize: '13.5px', margin: 0 }}>Extracting fragments… {Math.round((source.progress ?? 0) * 100)}% complete</p>
        </div>
      )}

      {/* Pending state */}
      {source.status === 'pending' && (
        <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--graphite)', fontSize: '13.5px' }}>
          <FileText size={24} style={{ marginBottom: '10px', display: 'block', margin: '0 auto 10px' }} />
          Queued for processing — this usually takes a few seconds.
        </div>
      )}
    </div>
  )
}

function FragmentRow({ fragment }: { fragment: SourceFragment }) {
  const isLinked = !!fragment.linkedBlock
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '80px minmax(0, 1fr) 160px',
      gap: '18px', padding: '12px 8px',
      borderBottom: '1px solid var(--rule-soft)',
      alignItems: 'flex-start',
    }}
    className="frag-row"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', fontSize: '11px', color: 'var(--graphite)' }}>
        <span style={{ fontFamily: 'var(--f-mono)', fontSize: '10.5px' }}>{fragment.id}</span>
        <span style={{ fontSize: '10.5px', color: 'var(--slate)' }}>p.{fragment.page}</span>
      </div>
      <div>
        <div style={{ fontSize: '10.5px', color: 'var(--graphite)', marginBottom: '4px', letterSpacing: '0.02em' }}>{fragment.section}</div>
        <p style={{ fontFamily: 'var(--f-serif)', fontSize: '13px', color: 'var(--ink)', lineHeight: 1.55, margin: 0 }}>
          {fragment.text}
        </p>
      </div>
      <div style={{ textAlign: 'right' }}>
        {isLinked ? (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '10.5px', color: 'var(--moss)', padding: '2px 6px', border: '1px solid oklch(0.78 0.04 145)', background: 'var(--moss-tint)', borderRadius: '2px' }}>
            ↗ In article
          </span>
        ) : (
          <span style={{ fontSize: '10.5px', color: 'var(--slate)' }}>Unlinked</span>
        )}
      </div>
    </div>
  )
}
