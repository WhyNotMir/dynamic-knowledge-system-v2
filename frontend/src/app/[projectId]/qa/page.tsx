import { QAScreen } from '@/components/qa/QAScreen'

export const metadata = { title: 'Q & A' }

export default function QAPage({ params }: { params: { projectId: string } }) {
  return <QAScreen projectId={params.projectId} />
}
