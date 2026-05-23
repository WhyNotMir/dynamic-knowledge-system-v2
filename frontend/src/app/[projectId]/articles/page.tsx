import { ArticlesListScreen } from '@/components/articles/ArticlesListScreen'

export const metadata = { title: 'Articles' }

export default function ArticlesPage({ params }: { params: { projectId: string } }) {
  return <ArticlesListScreen projectId={params.projectId} />
}
