import type { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  body?: string
  action?: React.ReactNode
}

export function EmptyState({ icon: Icon, title, body, action }: EmptyStateProps) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '10px',
      padding: '64px 24px',
      color: 'var(--graphite)',
      textAlign: 'center',
    }}>
      <div style={{
        width: 56, height: 56,
        display: 'grid', placeItems: 'center',
        border: '1px solid var(--rule)',
        borderRadius: '50%',
        color: 'var(--slate)',
        background: 'var(--surface)',
      }}>
        <Icon size={22} />
      </div>
      <p style={{ fontSize: '18px', color: 'var(--ink)', margin: 0 }}>{title}</p>
      {body && <p style={{ maxWidth: '360px', fontSize: '13px', lineHeight: 1.5, margin: 0 }}>{body}</p>}
      {action}
    </div>
  )
}
