import { ArticleDetailScreen } from '@/components/articles/ArticleDetailScreen'

export default function ArticleDetailPage({ params }: { params: { projectId: string; articleId: string } }) {
  return <ArticleDetailScreen projectId={params.projectId} articleId={params.articleId} />
}
