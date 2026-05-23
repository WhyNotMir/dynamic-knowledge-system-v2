// ── Q&A API ───────────────────────────────────────────────────────

import type { QAMessage, AskQuestionRequest } from '@/lib/types'
import { ApiError, apiFetch } from './client'

export async function askQuestion(req: AskQuestionRequest): Promise<QAMessage> {
  return apiFetch<QAMessage>(`/projects/${req.projectId}/qa`, {
    method: 'POST',
    body: JSON.stringify({ question: req.question, articleId: req.articleId }),
  })
}

export async function listSuggestedQuestions(projectId: string): Promise<string[]> {
  try {
    return await apiFetch<string[]>(`/projects/${projectId}/qa/suggestions`)
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return []
    throw error
  }
}
