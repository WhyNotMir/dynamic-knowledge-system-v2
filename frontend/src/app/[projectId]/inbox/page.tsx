import { InboxScreen } from '@/components/inbox/InboxScreen'

export const metadata = { title: 'Inbox' }

export default function InboxPage({ params }: { params: { projectId: string } }) {
  return <InboxScreen projectId={params.projectId} />
}
