// ── Sources API ───────────────────────────────────────────────────

import type { Source, SourceFragment } from '@/lib/types'
import { formatDateTime } from '@/lib/utils'
import { apiFetch, apiUpload } from './client'

interface SourceResponse {
  id: string
  project_id: string
  filename: string
  title?: string | null
  status: Source['status']
  fragment_count?: number
  page_count?: number
  error_message?: string | null
  created_at: string
  updated_at: string
}

interface SourceFragmentResponse {
  id: string
  source_id: string
  content: string
  element_type: string
  position_index: number
  page_number?: number | null
  heading_level?: number | null
  section_path?: string | null
  meta_json?: Record<string, unknown> | null
}

function colorForId(id: string): number {
  let sum = 0
  for (let index = 0; index < id.length; index += 1) {
    sum += id.charCodeAt(index)
  }
  return sum % 10
}

function toSource(source: SourceResponse): Source {
  return {
    id: source.id,
    projectId: source.project_id,
    title: source.title ?? source.filename,
    filename: source.filename,
    uploaded: formatDateTime(source.created_at),
    status: source.status,
    pages: source.page_count ?? undefined,
    fragments: source.fragment_count ?? 0,
    candidates: 0,
    articles: 0,
    color: colorForId(source.id),
    error: source.error_message ?? undefined,
  }
}

function toFragment(fragment: SourceFragmentResponse): SourceFragment {
  return {
    id: fragment.id,
    sourceId: fragment.source_id,
    page: fragment.page_number ?? 0,
    section: fragment.section_path ?? fragment.element_type,
    text: fragment.content,
    linkedBlock: null,
  }
}

export async function listSources(projectId: string): Promise<Source[]> {
  const sources = await apiFetch<SourceResponse[]>(`/projects/${projectId}/sources`)
  return sources.map(toSource)
}

export async function getSource(projectId: string, sourceId: string): Promise<Source> {
  return toSource(await apiFetch<SourceResponse>(`/projects/${projectId}/sources/${sourceId}`))
}

export async function uploadSource(
  projectId: string,
  file: File,
  meta?: { title?: string },
): Promise<Source> {
  const fd = new FormData()
  fd.append('file', file)
  if (meta?.title) fd.append('title', meta.title)
  return toSource(await apiUpload<SourceResponse>(`/projects/${projectId}/sources`, fd))
}

export async function deleteSource(projectId: string, sourceId: string): Promise<void> {
  await apiFetch<void>(`/projects/${projectId}/sources/${sourceId}`, { method: 'DELETE' })
}

export async function retrySource(projectId: string, sourceId: string): Promise<Source> {
  return toSource(await apiFetch<SourceResponse>(`/projects/${projectId}/sources/${sourceId}/retry`, { method: 'POST' }))
}

export async function listSourceFragments(
  projectId: string,
  sourceId: string,
): Promise<SourceFragment[]> {
  const fragments = await apiFetch<SourceFragmentResponse[]>(`/projects/${projectId}/sources/${sourceId}/fragments`)
  return fragments.map(toFragment)
}
