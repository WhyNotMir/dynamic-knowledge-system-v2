// ── Articles API ──────────────────────────────────────────────────

import type { ArticleSummary, ArticleDetail } from '@/lib/types'
import { formatDateTime } from '@/lib/utils'
import { apiFetch } from './client'

export interface ArticleResponse {
  id: string
  project_id: string
  candidate_id: string
  title: string
  topic_path?: string[]
  block_count?: number
  source_count?: number
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
  include_in_article?: boolean
  include_in_outline?: boolean
  created_at: string
}

interface ArticleDetailResponse extends ArticleResponse {
  blocks: ArticleBlockResponse[]
}

export function toArticleSummary(article: ArticleResponse, blocks = 0): ArticleSummary {
  const topicPath = article.topic_path ?? []
  return {
    id: article.id,
    title: article.title,
    topic: topicPath.join(' / '),
    topicPath,
    blocks: article.block_count ?? blocks,
    sources: article.source_count ?? 0,
    status: article.status,
    updated: formatDateTime(article.updated_at),
    citations: 0,
    excerpt: '',
  }
}

function blockType(block: ArticleBlockResponse): ArticleDetail['blocks'][number]['type'] {
  if (block.element_type === 'heading' && block.heading_level === 1) return 'h1'
  if (block.element_type === 'heading' && block.heading_level && block.heading_level >= 3) return 'h3'
  if (block.element_type === 'heading') return 'h2'
  if (block.element_type === 'table') return 'table'
  if (block.element_type === 'image') return 'image'
  if (block.element_type === 'caption') return 'caption'
  if (block.element_type === 'formula') return 'eq'
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
    elementType: block.element_type,
    headingLevel: block.heading_level ?? null,
    meta: block.meta_json,
    anchor: anchorFor(block),
    caption: captionText(block.meta_json),
    includeInArticle: block.include_in_article ?? true,
    includeInOutline: block.include_in_outline ?? true,
    provenance: {
      source: block.source_title ?? block.source_filename,
      page: block.page_number ?? null,
      fragment: block.fragment_id,
      section: block.section_path ?? '',
    },
  }))

  return {
    ...toArticleSummary(article, blocks.length),
    topic: article.topic_path ?? [],
    outline: blocks
      .filter(block => block.includeInOutline !== false)
      .filter(block => block.type === 'h1' || block.type === 'h2' || block.type === 'h3')
      .map(block => ({
        id: block.anchor ?? block.id,
        label: block.text,
        level: block.headingLevel ?? (block.type === 'h1' ? 1 : block.type === 'h2' ? 2 : 3),
      })),
    blocks,
  }
}

function captionText(meta: Record<string, unknown> | null | undefined): string | undefined {
  const caption = meta?.caption
  if (!caption || typeof caption !== 'object') return undefined
  const text = (caption as { text?: unknown }).text
  return typeof text === 'string' && text.trim() ? text : undefined
}

export async function listArticles(projectId: string): Promise<ArticleSummary[]> {
  const articles = await apiFetch<ArticleResponse[]>(`/projects/${projectId}/articles`)
  return articles.map(article => toArticleSummary(article))
}

export async function getArticle(projectId: string, articleId: string): Promise<ArticleDetail> {
  return toDetail(await apiFetch<ArticleDetailResponse>(`/projects/${projectId}/articles/${articleId}`))
}
