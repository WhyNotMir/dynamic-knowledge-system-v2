// ── Domain types for Atlas ────────────────────────────────────────

export type SourceStatus = 'pending' | 'processing' | 'done' | 'failed'
export type CandidateStatus = 'proposed' | 'confirmed' | 'rejected'
export type ArticleStatus = 'draft'

// ── Projects ──────────────────────────────────────────────────────

export interface Project {
  id: string
  name: string
  glyph: string
  description?: string
  articles: number
  candidates: number
  sources: number
  createdAt?: string
  updatedAt?: string
}

export interface CreateProjectRequest {
  name: string
  glyph?: string
  description?: string
}

// ── Sources ───────────────────────────────────────────────────────

export interface Source {
  id: string
  projectId: string
  title: string
  authors?: string
  year?: number
  filename: string
  pages?: number
  size?: string
  uploaded: string
  status: SourceStatus
  fragments: number
  candidates: number
  articles: number
  color: number           // 0–9 palette index
  progress?: number       // 0..1 while processing
  error?: string          // when status === 'failed'
}

export interface SourceFragment {
  id: string
  sourceId: string
  page: number
  section: string
  text: string
  linkedBlock: string | null  // "articleId/blockId" or null
}

// ── Inbox / Candidates ────────────────────────────────────────────

export interface ArticleCandidate {
  id: string
  projectId: string
  proposalId: string
  title: string
  sourcePath: string
  sourceId?: string
  fragments: number
  status: CandidateStatus
  confidence?: number      // 0..1 when backend provides it
  preview: string
  rejectReason?: string
}

export interface StructureProposal {
  id: string
  projectId: string
  candidates: ArticleCandidate[]
  proposedAt: string
}

export interface InboxItem {
  id: string
  projectId: string
  type: 'structure_proposal' | 'candidate'
  candidateId?: string
  proposalId?: string
  createdAt: string
}

export interface UpdateCandidateRequest {
  status?: CandidateStatus
  title?: string
  rejectReason?: string
}

// ── Articles ──────────────────────────────────────────────────────

export interface ArticleSummary {
  id: string
  title: string
  topic: string
  blocks: number
  sources: number
  status: ArticleStatus
  updated: string
  citations: number
  excerpt: string
}

export type ArticleBlockType = 'h1' | 'h2' | 'p' | 'eq'

export interface BlockProvenance {
  source: string
  page: number | null
  fragment: string
  section: string
}

export interface ArticleBlock {
  id: string
  type: ArticleBlockType
  text: string
  anchor?: string
  caption?: string
  provenance?: BlockProvenance | BlockProvenance[]
}

export interface OutlineItem {
  id: string
  label: string
  level: 1 | 2
}

export interface ArticleDetail {
  id: string
  title: string
  topic: string[]
  status: ArticleStatus
  updated: string
  authors?: string
  summary?: string
  outline: OutlineItem[]
  blocks: ArticleBlock[]
  sourceRefs?: SourceRef[]
  relatedArticles?: RelatedArticle[]
}

export interface SourceRef {
  id: string
  title: string
  authors?: string
  year?: number
}

export interface RelatedArticle {
  id: string
  title: string
}

// ── Topic tree ────────────────────────────────────────────────────

export interface TopicNode {
  id: string
  label: string
  count: number
  open?: boolean
  active?: boolean
  muted?: boolean
  articleId?: string
  children?: TopicNode[]
}

// ── Q&A ───────────────────────────────────────────────────────────

export interface Citation {
  id: string
  articleId: string
  articleTitle: string
  block: string
  source: string
  page: number
  fragment: string
  quote: string
}

export interface QAAnswer {
  summary: string
  points: string[]
  citations: Citation[]
  confidence: number   // 0..1
}

export interface QAMessage {
  kind: 'ask' | 'answer' | 'insufficient'
  text?: string
  answer?: QAAnswer
  insufficientContext?: InsufficientContextInfo
}

export interface InsufficientContextInfo {
  reason: string
  suggestions: string[]
  pendingSources?: string[]
}

export interface AskQuestionRequest {
  projectId: string
  question: string
  articleId?: string   // scope to specific article
}

// ── Activity ──────────────────────────────────────────────────────

export type ActivityKind = 'process' | 'candidate' | 'confirm' | 'ask' | 'upload' | 'fail' | 'reject'

export interface ActivityItem {
  id?: string
  when: string
  kind: ActivityKind
  text: string
  target: string
  meta: string
}

// ── API response wrappers ─────────────────────────────────────────

export interface ApiList<T> {
  items: T[]
  total: number
}

export interface ApiError {
  message: string
  code?: string
}
