'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { CheckCircle, X, Edit2, CheckCheck, Hammer, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import { listInboxItems, updateCandidate, confirmAllCandidates, buildArticles, proposeStructure } from '@/lib/api/inbox'
import { StatusPill } from '@/components/ui/StatusPill'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { formatConfidence } from '@/lib/utils'
import type { ArticleCandidate, CandidateStatus } from '@/lib/types'

type InboxFilter = 'all' | CandidateStatus

interface InboxScreenProps { projectId: string }

export function InboxScreen({ projectId }: InboxScreenProps) {
  const [selected, setSelected]     = useState<ArticleCandidate | null>(null)
  const [filter, setFilter]         = useState<InboxFilter>('all')
  const [renaming, setRenaming]     = useState<string | null>(null)
  const [renameVal, setRenameVal]   = useState('')
  const qc = useQueryClient()
  const router = useRouter()

  const { data: candidates, isLoading, error, refetch } = useQuery({
    queryKey: ['inbox', projectId],
    queryFn: () => listInboxItems(projectId),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, req }: { id: string; req: Parameters<typeof updateCandidate>[2] }) =>
      updateCandidate(projectId, id, req),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: ['inbox', projectId] })
      if (selected?.id === updated.id) setSelected(updated)
      toast.success(`Candidate "${updated.title}" ${updated.status}`)
    },
  })

  const proposeMut = useMutation({
    mutationFn: () => proposeStructure(projectId),
    onSuccess: candidates => {
      qc.invalidateQueries({ queryKey: ['inbox', projectId] })
      toast.success(`Created ${candidates.length} candidate${candidates.length === 1 ? '' : 's'}`)
    },
    onError: (error: Error) => toast.error(error.message),
  })

  const confirmAllMut = useMutation({
    mutationFn: (proposalId: string) => confirmAllCandidates(projectId, proposalId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inbox', projectId] })
      toast.success('All proposed candidates confirmed')
    },
  })

  const buildMut = useMutation({
    mutationFn: (proposalId: string) => buildArticles(projectId, proposalId),
    onSuccess: () => {
      toast.success('Articles built')
      router.push(`/${projectId}/articles`)
    },
  })

  const filtered = (candidates ?? []).filter(c => filter === 'all' || c.status === filter)
  const counts: Record<string, number> = { all: candidates?.length ?? 0 }
  candidates?.forEach(c => { counts[c.status] = (counts[c.status] ?? 0) + 1 })
  const proposedCount = counts.proposed ?? 0
  const confirmedCount = counts.confirmed ?? 0
  const proposalIds = Array.from(new Set((candidates ?? []).map(c => c.proposalId)))
  const activeProposalId = proposalIds.length === 1 ? proposalIds[0] : null

  if (isLoading) return <div style={{ padding: '24px 32px' }}><LoadingState label="Loading inbox…" /></div>
  if (error) return <div style={{ padding: '24px 32px' }}><ErrorState onRetry={() => refetch()} /></div>

  return (
    <div style={{ padding: '24px 32px 64px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: '24px', marginBottom: '18px' }}>
        <div>
          <span className="eyebrow">Inbox</span>
          <h1 style={{ fontSize: '28px', lineHeight: 1.15, fontWeight: 400, letterSpacing: '-0.012em', color: 'var(--ink)', margin: '4px 0 6px' }}>
            Review desk
          </h1>
          <p style={{ margin: 0, fontSize: '13.5px', color: 'var(--graphite)' }}>
            {proposedCount} candidate{proposedCount !== 1 ? 's' : ''} proposed · {confirmedCount} confirmed
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
          {counts.all === 0 && (
            <button className="btn" onClick={() => proposeMut.mutate()} disabled={proposeMut.isPending}>
              <Hammer size={13} /> {proposeMut.isPending ? 'Proposing…' : 'Propose structure'}
            </button>
          )}
          {proposedCount > 0 && (
            <button className="btn" onClick={() => activeProposalId && confirmAllMut.mutate(activeProposalId)} disabled={confirmAllMut.isPending || !activeProposalId}>
              <CheckCheck size={13} /> {confirmAllMut.isPending ? 'Confirming…' : `Confirm all (${proposedCount})`}
            </button>
          )}
          {confirmedCount > 0 && (
            <button className="btn btn--moss" onClick={() => activeProposalId && buildMut.mutate(activeProposalId)} disabled={buildMut.isPending || !activeProposalId}>
              <Hammer size={13} /> {buildMut.isPending ? 'Building…' : `Build ${confirmedCount} article${confirmedCount !== 1 ? 's' : ''}`}
            </button>
          )}
        </div>
      </div>

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: '6px', borderBottom: '1px solid var(--rule)', paddingBottom: '10px', marginBottom: '0' }}>
        {(['all', 'proposed', 'confirmed', 'rejected'] as InboxFilter[]).map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              appearance: 'none', border: 0, padding: '5px 10px', borderRadius: '3px',
              fontSize: '12px', background: filter === s ? 'var(--ink)' : 'transparent',
              color: filter === s ? 'var(--paper)' : 'var(--ink-2)',
              cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px',
              fontFamily: 'var(--f-sans)',
            }}
          >
            {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            <span style={{ fontSize: '10.5px', color: filter === s ? 'oklch(0.95 0.01 80)' : 'var(--slate)' }}>{counts[s] ?? 0}</span>
          </button>
        ))}
      </div>

      {/* Grid: list + preview pane */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={CheckCircle}
          title="Inbox empty"
          body="No structure proposal has been created for this project yet."
          action={
            <button className="btn btn--primary" onClick={() => proposeMut.mutate()} disabled={proposeMut.isPending}>
              <Hammer size={13} /> {proposeMut.isPending ? 'Proposing…' : 'Propose structure'}
            </button>
          }
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 380px', gap: '28px', alignItems: 'start', marginTop: '0' }}>
          {/* Candidate list */}
          <div>
            {filtered.map(cand => (
              <CandidateRow
                key={cand.id}
                candidate={cand}
                isSelected={selected?.id === cand.id}
                isRenaming={renaming === cand.id}
                renameVal={renameVal}
                onSelect={() => { setSelected(cand); setRenaming(null) }}
                onConfirm={() => updateMut.mutate({ id: cand.id, req: { status: 'confirmed' } })}
                onReject={() => updateMut.mutate({ id: cand.id, req: { status: 'rejected' } })}
                onStartRename={() => { setRenaming(cand.id); setRenameVal(cand.title) }}
                onRenameChange={setRenameVal}
                onRenameSubmit={() => {
                  if (renameVal.trim()) {
                    updateMut.mutate({ id: cand.id, req: { title: renameVal.trim() } })
                  }
                  setRenaming(null)
                }}
                onRenameCancel={() => setRenaming(null)}
              />
            ))}
          </div>

          {/* Preview pane */}
          <div style={{ position: 'sticky', top: '16px' }}>
            {selected ? (
              <CandidatePreview
                candidate={selected}
                onConfirm={() => updateMut.mutate({ id: selected.id, req: { status: 'confirmed' } })}
                onReject={() => updateMut.mutate({ id: selected.id, req: { status: 'rejected' } })}
                loading={updateMut.isPending}
              />
            ) : (
              <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--slate)', background: 'var(--surface)', border: '1px solid var(--rule)', borderRadius: '3px' }}>
                <p style={{ fontSize: '13px', margin: 0 }}>Select a candidate to preview it.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Candidate row ─────────────────────────────────────────────────

interface CandidateRowProps {
  candidate: ArticleCandidate
  isSelected: boolean
  isRenaming: boolean
  renameVal: string
  onSelect: () => void
  onConfirm: () => void
  onReject: () => void
  onStartRename: () => void
  onRenameChange: (v: string) => void
  onRenameSubmit: () => void
  onRenameCancel: () => void
}

function CandidateRow({ candidate, isSelected, isRenaming, renameVal, onSelect, onConfirm, onReject, onStartRename, onRenameChange, onRenameSubmit, onRenameCancel }: CandidateRowProps) {
  const markerColor = {
    proposed:  { bg: 'var(--brass-tint)', border: 'var(--brass)' },
    confirmed: { bg: 'var(--moss)',       border: 'var(--moss)' },
    rejected:  { bg: 'transparent',       border: 'oklch(0.65 0.12 32)' },
  }[candidate.status]

  return (
    <div
      style={{
        display: 'grid', gridTemplateColumns: '28px minmax(0, 1fr) auto',
        gap: '16px', padding: '16px 12px 16px 0',
        borderBottom: '1px solid var(--rule)',
        cursor: 'pointer', alignItems: 'flex-start',
        background: isSelected ? 'var(--surface)' : 'transparent',
        boxShadow: isSelected ? 'inset 2px 0 0 var(--ink)' : 'none',
        opacity: candidate.status === 'rejected' ? 0.7 : 1,
        transition: 'background 0.1s',
      }}
      onClick={onSelect}
    >
      {/* Marker */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: '8px' }}>
        <div style={{
          width: 9, height: 9,
          border: `1px solid ${markerColor.border}`,
          background: markerColor.bg,
          transform: 'rotate(45deg)',
        }} />
      </div>

      <div>
        {/* Title */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '4px', flexWrap: 'wrap' }}>
          {isRenaming ? (
            <input
              value={renameVal}
              onChange={e => onRenameChange(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') onRenameSubmit(); if (e.key === 'Escape') onRenameCancel() }}
              onClick={e => e.stopPropagation()}
              autoFocus
              style={{ fontSize: '16px', fontWeight: 400, border: '1px solid var(--ink)', borderRadius: '2px', padding: '1px 6px', background: 'var(--paper)', fontFamily: 'var(--f-sans)', color: 'var(--ink)', outline: 'none' }}
            />
          ) : (
            <h3 style={{
              fontSize: '16px', fontWeight: 400, margin: 0, color: 'var(--ink)', letterSpacing: '-0.005em',
              textDecoration: candidate.status === 'rejected' ? 'line-through' : 'none',
              textDecorationColor: 'oklch(0.7 0.08 32)',
            }}>
              {candidate.title}
            </h3>
          )}
          <span style={{ fontSize: '11px', color: 'var(--slate)' }}>{candidate.sourcePath}</span>
        </div>

        {/* Meta */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--graphite)', flexWrap: 'wrap' }}>
          <span style={{ color: 'var(--ink-2)' }}>{candidate.fragments} fragments</span>
          <span style={{ color: 'var(--whisper)' }}>·</span>
          <StatusPill status={candidate.status} />
          <span style={{ color: 'var(--whisper)' }}>·</span>
          <span style={{
            color: candidate.confidence === undefined
              ? 'var(--slate)'
              : candidate.confidence >= 0.85 ? 'var(--moss)' : candidate.confidence >= 0.70 ? 'oklch(0.45 0.13 70)' : 'oklch(0.45 0.12 32)'
          }}>
            {candidate.confidence !== undefined ? `${formatConfidence(candidate.confidence)} confidence` : 'confidence unavailable'}
          </span>
          {candidate.rejectReason && (
            <>
              <span style={{ color: 'var(--whisper)' }}>·</span>
              <span style={{ color: 'oklch(0.45 0.12 32)', fontSize: '10.5px' }}>{candidate.rejectReason}</span>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '4px', alignItems: 'center', paddingTop: '4px' }} onClick={e => e.stopPropagation()}>
        {candidate.status === 'proposed' && (
          <>
            <button className="btn btn--sm btn--ghost" title="Rename" onClick={onStartRename}>
              <Edit2 size={11} />
            </button>
            <button className="btn btn--sm btn--ghost" title="Reject" onClick={onReject} style={{ color: 'oklch(0.45 0.12 32)' }}>
              <X size={12} />
            </button>
            <button className="btn btn--sm btn--moss" title="Confirm" onClick={onConfirm}>
              <CheckCircle size={12} /> Confirm
            </button>
          </>
        )}
        {candidate.status === 'confirmed' && (
          <button className="btn btn--sm btn--ghost" title="Undo" onClick={onReject} style={{ color: 'var(--slate)' }}>
            Undo
          </button>
        )}
        {candidate.status === 'rejected' && (
          <button className="btn btn--sm btn--ghost" title="Restore" onClick={onConfirm} style={{ color: 'var(--slate)' }}>
            Restore
          </button>
        )}
      </div>
    </div>
  )
}

// ── Preview pane ──────────────────────────────────────────────────

function CandidatePreview({ candidate, onConfirm, onReject, loading }: {
  candidate: ArticleCandidate
  onConfirm: () => void
  onReject: () => void
  loading: boolean
}) {
  return (
    <div style={{ padding: '18px 18px 16px', background: 'var(--surface)', border: '1px solid var(--rule)', borderRadius: '3px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', paddingBottom: '10px', borderBottom: '1px solid var(--rule)' }}>
        <StatusPill status={candidate.status} />
        {candidate.confidence !== undefined && (
          <span style={{ fontSize: '10.5px', color: 'var(--slate)' }}>{formatConfidence(candidate.confidence)} confidence</span>
        )}
      </div>

      <h2 style={{ fontSize: '19px', lineHeight: 1.2, margin: '0 0 4px', fontWeight: 400, color: 'var(--ink)', letterSpacing: '-0.008em' }}>
        {candidate.title}
      </h2>
      <div style={{ fontSize: '11px', color: 'var(--slate)', marginBottom: '14px' }}>{candidate.sourcePath}</div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', borderTop: '1px solid var(--rule-soft)', borderBottom: '1px solid var(--rule-soft)', padding: '10px 0', gap: '6px', marginBottom: '12px' }}>
        {[
          { k: 'Fragments', v: candidate.fragments },
          { k: 'Status',    v: <StatusPill status={candidate.status} /> },
          { k: 'Confidence',v: candidate.confidence !== undefined ? formatConfidence(candidate.confidence) : '—' },
        ].map(({ k, v }) => (
          <div key={k} style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '10px', color: 'var(--slate)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{k}</span>
            <span style={{ fontSize: '14px', color: 'var(--ink)', marginTop: '2px' }}>{v}</span>
          </div>
        ))}
      </div>

      <p style={{ fontSize: '13px', color: 'var(--ink-2)', lineHeight: 1.55, margin: '0 0 14px', fontFamily: 'var(--f-serif)' }}>
        {candidate.preview}
      </p>

      {candidate.rejectReason && (
        <div style={{ fontSize: '11.5px', color: 'oklch(0.45 0.12 32)', background: 'var(--rust-tint)', padding: '8px 12px', borderRadius: '2px', marginBottom: '12px' }}>
          Rejected: {candidate.rejectReason}
        </div>
      )}

      <div style={{ marginTop: 'auto', borderTop: '1px solid var(--rule)', paddingTop: '14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {candidate.status !== 'confirmed' && (
          <button className="btn btn--moss" style={{ justifyContent: 'center' }} onClick={onConfirm} disabled={loading}>
            <CheckCircle size={13} /> Confirm candidate
          </button>
        )}
        {candidate.status !== 'rejected' && (
          <button className="btn btn--rust" style={{ justifyContent: 'center' }} onClick={onReject} disabled={loading}>
            <X size={13} /> Reject
          </button>
        )}
        {candidate.status === 'confirmed' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center', fontSize: '11px', color: 'var(--moss)' }}>
            <CheckCircle size={12} /> Confirmed — will be built into an article
          </div>
        )}
      </div>
    </div>
  )
}
