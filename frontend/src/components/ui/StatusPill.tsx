import type { SourceStatus, CandidateStatus, ArticleStatus } from '@/lib/types'

type PillStatus = SourceStatus | CandidateStatus | ArticleStatus

interface StatusPillProps {
  status: PillStatus
  label?: string
}

const STATUS_LABELS: Record<string, string> = {
  pending:    'Pending',
  processing: 'Processing',
  done:       'Done',
  failed:     'Failed',
  proposed:   'Proposed',
  confirmed:  'Confirmed',
  rejected:   'Rejected',
  draft:      'Draft',
}

export function StatusPill({ status, label }: StatusPillProps) {
  return (
    <span className={`pill pill--${status}`}>
      <span className="dot" />
      {label ?? STATUS_LABELS[status] ?? status}
    </span>
  )
}
