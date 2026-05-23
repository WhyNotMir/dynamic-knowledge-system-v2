import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export function ErrorState({ title = 'Something went wrong', message, onRetry }: ErrorStateProps) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      gap: '10px', padding: '64px 24px', textAlign: 'center',
    }}>
      <div style={{
        width: 48, height: 48, borderRadius: '50%',
        border: '1px solid oklch(0.78 0.08 32)',
        background: 'var(--rust-tint)',
        color: 'var(--rust)',
        display: 'grid', placeItems: 'center',
      }}>
        <AlertTriangle size={20} />
      </div>
      <p style={{ fontSize: '16px', color: 'oklch(0.38 0.12 32)', margin: 0, fontWeight: 500 }}>{title}</p>
      {message && <p style={{ fontSize: '13px', color: 'var(--ink-2)', margin: 0, maxWidth: '360px' }}>{message}</p>}
      {onRetry && (
        <button className="btn btn--sm" onClick={onRetry} style={{ marginTop: '4px' }}>
          Try again
        </button>
      )}
    </div>
  )
}
