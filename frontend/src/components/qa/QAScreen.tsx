'use client'

import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { Copy, ExternalLink, MessageSquare, Plus, Send, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  askQuestionStream,
  deleteConversation,
  listConversationMessages,
  listConversations,
} from '@/lib/api/qa'
import type { Citation, Conversation, ConversationMessage, QAMessage } from '@/lib/types'
import { formatConfidence } from '@/lib/utils'

interface Props {
  projectId: string
}

interface ChatTurn {
  id: string
  question: string
  response?: QAMessage
}

export function QAScreen({ projectId }: Props) {
  const queryClient = useQueryClient()
  const [question, setQuestion] = useState('')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null)
  const [showAllConversations, setShowAllConversations] = useState(false)

  const { data: conversations = [] } = useQuery({
    queryKey: ['qa-conversations', projectId],
    queryFn: () => listConversations(projectId),
  })

  const { data: selectedMessages = [] } = useQuery({
    queryKey: ['qa-messages', projectId, conversationId],
    queryFn: () => listConversationMessages(projectId, conversationId as string),
    enabled: Boolean(conversationId),
  })

  useEffect(() => {
    if (!conversationId) return
    setTurns(turnsFromMessages(selectedMessages).reverse())
  }, [conversationId, selectedMessages])

  const visibleConversations = useMemo(() => {
    const sorted = [...conversations].sort((a, b) => {
      const updated = Date.parse(b.updated_at) - Date.parse(a.updated_at)
      return updated || Date.parse(b.created_at) - Date.parse(a.created_at)
    })
    return showAllConversations ? sorted : sorted.slice(0, 5)
  }, [conversations, showAllConversations])

  const askMut = useMutation({
    mutationFn: async (value: string) => {
      setStreamingStatus('retrieving')
      return askQuestionStream(
        {
          projectId,
          question: value,
          conversationId: conversationId ?? undefined,
        },
        {
          onStatus: setStreamingStatus,
          onAnswer: answer => {
            setConversationId(answer.conversationId ?? conversationId)
            setTurns(prev => replacePendingTurn(prev, value, answer))
          },
          onDone: () => setStreamingStatus(null),
        },
      )
    },
    onError: (error: Error) => {
      setStreamingStatus(null)
      toast.error(error.message)
    },
    onSuccess: answer => {
      if (answer?.conversationId) setConversationId(answer.conversationId)
      queryClient.invalidateQueries({ queryKey: ['qa-conversations', projectId] })
      if (answer?.conversationId) {
        queryClient.invalidateQueries({ queryKey: ['qa-messages', projectId, answer.conversationId] })
      }
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteConversation(projectId, id),
    onSuccess: (_, deletedId) => {
      if (conversationId === deletedId) newChat()
      queryClient.invalidateQueries({ queryKey: ['qa-conversations', projectId] })
    },
    onError: (error: Error) => toast.error(error.message),
  })

  function submit(value = question) {
    const q = value.trim()
    if (!q || askMut.isPending) return
    setQuestion('')
    setTurns(prev => [{ id: crypto.randomUUID(), question: q }, ...prev])
    askMut.mutate(q)
  }

  function newChat() {
    setConversationId(null)
    setTurns([])
    setQuestion('')
    setStreamingStatus(null)
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'minmax(760px, 1fr) 360px',
      gap: 64,
      padding: '24px 40px 64px 32px',
    }}>
      <main>
        <div style={{ marginBottom: 20 }}>
          <span className="eyebrow">Q & A</span>
          <h1 style={{ fontSize: 28, fontWeight: 400, color: 'var(--ink)', margin: '4px 0 6px' }}>
            Ask a question
          </h1>
          <p style={{ margin: 0, fontSize: 13.5, color: 'var(--graphite)' }}>
            Grounded answers from saved articles and source citations.
          </p>
        </div>

        <div style={{ border: '1px solid var(--rule-strong)', background: 'var(--surface)', borderRadius: 3, padding: '14px 16px 0', marginBottom: 16 }}>
          <textarea
            placeholder="Ask anything about your knowledge base..."
            value={question}
            onChange={event => setQuestion(event.target.value)}
            onKeyDown={event => {
              if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) submit()
            }}
            rows={3}
            style={{ width: '100%', border: 0, outline: 0, background: 'transparent', fontFamily: 'var(--f-serif)', fontSize: 18, lineHeight: 1.45, color: 'var(--ink)', resize: 'vertical', padding: 0 }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--rule-soft)', padding: '10px 0', marginTop: 8 }}>
            <div style={{ fontSize: 11, color: 'var(--slate)', display: 'flex', alignItems: 'center', gap: 6 }}>
              {streamingStatus ? statusText(streamingStatus) : 'Searching saved article fragments'}
              <span className="kbd">⌘↵</span>
            </div>
            <button className="btn btn--primary" onClick={() => submit()} disabled={!question.trim() || askMut.isPending}>
              <Send size={12} /> Ask
            </button>
          </div>
        </div>

        {askMut.isPending && (
          <div style={{ padding: 18, border: '1px solid var(--rule)', background: 'var(--paper-2)', marginBottom: 16 }}>
            <span className="eyebrow">{statusText(streamingStatus ?? 'retrieving')}</span>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {turns.map(turn => (
            <ChatTurnView key={turn.id} turn={turn} projectId={projectId} />
          ))}
        </div>
      </main>

      <aside style={{ borderLeft: '1px solid var(--rule)', paddingLeft: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <span className="eyebrow">Conversations</span>
          <button className="btn btn--ghost btn--icon" onClick={newChat} title="New chat">
            <Plus size={14} />
          </button>
        </div>
        <button className="btn btn--primary" onClick={newChat} style={{ width: '100%', marginBottom: 16 }}>
          <MessageSquare size={13} /> New chat
        </button>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {visibleConversations.map(item => (
            <ConversationItem
              key={item.id}
              conversation={item}
              active={item.id === conversationId}
              onOpen={() => setConversationId(item.id)}
              onDelete={() => deleteMut.mutate(item.id)}
            />
          ))}
        </div>
        {conversations.length > 5 && (
          <button className="btn btn--ghost" style={{ width: '100%', marginTop: 10 }} onClick={() => setShowAllConversations(value => !value)}>
            {showAllConversations ? 'Show recent' : 'View all'}
          </button>
        )}
      </aside>
    </div>
  )
}

function ChatTurnView({ turn, projectId }: { turn: ChatTurn; projectId: string }) {
  return (
    <section style={{ borderTop: '1px solid var(--rule)', paddingTop: 16 }}>
      <p style={{ fontFamily: 'var(--f-serif)', fontSize: 19, lineHeight: 1.45, color: 'var(--ink)', margin: '0 0 16px' }}>
        {turn.question}
      </p>
      {turn.response?.answer && (
        <AnswerBlock message={turn.response} projectId={projectId} />
      )}
    </section>
  )
}

function AnswerBlock({ message, projectId }: { message: QAMessage; projectId: string }) {
  const [open, setOpen] = useState(false)
  const answer = message.answer
  if (!answer) return null
  const insufficient = message.kind === 'insufficient' || answer.insufficientContext

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{
          fontFamily: 'var(--f-mono)',
          fontSize: 11,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          border: '1px solid var(--rule)',
          background: insufficient ? 'var(--rust-tint)' : 'oklch(0.94 0.04 145)',
          color: insufficient ? 'oklch(0.45 0.12 32)' : 'var(--moss)',
          padding: '3px 7px',
        }}>
          {insufficient ? 'insufficient' : 'grounded'}
        </span>
        <span style={{ fontSize: 11, color: 'var(--slate)' }}>
          confidence {formatConfidence(answer.confidence)} · saved to conversation
        </span>
      </div>
      <p style={{ fontFamily: 'var(--f-serif)', fontSize: 21, lineHeight: 1.5, color: 'var(--ink)', margin: '0 0 14px', maxWidth: '76ch' }}>
        {answer.summary}
      </p>
      {answer.points.length > 0 && (
        <ul style={{ margin: '0 0 16px', paddingLeft: 18, color: 'var(--ink-2)' }}>
          {answer.points.map(point => (
            <li key={point} style={{ marginBottom: 6 }}>{point}</li>
          ))}
        </ul>
      )}
      {message.insufficientContext && (
        <p style={{ fontSize: 13, color: 'var(--graphite)', margin: '0 0 14px' }}>
          {message.insufficientContext.reason}
        </p>
      )}
      {answer.citations.length > 0 && (
        <div>
          <button className="btn btn--ghost" onClick={() => setOpen(value => !value)}>
            {open ? 'Hide evidence' : 'Show evidence'} · {answer.citations.length}
          </button>
          {open && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 10 }}>
              {answer.citations.map(citation => (
                <CitationCard key={citation.id} citation={citation} projectId={projectId} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function CitationCard({ citation, projectId }: { citation: Citation; projectId: string }) {
  return (
    <div style={{ border: '1px solid var(--rule)', background: 'var(--surface)', padding: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <Link href={`/${projectId}/articles/${citation.articleId}#anchor-block-${citation.block}`}>
            <span style={{ color: 'var(--ink)', borderBottom: '1px solid var(--rule-strong)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <ExternalLink size={11} /> {citation.articleTitle}
            </span>
          </Link>
          <div style={{ fontSize: 11, color: 'var(--slate)', marginTop: 4 }}>
            {citation.source} · p.{citation.page || '?'} · score {citation.score.toFixed(2)}
          </div>
          {citation.sectionPath && (
            <div style={{ fontSize: 11, color: 'var(--graphite)', marginTop: 4 }}>{citation.sectionPath}</div>
          )}
        </div>
        <button
          className="btn btn--ghost btn--icon"
          title="Copy citation"
          onClick={() => navigator.clipboard?.writeText(`${citation.source} p.${citation.page}: ${citation.quote}`)}
        >
          <Copy size={12} />
        </button>
      </div>
      <p style={{ fontFamily: 'var(--f-serif)', fontSize: 14, lineHeight: 1.5, color: 'var(--ink-2)', margin: '10px 0 0' }}>
        {citation.quote}
      </p>
    </div>
  )
}

function ConversationItem({ conversation, active, onOpen, onDelete }: {
  conversation: Conversation
  active: boolean
  onOpen: () => void
  onDelete: () => void
}) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 28px', gap: 6, alignItems: 'center' }}>
      <button
        onClick={onOpen}
        style={{
          textAlign: 'left',
          border: `1px solid ${active ? 'var(--rule-strong)' : 'var(--rule)'}`,
          borderLeft: active ? '3px solid var(--ink)' : '1px solid var(--rule)',
          background: active ? 'var(--surface)' : 'var(--paper)',
          color: 'var(--ink)',
          padding: '9px 10px',
          cursor: 'pointer',
        }}
      >
        <span style={{ display: 'block', fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {conversation.title}
        </span>
        <span style={{ display: 'block', fontSize: 10.5, color: 'var(--slate)', marginTop: 3 }}>
          {conversation.message_count} messages
        </span>
      </button>
      <button className="btn btn--ghost btn--icon" onClick={onDelete} title="Delete conversation">
        <Trash2 size={12} />
      </button>
    </div>
  )
}

function turnsFromMessages(messages: ConversationMessage[]): ChatTurn[] {
  const turns: ChatTurn[] = []
  for (let index = 0; index < messages.length; index += 1) {
    const message = messages[index]
    if (message.role !== 'user') continue
    const assistant = messages.slice(index + 1).find(item => item.role === 'assistant')
    turns.push({
      id: message.id,
      question: message.content,
      response: assistant ? responseFromAssistantMessage(assistant) : undefined,
    })
  }
  return turns
}

function responseFromAssistantMessage(message: ConversationMessage): QAMessage {
  const meta = message.meta_json ?? {}
  const citations = Array.isArray(meta.citations)
    ? meta.citations.map(normalizeStoredCitation).filter((citation): citation is Citation => citation !== null)
    : []
  const insufficient = Boolean(meta.insufficient_context)
  return {
    kind: insufficient ? 'insufficient' : 'answer',
    conversationId: message.conversation_id,
    messageId: message.id,
    answer: {
      summary: message.content,
      points: [],
      citations,
      confidence: typeof meta.confidence === 'number' ? meta.confidence : 0,
      insufficientContext: insufficient,
    },
  }
}

function normalizeStoredCitation(value: unknown): Citation | null {
  if (!value || typeof value !== 'object') return null
  const raw = value as Record<string, unknown>
  const articleId = stringValue(raw.articleId ?? raw.article_id)
  const block = stringValue(raw.block ?? raw.block_id)
  const fragment = stringValue(raw.fragment ?? raw.fragment_id)
  if (!articleId || !block || !fragment) return null

  return {
    id: stringValue(raw.id) ?? block,
    articleId,
    articleTitle: stringValue(raw.articleTitle ?? raw.article_title) ?? 'Article',
    block,
    source: stringValue(raw.source) ?? 'Source',
    page: numberValue(raw.page) ?? 0,
    sectionPath: stringValue(raw.sectionPath ?? raw.section_path),
    fragment,
    quote: stringValue(raw.quote) ?? '',
    score: numberValue(raw.score) ?? 0,
  }
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

function numberValue(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function replacePendingTurn(turns: ChatTurn[], question: string, answer: QAMessage): ChatTurn[] {
  const [first, ...rest] = turns
  if (first && first.question === question && !first.response) {
    return [{ ...first, response: answer }, ...rest]
  }
  return [{ id: answer.messageId ?? crypto.randomUUID(), question, response: answer }, ...turns]
}

function statusText(status: string): string {
  if (status === 'retrieving') return 'Retrieving evidence'
  if (status === 'answering') return 'Answering from context'
  if (status === 'insufficient') return 'Insufficient evidence'
  return status
}
