import type { ArticleSummary, TopicNode } from '@/lib/types'

export function buildTopicTree(articles: ArticleSummary[], activeArticleId?: string): TopicNode[] {
  const roots: TopicNode[] = []

  for (const article of articles) {
    const path = article.topicPath.length > 0 ? article.topicPath : [article.title]
    let siblings = roots

    path.forEach((label, index) => {
      const id = path.slice(0, index + 1).join('>')
      let node = siblings.find(item => item.id === id)
      if (!node) {
        node = {
          id,
          label,
          count: 0,
          open: true,
          children: [],
        }
        siblings.push(node)
      }

      node.count += Math.max(article.blocks, 1)
      if (index === path.length - 1) {
        node.articleId = article.id
        node.active = article.id === activeArticleId
      }
      siblings = node.children ?? []
    })
  }

  return pruneEmptyChildren(roots)
}

function pruneEmptyChildren(nodes: TopicNode[]): TopicNode[] {
  return nodes.map(node => ({
    ...node,
    children: node.children && node.children.length > 0
      ? pruneEmptyChildren(node.children)
      : undefined,
  }))
}
