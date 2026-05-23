import { SourceDetailScreen } from '@/components/sources/SourceDetailScreen'

export const metadata = { title: 'Source detail' }

export default function SourceDetailPage({ params }: { params: { projectId: string; sourceId: string } }) {
  return <SourceDetailScreen projectId={params.projectId} sourceId={params.sourceId} />
}
