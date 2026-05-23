import { SourcesScreen } from '@/components/sources/SourcesScreen'

export const metadata = { title: 'Sources' }

export default function SourcesPage({ params }: { params: { projectId: string } }) {
  return <SourcesScreen projectId={params.projectId} />
}
