'use client'

import { useState, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Upload, ChevronRight, RefreshCw, Trash2, Eye } from 'lucide-react'
import { toast } from 'sonner'
import { listSources, uploadSource, deleteSource } from '@/lib/api/sources'
import { StatusPill } from '@/components/ui/StatusPill'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { SOURCE_COLORS } from '@/lib/ui/constants'
import type { Source, SourceStatus } from '@/lib/types'

type FilterStatus = 'all' | SourceStatus

interface SourcesScreenProps { projectId: string }

export function SourcesScreen({ projectId }: SourcesScreenProps) {
  const [filter, setFilter] = useState<FilterStatus>('all')
  const [isDrag, setIsDrag] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const qc = useQueryClient()
  const router = useRouter()

  const { data: sources, isLoading, error, refetch } = useQuery({
    queryKey: ['sources', projectId],
    queryFn: () => listSources(projectId),
    refetchInterval: query => {
      const currentSources = query.state.data as Source[] | undefined
      return currentSources?.some(source => source.status === 'pending' || source.status === 'processing')
        ? 2000
        : false
    },
    refetchOnWindowFocus: true,
  })

  const uploadMut = useMutation({
    mutationFn: (file: File) => uploadSource(projectId, file),
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: ['sources', projectId] })
      toast.success(`"${s.title}" queued for processing`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteSource(projectId, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sources', projectId] })
      toast.success('Source deleted')
    },
  })

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return
    Array.from(files).forEach(f => {
      if (f.type === 'application/pdf') uploadMut.mutate(f)
      else toast.error(`${f.name} is not a PDF`)
    })
  }, [uploadMut])

  const filtered = sources?.filter(s => filter === 'all' || s.status === filter) ?? []

  const counts: Record<string, number> = { all: sources?.length ?? 0 }
  sources?.forEach(s => { counts[s.status] = (counts[s.status] ?? 0) + 1 })

  if (isLoading) return <div style={{ padding: '24px 32px' }}><LoadingState label="Loading sources…" /></div>
  if (error) return <div style={{ padding: '24px 32px' }}><ErrorState onRetry={() => refetch()} /></div>

  return (
    <div style={{ padding: '24px 32px 64px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: '24px', marginBottom: '18px' }}>
        <div>
          <span className="eyebrow">Sources</span>
          <h1 style={{ fontSize: '28px', lineHeight: 1.15, fontWeight: 400, letterSpacing: '-0.012em', color: 'var(--ink)', margin: '4px 0 6px' }}>
            Document library
          </h1>
          <p style={{ margin: 0, fontSize: '13.5px', color: 'var(--graphite)' }}>
            Upload PDF sources. Atlas extracts fragments and proposes article candidates.
          </p>
        </div>
        <button className="btn btn--primary" onClick={() => fileRef.current?.click()}>
          <Upload size={13} /> Upload PDF
        </button>
        <input ref={fileRef} type="file" accept=".pdf" multiple hidden onChange={e => handleFiles(e.target.files)} />
      </div>

      {/* Upload zone */}
      <div
        className={`upload${isDrag ? ' is-drag' : ''}`}
        onDragOver={e => { e.preventDefault(); setIsDrag(true) }}
        onDragLeave={() => setIsDrag(false)}
        onDrop={e => { e.preventDefault(); setIsDrag(false); handleFiles(e.dataTransfer.files) }}
        onClick={() => fileRef.current?.click()}
        style={{ cursor: 'pointer', marginBottom: '22px' }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '32px 1fr', gap: '14px', alignItems: 'center' }}>
          <Upload size={22} color="var(--graphite)" />
          <div>
            <div style={{ fontSize: '16px', color: 'var(--ink)', marginBottom: '2px' }}>Drop PDFs here</div>
            <div style={{ fontSize: '10.5px', color: 'var(--slate)' }}>or click to browse · PDF only · max 50 MB per file</div>
          </div>
        </div>
        {uploadMut.isPending && (
          <div style={{ borderLeft: '1px dashed var(--rule)', paddingLeft: '24px' }}>
            <div style={{ fontSize: '11.5px', color: 'var(--slate)' }}>Uploading…</div>
          </div>
        )}
      </div>

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: '6px', alignItems: 'center', borderBottom: '1px solid var(--rule)', paddingBottom: '10px', marginBottom: '12px' }}>
        {(['all', 'done', 'processing', 'pending', 'failed'] as FilterStatus[]).map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`filter-chip${filter === s ? ' is-active' : ''}`}
            style={{
              appearance: 'none', border: 0, padding: '5px 10px', borderRadius: '3px',
              fontSize: '12px', color: filter === s ? 'var(--paper)' : 'var(--ink-2)',
              background: filter === s ? 'var(--ink)' : 'transparent', cursor: 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--f-sans)',
            }}
          >
            {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            <span style={{ fontSize: '10.5px', color: filter === s ? 'oklch(0.95 0.01 80)' : 'var(--slate)' }}>
              {counts[s] ?? 0}
            </span>
          </button>
        ))}
      </div>

      {/* Source table */}
      {filtered.length === 0 ? (
        <EmptyState icon={Upload} title="No sources" body="Upload PDF documents to start building your knowledge base." />
      ) : (
        <div>
          {/* Table header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 2.4fr) 130px 60px 90px 100px 80px 90px 28px',
            gap: '12px', padding: '8px 8px',
            borderBottom: '1px solid var(--rule)',
            fontFamily: 'var(--f-mono)', fontSize: '10.5px', letterSpacing: '0.06em',
            textTransform: 'uppercase', color: 'var(--graphite)',
          }}>
            <span>Title</span><span>Status</span><span style={{ textAlign: 'right' }}>Pages</span>
            <span style={{ textAlign: 'right' }}>Fragments</span><span style={{ textAlign: 'right' }}>Candidates</span>
            <span style={{ textAlign: 'right' }}>Size</span><span>Uploaded</span><span />
          </div>

          {filtered.map(source => (
            <SourceRow
              key={source.id}
              source={source}
              projectId={projectId}
              onDelete={() => deleteMut.mutate(source.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ── Source Row ────────────────────────────────────────────────────

function SourceRow({ source, projectId, onDelete }: { source: Source; projectId: string; onDelete: () => void }) {
  const [hovered, setHovered] = useState(false)

  return (
    <Link href={`/${projectId}/sources/${source.id}`}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 2.4fr) 130px 60px 90px 100px 80px 90px 28px',
          gap: '12px', padding: '12px 8px',
          borderBottom: '1px solid var(--rule-soft)',
          alignItems: 'center', cursor: 'pointer',
          background: hovered ? 'var(--surface)' : 'transparent',
          transition: 'background 0.1s',
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {/* Title cell */}
        <div style={{ display: 'grid', gridTemplateColumns: '8px 1fr', gap: '12px', alignItems: 'center', minWidth: 0 }}>
          <div style={{ width: 4, height: 38, borderRadius: '1px', background: SOURCE_COLORS[source.color] ?? 'var(--slate)', flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: '14.5px', color: 'var(--ink)', fontWeight: 400, margin: 0, letterSpacing: '-0.003em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {source.title}
            </div>
            <div style={{ fontSize: '10.5px', color: 'var(--slate)', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {source.authors}{source.year ? ` · ${source.year}` : ''} · {source.filename}
            </div>
            {source.status === 'processing' && source.progress !== undefined && (
              <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10.5px', color: 'var(--slate)' }}>
                <div className="bar bar--azure" style={{ flex: 1 }}>
                  <i style={{ width: `${source.progress * 100}%` }} />
                </div>
                <span>{Math.round((source.progress ?? 0) * 100)}%</span>
              </div>
            )}
            {source.status === 'failed' && source.error && (
              <div style={{ fontSize: '10.5px', color: 'oklch(0.45 0.12 32)', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                ⚠ {source.error.slice(0, 60)}…
              </div>
            )}
          </div>
        </div>

        <div><StatusPill status={source.status} /></div>
        <div style={{ textAlign: 'right', fontSize: '12.5px', color: 'var(--ink-2)' }}>{source.pages ?? '—'}</div>
        <div style={{ textAlign: 'right', fontSize: '12.5px', color: source.fragments > 0 ? 'var(--ink-2)' : 'var(--slate)' }}>
          {source.fragments > 0 ? source.fragments.toLocaleString() : '—'}
        </div>
        <div style={{ textAlign: 'right', fontSize: '12.5px', color: source.candidates > 0 ? 'oklch(0.45 0.12 70)' : 'var(--slate)' }}>
          {source.candidates > 0 ? source.candidates : '—'}
        </div>
        <div style={{ textAlign: 'right', fontSize: '11px', color: 'var(--slate)' }}>{source.size ?? '—'}</div>
        <div style={{ fontSize: '11px', color: 'var(--slate)' }}>{source.uploaded}</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px', opacity: hovered ? 1 : 0, transition: 'opacity 0.1s' }}
          onClick={e => e.preventDefault()}>
          <button className="btn btn--ghost btn--icon" title="Delete" onClick={e => { e.preventDefault(); onDelete() }}>
            <Trash2 size={12} color="var(--graphite)" />
          </button>
        </div>
      </div>
    </Link>
  )
}
