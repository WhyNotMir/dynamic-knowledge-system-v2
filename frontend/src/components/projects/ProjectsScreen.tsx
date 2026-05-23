'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { Plus, Trash2, FolderOpen, BookOpen, Upload, Inbox } from 'lucide-react'
import { toast } from 'sonner'
import { listProjects, createProject, deleteProject } from '@/lib/api/projects'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import type { Project } from '@/lib/types'

export function ProjectsScreen() {
  const [showCreate, setShowCreate]       = useState(false)
  const [deleteTarget, setDeleteTarget]   = useState<Project | null>(null)
  const router = useRouter()
  const qc = useQueryClient()

  const { data: projects, isLoading, error, refetch } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  })

  const createMut = useMutation({
    mutationFn: createProject,
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      toast.success(`Project "${p.name}" created`)
      router.push(`/${p.id}/`)
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project deleted')
      setDeleteTarget(null)
    },
  })

  if (isLoading) return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <ProjectsHeader onNew={() => setShowCreate(true)} />
      <LoadingState label="Loading projects…" />
    </div>
  )

  if (error) return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }}>
      <ProjectsHeader onNew={() => setShowCreate(true)} />
      <ErrorState message="Could not load projects" onRetry={() => refetch()} />
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)' }} className="topo-bg">
      <ProjectsHeader onNew={() => setShowCreate(true)} />

      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '40px 32px 80px' }}>
        {/* coord strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: '12px', alignItems: 'center', marginBottom: '28px' }}>
          <span className="coord" style={{ fontSize: '10.5px' }}>atlas.projects</span>
          <div style={{ borderTop: '1px dashed var(--rule-strong)' }} />
          <span style={{ fontFamily: 'var(--f-mono)', fontSize: '10.5px', color: 'var(--slate)' }}>{projects?.length ?? 0} projects</span>
        </div>

        {projects?.length === 0 ? (
          <EmptyState
            icon={FolderOpen}
            title="No projects yet"
            body="Create your first project to start building a knowledge base from your documents."
            action={<button className="btn btn--primary" onClick={() => setShowCreate(true)}><Plus size={13} /> New project</button>}
          />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
            {projects?.map(p => (
              <ProjectCard
                key={p.id}
                project={p}
                onOpen={() => router.push(`/${p.id}/`)}
                onPrefetch={() => router.prefetch(`/${p.id}/`)}
                onDelete={() => setDeleteTarget(p)}
              />
            ))}
            <NewProjectCard onClick={() => setShowCreate(true)} />
          </div>
        )}
      </div>

      {showCreate && (
        <CreateProjectDialog
          onClose={() => setShowCreate(false)}
          onSubmit={req => createMut.mutate(req)}
          loading={createMut.isPending}
        />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={open => { if (!open) setDeleteTarget(null) }}
        title={`Delete "${deleteTarget?.name}"?`}
        description="All sources, articles, and candidates in this project will be permanently deleted. This cannot be undone."
        confirmLabel="Delete project"
        confirmVariant="danger"
        onConfirm={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}
        loading={deleteMut.isPending}
      />
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────

function ProjectsHeader({ onNew }: { onNew: () => void }) {
  return (
    <div style={{ borderBottom: '1px solid var(--rule)', padding: '0 32px', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--paper)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: 26, height: 26, background: 'var(--ink)', borderRadius: '2px', display: 'grid', placeItems: 'center' }}>
          <span style={{ fontFamily: 'var(--f-mono)', fontSize: '11px', fontWeight: 700, color: 'var(--paper)', letterSpacing: '0.04em' }}>At</span>
        </div>
        <span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--ink)' }}>Atlas</span>
      </div>
      <button className="btn btn--primary" onClick={onNew}>
        <Plus size={13} /> New project
      </button>
    </div>
  )
}

function ProjectCard({
  project,
  onOpen,
  onPrefetch,
  onDelete,
}: {
  project: Project
  onOpen: () => void
  onPrefetch: () => void
  onDelete: () => void
}) {
  const [hovered, setHovered] = useState(false)
  return (
    <div
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--rule)',
        borderRadius: '4px',
        padding: '20px',
        cursor: 'pointer',
        transition: 'border-color 0.12s, box-shadow 0.12s',
        borderColor: hovered ? 'var(--ink-2)' : 'var(--rule)',
        boxShadow: hovered ? '0 2px 12px oklch(0.2 0.015 260 / 0.08)' : 'none',
        position: 'relative',
      }}
      onMouseEnter={() => {
        setHovered(true)
        onPrefetch()
      }}
      onMouseLeave={() => setHovered(false)}
      onClick={onOpen}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{
          width: 40, height: 40, background: 'var(--ink)', color: 'var(--paper)',
          display: 'grid', placeItems: 'center',
          fontFamily: 'var(--f-mono)', fontSize: '13px', fontWeight: 600,
          borderRadius: '3px',
        }}>
          {project.glyph}
        </div>
        <button
          className="btn btn--ghost btn--icon"
          style={{ opacity: hovered ? 1 : 0, transition: 'opacity 0.12s' }}
          onClick={e => { e.stopPropagation(); onDelete() }}
        >
          <Trash2 size={13} color="var(--rust)" />
        </button>
      </div>

      <h3 style={{ fontSize: '16px', fontWeight: 500, margin: '0 0 4px', color: 'var(--ink)', letterSpacing: '-0.004em' }}>
        {project.name}
      </h3>
      {project.description && (
        <p style={{ fontSize: '12.5px', color: 'var(--graphite)', margin: '0 0 14px', lineHeight: 1.45 }}>
          {project.description}
        </p>
      )}

      <div style={{ display: 'flex', gap: '16px', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--rule-soft)' }}>
        <StatChip icon={Upload} value={project.sources} label="sources" />
        <StatChip icon={Inbox}  value={project.candidates} label="pending" accent={project.candidates > 0 ? 'brass' : undefined} />
        <StatChip icon={BookOpen} value={project.articles} label="articles" />
      </div>
    </div>
  )
}

function StatChip({ icon: Icon, value, label, accent }: { icon: typeof Upload; value: number; label: string; accent?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11.5px', color: accent === 'brass' ? 'oklch(0.45 0.12 70)' : 'var(--graphite)' }}>
      <Icon size={11} />
      <span style={{ fontVariantNumeric: 'tabular-nums' }}>{value}</span>
      <span>{label}</span>
    </div>
  )
}

function NewProjectCard({ onClick }: { onClick: () => void }) {
  const [hovered, setHovered] = useState(false)
  return (
    <div
      style={{
        background: 'transparent',
        border: `1px dashed ${hovered ? 'var(--ink-2)' : 'var(--rule-strong)'}`,
        borderRadius: '4px',
        padding: '20px',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        minHeight: '160px',
        color: hovered ? 'var(--ink)' : 'var(--slate)',
        transition: 'border-color 0.12s, color 0.12s',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={onClick}
    >
      <Plus size={20} />
      <span style={{ fontSize: '13px' }}>New project</span>
    </div>
  )
}

// ── Create project dialog ─────────────────────────────────────────

function CreateProjectDialog({ onClose, onSubmit, loading }: {
  onClose: () => void
  onSubmit: (req: { name: string; glyph?: string; description?: string }) => void
  loading: boolean
}) {
  const [name, setName]             = useState('')
  const [glyph, setGlyph]           = useState('')
  const [description, setDescription] = useState('')
  const autoGlyph = name.slice(0, 2).toUpperCase()

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'oklch(0.2 0.015 260 / 0.35)', zIndex: 100, display: 'grid', placeItems: 'center' }}>
      <div style={{
        background: 'var(--surface)',
        border: '1px solid var(--rule-strong)',
        borderRadius: '4px',
        padding: '28px',
        width: '440px',
        maxWidth: 'calc(100vw - 32px)',
        boxShadow: '0 20px 60px oklch(0.2 0.02 260 / 0.2)',
      }}>
        <h2 style={{ fontSize: '19px', fontWeight: 400, margin: '0 0 20px', color: 'var(--ink)', letterSpacing: '-0.008em' }}>
          New project
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <Field label="Project name" required>
            <input
              className="field-input"
              placeholder="ML Systems Atlas"
              value={name}
              onChange={e => setName(e.target.value)}
              autoFocus
              style={fieldStyle}
            />
          </Field>
          <Field label="Glyph" hint="2 characters shown in sidebar">
            <input
              className="field-input"
              placeholder={autoGlyph || 'MS'}
              maxLength={2}
              value={glyph}
              onChange={e => setGlyph(e.target.value.toUpperCase())}
              style={{ ...fieldStyle, width: '80px', fontFamily: 'var(--f-mono)', letterSpacing: '0.06em' }}
            />
          </Field>
          <Field label="Description">
            <textarea
              placeholder="Optional description…"
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={2}
              style={{ ...fieldStyle, resize: 'vertical', lineHeight: 1.5 }}
            />
          </Field>
        </div>
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '24px' }}>
          <button className="btn" onClick={onClose}>Cancel</button>
          <button
            className="btn btn--primary"
            disabled={!name.trim() || loading}
            onClick={() => onSubmit({ name: name.trim(), glyph: glyph || autoGlyph, description: description.trim() || undefined })}
          >
            {loading ? 'Creating…' : 'Create project'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Field({ label, hint, required, children }: { label: string; hint?: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
      <label style={{ fontSize: '11.5px', color: 'var(--ink-2)', fontWeight: 500 }}>
        {label}{required && <span style={{ color: 'var(--rust)', marginLeft: '2px' }}>*</span>}
      </label>
      {children}
      {hint && <span style={{ fontSize: '10.5px', color: 'var(--slate)' }}>{hint}</span>}
    </div>
  )
}

const fieldStyle: React.CSSProperties = {
  width: '100%',
  padding: '7px 10px',
  border: '1px solid var(--rule-strong)',
  borderRadius: '3px',
  background: 'var(--paper)',
  color: 'var(--ink)',
  fontSize: '13.5px',
  fontFamily: 'var(--f-sans)',
  outline: 'none',
}
