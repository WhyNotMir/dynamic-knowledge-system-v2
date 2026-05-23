// ── Projects API ──────────────────────────────────────────────────

import type { Project, CreateProjectRequest } from '@/lib/types'
import { apiFetch } from './client'

interface ProjectResponse {
  id: string
  name: string
  description?: string | null
  created_at?: string
  updated_at?: string
}

function projectGlyph(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  const initials = parts.length > 1
    ? `${parts[0][0]}${parts[1][0]}`
    : name.slice(0, 2)
  return initials.toUpperCase()
}

function toProject(project: ProjectResponse): Project {
  return {
    id: project.id,
    name: project.name,
    glyph: projectGlyph(project.name),
    description: project.description ?? undefined,
    articles: 0,
    candidates: 0,
    sources: 0,
    createdAt: project.created_at,
    updatedAt: project.updated_at,
  }
}

export async function listProjects(): Promise<Project[]> {
  const projects = await apiFetch<ProjectResponse[]>('/projects')
  return projects.map(toProject)
}

export async function getProject(id: string): Promise<Project> {
  return toProject(await apiFetch<ProjectResponse>(`/projects/${id}`))
}

export async function createProject(req: CreateProjectRequest): Promise<Project> {
  return toProject(await apiFetch<ProjectResponse>('/projects', {
    method: 'POST',
    body: JSON.stringify({
      name: req.name,
      description: req.description,
    }),
  }))
}

export async function deleteProject(id: string): Promise<void> {
  await apiFetch<void>(`/projects/${id}`, { method: 'DELETE' })
}
