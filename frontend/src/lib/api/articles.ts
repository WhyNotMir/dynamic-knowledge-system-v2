// ── Articles API ──────────────────────────────────────────────────

import type { ArticleSummary, ArticleDetail } from '@/lib/types'
import { formatDateTime } from '@/lib/utils'
import { apiFetch } from './client'

interface ArticleResponse {
  id: string
  project_id: string
  candidate_id: string
  title: string
  status: ArticleSummary['status']
  created_at: string
  updated_at: string
}

interface ArticleBlockResponse {
  id: string
  article_id: string
  fragment_id: string
  source_title?: string | null
  source_filename: string
  content: string
  element_type: string
  position_index: number
  page_number?: number | null
  heading_level?: number | null
  section_path?: string | null
  meta_json?: Record<string, unknown> | null
  created_at: string
}

interface ArticleDetailResponse extends ArticleResponse {
  blocks: ArticleBlockResponse[]
}

function toSummary(article: ArticleResponse, blocks = 0): ArticleSummary {
  return {
    id: article.id,
    title: article.title,
    topic: '',
    blocks,
    sources: 0,
    status: article.status,
    updated: formatDateTime(article.updated_at),
    citations: 0,
    excerpt: '',
  }
}

function blockType(block: ArticleBlockResponse): 'h1' | 'h2' | 'p' | 'eq' {
  if (block.element_type === 'heading' && block.heading_level === 1) return 'h1'
  if (block.element_type === 'heading') return 'h2'
  return 'p'
}

function anchorFor(block: ArticleBlockResponse): string {
  return `block-${block.id}`
}

function toDetail(article: ArticleDetailResponse): ArticleDetail {
  const blocks = article.blocks.map(block => ({
    id: block.id,
    type: blockType(block),
    text: block.content,
    anchor: anchorFor(block),
    provenance: {
      source: block.source_title ?? block.source_filename,
      page: block.page_number ?? null,
      fragment: block.fragment_id,
      section: block.section_path ?? '',
    },
  }))

  return {
    ...toSummary(article, blocks.length),
    topic: [],
    outline: blocks
      .filter(block => block.type === 'h1' || block.type === 'h2')
      .map(block => ({
        id: block.anchor ?? block.id,
        label: block.text,
        level: block.type === 'h1' ? 1 : 2,
      })),
    blocks,
  }
}

export async function listArticles(projectId: string): Promise<ArticleSummary[]> {
  const articles = await apiFetch<ArticleResponse[]>(`/projects/${projectId}/articles`)
  return articles.map(article => toSummary(article))
}

export async function getArticle(projectId: string, articleId: string): Promise<ArticleDetail> {
  return toDetail(await apiFetch<ArticleDetailResponse>(`/projects/${projectId}/articles/${articleId}`))
}
