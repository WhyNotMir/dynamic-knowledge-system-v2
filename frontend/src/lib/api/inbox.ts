// ── Inbox API ─────────────────────────────────────────────────────

import type { ArticleCandidate, UpdateCandidateRequest } from '@/lib/types'
import { apiFetch } from './client'

interface CandidateFragmentResponse {
  fragment_id: string
  position_index: number
  content: string
}

interface ArticleCandidateResponse {
  id: string
  proposal_id: string
  title: string
  source_section_path: string
  status: ArticleCandidate['status']
  suggested_order: number
  created_at: string
  fragments?: CandidateFragmentResponse[]
}

interface StructureProposalResponse {
  id: string
  project_id: string
  status: string
  candidate_count: number
  created_at: string
  updated_at: string
  candidates: ArticleCandidateResponse[]
}

interface ConfirmAllResponse {
  updated_count: number
}

function toCandidate(projectId: string, candidate: ArticleCandidateResponse): ArticleCandidate {
  const fragments = candidate.fragments ?? []
  return {
    id: candidate.id,
    projectId,
    proposalId: candidate.proposal_id,
    title: candidate.title,
    sourcePath: candidate.source_section_path,
    fragments: fragments.length,
    status: candidate.status,
    preview: fragments.map(fragment => fragment.content).join('\n\n'),
  }
}

export async function listInboxItems(projectId: string): Promise<ArticleCandidate[]> {
  const proposals = await apiFetch<StructureProposalResponse[]>(`/projects/${projectId}/structure/proposals`)
  return proposals.flatMap(proposal =>
    proposal.candidates.map(candidate => toCandidate(projectId, candidate)),
  )
}

export async function proposeStructure(projectId: string): Promise<ArticleCandidate[]> {
  const proposal = await apiFetch<StructureProposalResponse>(
    `/projects/${projectId}/structure/propose`,
    { method: 'POST' },
  )
  return proposal.candidates.map(candidate => toCandidate(projectId, candidate))
}

export async function getStructureProposal(
  projectId: string,
  proposalId: string,
): Promise<StructureProposalResponse> {
  return apiFetch<StructureProposalResponse>(`/projects/${projectId}/structure/proposals/${proposalId}`)
}

export async function updateCandidate(
  projectId: string,
  candidateId: string,
  req: UpdateCandidateRequest,
): Promise<ArticleCandidate> {
  const candidate = await apiFetch<ArticleCandidateResponse>(
    `/projects/${projectId}/structure/candidates/${candidateId}`,
    { method: 'PATCH', body: JSON.stringify(req) },
  )
  return toCandidate(projectId, candidate)
}

export async function confirmAllCandidates(
  projectId: string,
  proposalId: string,
): Promise<ConfirmAllResponse> {
  return apiFetch<ConfirmAllResponse>(
    `/projects/${projectId}/structure/proposals/${proposalId}/confirm-all`,
    { method: 'POST' },
  )
}

export async function buildArticles(
  projectId: string,
  proposalId: string,
): Promise<unknown> {
  return apiFetch(
    `/projects/${projectId}/articles/build`,
    { method: 'POST', body: JSON.stringify({ proposal_id: proposalId }) },
  )
}
