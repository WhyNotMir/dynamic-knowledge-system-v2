// ── Q&A API ───────────────────────────────────────────────────────

import type { AskQuestionRequest, Conversation, ConversationMessage, QAMessage } from '@/lib/types'
import { ApiError, apiFetch, apiUrl } from './client'

type StreamHandlers = {
  onStatus?: (status: string) => void
  onAnswer?: (message: QAMessage) => void
  onDone?: () => void
}

function askPayload(req: AskQuestionRequest) {
  return {
    question: req.question,
    conversationId: req.conversationId,
    topK: req.topK,
    maxPerArticle: req.maxPerArticle,
    minScore: req.minScore,
    minEvidenceScore: req.minEvidenceScore,
    minEvidenceBlocks: req.minEvidenceBlocks,
  }
}

export async function askQuestion(req: AskQuestionRequest): Promise<QAMessage> {
  return apiFetch<QAMessage>(`/projects/${req.projectId}/ask`, {
    method: 'POST',
    body: JSON.stringify(askPayload(req)),
  })
}

export async function askQuestionStream(
  req: AskQuestionRequest,
  handlers: StreamHandlers,
): Promise<QAMessage | null> {
  const response = await fetch(apiUrl(`/projects/${req.projectId}/ask/stream`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(askPayload(req)),
  })
  if (!response.ok) {
    throw new ApiError(`HTTP ${response.status}`, response.status)
  }
  if (!response.body) return null

  let lastAnswer: QAMessage | null = null
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''
    for (const chunk of chunks) {
      const event = parseSseEvent(chunk)
      if (!event) continue
      if (event.event === 'status') handlers.onStatus?.(String(event.data.status ?? ''))
      if (event.event === 'answer') {
        lastAnswer = event.data as unknown as QAMessage
        handlers.onAnswer?.(lastAnswer)
      }
      if (event.event === 'done') handlers.onDone?.()
      if (event.event === 'error') {
        throw new ApiError(String(event.data.detail ?? 'Q&A failed'), Number(event.data.status ?? 500))
      }
    }
  }

  return lastAnswer
}

export async function listSuggestedQuestions(projectId: string): Promise<string[]> {
  try {
    return await apiFetch<string[]>(`/projects/${projectId}/qa/suggestions`)
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return []
    throw error
  }
}

export async function listConversations(projectId: string): Promise<Conversation[]> {
  return apiFetch<Conversation[]>(`/projects/${projectId}/conversations`)
}

export async function listConversationMessages(
  projectId: string,
  conversationId: string,
): Promise<ConversationMessage[]> {
  return apiFetch<ConversationMessage[]>(
    `/projects/${projectId}/conversations/${conversationId}/messages`,
  )
}

export async function deleteConversation(
  projectId: string,
  conversationId: string,
): Promise<void> {
  await apiFetch<void>(`/projects/${projectId}/conversations/${conversationId}`, {
    method: 'DELETE',
  })
}

function parseSseEvent(chunk: string): { event: string; data: Record<string, unknown> } | null {
  const lines = chunk.split('\n')
  const event = lines.find(line => line.startsWith('event: '))?.slice(7)
  const dataLine = lines.find(line => line.startsWith('data: '))?.slice(6)
  if (!event || !dataLine) return null
  return { event, data: JSON.parse(dataLine) }
}
