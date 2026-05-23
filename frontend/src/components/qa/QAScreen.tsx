'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import Link from 'next/link'
import { Send, AlertTriangle, ExternalLink, Copy } from 'lucide-react'
import { toast } from 'sonner'
import { askQuestion, listSuggestedQuestions } from '@/lib/api/qa'
import { LoadingDots } from '@/components/ui/LoadingState'
import type { QAMessage, Citation } from '@/lib/types'
import { formatConfidence } from '@/lib/utils'

interface Props { projectId: string }

export function QAScreen({ projectId }: Props) {
  const [question, setQuestion]     = useState('')
  const [messages, setMessages]     = useState<QAMessage[]>([])
  const [activeCite, setActiveCite] = useState<string | null>(null)

  const { data: suggested } = useQuery({
    queryKey: ['qa-suggestions', projectId],
    queryFn: () => listSuggestedQuestions(projectId),
  })

  const askMut = useMutation({
    mutationFn: (q: string) => askQuestion({ projectId, question: q }),
    onSuccess: (answer) => {
      setMessages(prev => [...prev, answer])
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const handleSubmit = () => {
    const q = question.trim()
    if (!q || askMut.isPending) return
    setMessages(prev => [...prev, { kind: 'ask', text: q }])
    setQuestion('')
    askMut.mutate(q)
  }

  const handleSuggested = (q: string) => {
    setMessages(prev => [...prev, { kind: 'ask', text: q }])
    askMut.mutate(q)
  }

  const lastAnswer = messages.findLast(m => m.kind === 'answer')

  return (
    <div style={{ padding: '24px 32px 64px', maxWidth: '860px' }}>
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <span className="eyebrow">Q & A</span>
        <h1 style={{ fontSize: '28px', fontWeight: 400, letterSpacing: '-0.012em', color: 'var(--ink)', margin: '4px 0 6px' }}>
          Ask a question
        </h1>
        <p style={{ margin: 0, fontSize: '13.5px', color: 'var(--graphite)' }}>
          Get cited answers drawn from your knowledge base.
        </p>
      </div>

      {/* Question input */}
      <div style={{
        border: '1px solid var(--rule-strong)',
        background: 'var(--surface)',
        borderRadius: '3px',
        padding: '14px 16px 0',
        marginBottom: '16px',
      }}>
        <textarea
          placeholder="Ask anything about your documents…"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit() }}
          rows={2}
          style={{
            width: '100%', border: 0, outline: 0,
            background: 'transparent',
            fontFamily: 'var(--f-serif)',
            fontSize: '18px', lineHeight: 1.45,
            color: 'var(--ink)', resize: 'vertical',
            padding: 0, minHeight: '30px',
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--rule-soft)', padding: '10px 0', marginTop: '8px' }}>
          <div style={{ fontSize: '11px', color: 'var(--slate)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            Searching all articles in this project
            <span className="kbd">⌘↵</span>
          </div>
          <button
            className="btn btn--primary"
            onClick={handleSubmit}
            disabled={!question.trim() || askMut.isPending}
          >
            <Send size={12} /> Ask
          </button>
        </div>
      </div>

      {/* Suggested questions (shown only when no history) */}
      {messages.length === 0 && suggested && suggested.length > 0 && (
        <div style={{ marginBottom: '28px' }}>
          <div style={{ fontSize: '11px', color: 'var(--slate)', marginBottom: '6px' }}>Suggested questions</div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {suggested.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSuggested(q)}
                style={{
                  appearance: 'none',
                  border: '1px solid var(--rule)',
                  background: 'var(--surface)',
                  padding: '6px 10px',
                  borderRadius: '3px',
                  font: 'inherit',
                  fontFamily: 'var(--f-serif)',
                  fontSize: '12px',
                  color: 'var(--ink-2)',
                  cursor: 'pointer',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--ink-2)'; (e.currentTarget as HTMLElement).style.color = 'var(--ink)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--rule)'; (e.currentTarget as HTMLElement).style.color = 'var(--ink-2)' }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Thinking indicator */}
      {askMut.isPending && (
        <div style={{ padding: '24px', background: 'var(--paper-2)', border: '1px solid var(--rule)', borderRadius: '3px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {['Searching fragments…', 'Composing answer…', 'Gathering citations…'].map((step, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                fontSize: '12px', color: 'var(--graphite)',
                fontFamily: 'var(--f-mono)',
                animation: `thinkfade 1.5s ease-in-out ${i * 0.3}s infinite`,
              }}>
                <LoadingDots />
                {step}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conversation messages */}
      {messages.map((msg, i) => {
        if (msg.kind === 'ask') return (
          <div key={i} style={{ borderBottom: '1px dashed var(--rule)', paddingBottom: '16px', marginBottom: '16px' }}>
            <p style={{ fontFamily: 'var(--f-serif)', fontSize: '19px', lineHeight: 1.4, color: 'var(--ink)', margin: 0, letterSpacing: '-0.007em' }}>
              {msg.text}
            </p>
          </div>
        )

        if (msg.kind === 'answer' && msg.answer) return (
          <AnswerBlock
            key={i}
            answer={msg.answer}
            activeCite={activeCite}
            onCiteClick={setActiveCite}
            projectId={projectId}
          />
        )

        if (msg.kind === 'insufficient') return (
          <InsufficientContextBlock key={i} />
        )

        return null
      })}
    </div>
  )
}

// ── Answer block ──────────────────────────────────────────────────

function AnswerBlock({ answer, activeCite, onCiteClick, projectId }: {
  answer: NonNullable<QAMessage['answer']>
  activeCite: string | null
  onCiteClick: (id: string | null) => void
  projectId: string
}) {
  return (
    <div style={{ paddingTop: '20px', borderTop: '1px solid var(--rule)' }}>
      {/* Confidence */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <span className="eyebrow">Answer</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10.5px', color: 'var(--graphite)' }}>
          <span>Confidence</span>
          <div style={{ display: 'inline-block', width: '80px', height: '4px', background: 'var(--rule-soft)', borderRadius: '1px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${answer.confidence * 100}%`, background: 'var(--moss)' }} />
          </div>
          <span>{formatConfidence(answer.confidence)}</span>
        </div>
      </div>

      {/* Summary */}
      <p style={{ fontFamily: 'var(--f-serif)', fontSize: '22px', lineHeight: 1.45, color: 'var(--ink)', margin: '0 0 24px', maxWidth: '64ch', letterSpacing: '-0.008em' }}>
        {answer.summary}
      </p>

      {/* Points */}
      <ul style={{ listStyle: 'none', margin: '0 0 24px', padding: 0, display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '70ch' }}>
        {answer.points.map((point, i) => {
          const citeId = answer.citations[i]?.id
          return (
            <li key={i} style={{ display: 'grid', gridTemplateColumns: '32px 1fr', gap: '12px', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '11px', color: 'var(--slate)', paddingTop: '4px', letterSpacing: '0.06em', borderTop: '1px solid var(--rule)', fontFamily: 'var(--f-mono)' }}>
                {String(i + 1).padStart(2, '0')}
              </span>
              <p style={{ fontFamily: 'var(--f-serif)', fontSize: '14.5px', lineHeight: 1.55, color: 'var(--ink-2)', margin: 0, paddingTop: '4px', borderTop: '1px solid var(--rule)' }}>
                {point}
                {citeId && (
                  <button
                    onClick={() => onCiteClick(activeCite === citeId ? null : citeId)}
                    style={{
                      display: 'inline-flex', appearance: 'none', border: 0,
                      background: 'var(--highlight)', padding: '0 4px',
                      marginLeft: '4px', borderRadius: '2px',
                      fontFamily: 'var(--f-mono)', fontSize: '10.5px',
                      color: activeCite === citeId ? 'var(--ink)' : 'oklch(0.4 0.12 70)',
                      cursor: 'pointer', verticalAlign: '1px', lineHeight: 1.4,
                    }}
                  >
                    {i + 1}
                  </button>
                )}
              </p>
            </li>
          )
        })}
      </ul>

      {/* Citations */}
      {answer.citations.length > 0 && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '10px' }}>
            <span className="eyebrow">Citations</span>
            <span style={{ fontSize: '10.5px', color: 'var(--slate)' }}>{answer.citations.length} source{answer.citations.length !== 1 ? 's' : ''}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {answer.citations.map((cite, i) => (
              <CitationCard
                key={cite.id}
                citation={cite}
                index={i + 1}
                isActive={activeCite === cite.id}
                onClick={() => onCiteClick(activeCite === cite.id ? null : cite.id)}
                projectId={projectId}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Citation card ─────────────────────────────────────────────────

function CitationCard({ citation, index, isActive, onClick, projectId }: {
  citation: Citation
  index: number
  isActive: boolean
  onClick: () => void
  projectId: string
}) {
  return (
    <div
      style={{
        display: 'grid', gridTemplateColumns: '36px minmax(0, 1fr) 32px',
        gap: '14px', padding: '14px',
        border: `1px solid ${isActive ? 'var(--highlight-rule)' : 'var(--rule)'}`,
        background: isActive ? 'var(--highlight)' : 'var(--surface)',
        borderRadius: '3px', cursor: 'pointer',
        alignItems: 'flex-start',
        transition: 'background 0.12s, border-color 0.12s',
      }}
      onClick={onClick}
      onMouseEnter={e => { if (!isActive) (e.currentTarget as HTMLElement).style.borderColor = 'var(--ink-2)' }}
      onMouseLeave={e => { if (!isActive) (e.currentTarget as HTMLElement).style.borderColor = 'var(--rule)' }}
    >
      <span style={{ fontFamily: 'var(--f-mono)', fontSize: '11px', color: 'var(--brass)', paddingTop: '2px' }}>
        [{index}]
      </span>
      <div>
        <p style={{ fontStyle: 'italic', fontSize: '14px', lineHeight: 1.5, color: 'var(--ink)', marginBottom: '8px', margin: '0 0 8px' }}>
          "{citation.quote}"
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
          <Link href={`/${projectId}/articles/${citation.articleId}`}>
            <span style={{ color: 'var(--ink)', cursor: 'pointer', borderBottom: '1px solid var(--rule-strong)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <ExternalLink size={10} /> {citation.articleTitle}
            </span>
          </Link>
          <span style={{ color: 'var(--whisper)' }}>·</span>
          <span style={{ color: 'var(--graphite)' }}>{citation.source}</span>
          {citation.page && (
            <>
              <span style={{ color: 'var(--whisper)' }}>·</span>
              <span style={{ color: 'var(--graphite)' }}>p.{citation.page}</span>
            </>
          )}
          <span style={{ color: 'var(--whisper)' }}>·</span>
          <span style={{ fontFamily: 'var(--f-mono)', fontSize: '10px', color: 'var(--brass)' }}>{citation.fragment}</span>
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button
          className="btn btn--ghost btn--icon"
          onClick={e => { e.stopPropagation(); navigator.clipboard?.writeText(`${citation.source} p.${citation.page} [${citation.fragment}]: "${citation.quote}"`) }}
          title="Copy citation"
        >
          <Copy size={12} />
        </button>
      </div>
    </div>
  )
}

// ── Insufficient context block ────────────────────────────────────

function InsufficientContextBlock() {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '36px 1fr',
      gap: '16px', padding: '20px 22px',
      background: 'var(--rust-tint)',
      border: '1px solid oklch(0.80 0.07 32)',
      borderTop: '4px solid oklch(0.55 0.13 32)',
      borderRadius: '0 0 3px 3px',
      marginTop: '20px',
    }}>
      <div style={{ width: 30, height: 30, borderRadius: '50%', background: 'var(--surface)', border: '1px solid oklch(0.75 0.10 32)', display: 'grid', placeItems: 'center', color: 'oklch(0.45 0.12 32)' }}>
        <AlertTriangle size={14} />
      </div>
      <div>
        <h3 style={{ fontSize: '18px', margin: '0 0 8px', color: 'oklch(0.38 0.12 32)', fontWeight: 400 }}>Insufficient context</h3>
        <p style={{ fontSize: '13.5px', color: 'var(--ink-2)', lineHeight: 1.55, margin: '0 0 16px', maxWidth: '70ch' }}>
          The knowledge base doesn't have enough information to answer this question confidently. Try uploading more relevant sources or rephrasing the question.
        </p>
        <div style={{ paddingTop: '12px', borderTop: '1px dashed oklch(0.80 0.06 32)' }}>
          <div style={{ fontSize: '11px', color: 'var(--slate)', marginBottom: '6px' }}>You might try</div>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px' }}>
            <li>Upload more sources covering this topic</li>
            <li>Check if relevant sources are still processing</li>
            <li>Try a more specific question</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
