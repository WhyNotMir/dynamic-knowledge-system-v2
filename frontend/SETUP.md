# Atlas – Setup

## Prerequisites
- Node.js 18+
- npm or pnpm

## Install & run

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — it redirects to `/projects`.

## Mock mode (default)
All API calls return typed mock data with simulated latency.
No backend is required.

## Connect real backend
1. Copy `.env.local.example` → `.env.local`
2. Set `NEXT_PUBLIC_API_URL=http://your-api-host`
3. In each `src/lib/api/*.ts`, flip `const MOCK = false`
   (or replace with env check: `const MOCK = !process.env.NEXT_PUBLIC_API_URL`)

## File tree

```
src/
├── app/                         Next.js App Router pages
│   ├── layout.tsx               Root layout + Providers
│   ├── page.tsx                 → redirect /projects
│   ├── projects/
│   │   └── page.tsx             Project list (no sidebar)
│   └── [projectId]/
│       ├── layout.tsx           Fetch project, render AppShell
│       ├── page.tsx             Workspace dashboard
│       ├── sources/
│       │   ├── page.tsx
│       │   └── [sourceId]/page.tsx
│       ├── inbox/page.tsx
│       ├── articles/
│       │   ├── page.tsx
│       │   └── [articleId]/page.tsx
│       └── qa/page.tsx
│
├── components/
│   ├── shell/                   AppShell, Sidebar, TopBar, Providers
│   ├── ui/                      StatusPill, EmptyState, LoadingState, ErrorState, ConfirmDialog
│   ├── workspace/               WorkspaceScreen
│   ├── projects/                ProjectsScreen
│   ├── sources/                 SourcesScreen, SourceDetailScreen
│   ├── inbox/                   InboxScreen
│   ├── articles/                ArticlesListScreen, ArticleDetailScreen,
│   │                            ArticleBody, TopicTreePanel, ArticleOutline
│   └── qa/                      QAScreen
│
├── lib/
│   ├── types.ts                 All domain types
│   ├── utils.ts                 cn(), formatConfidence(), truncate()
│   ├── query-client.ts          TanStack Query singleton
│   └── api/                     Typed API stubs (flip MOCK to connect backend)
│       ├── client.ts            apiFetch / apiUpload base
│       ├── projects.ts
│       ├── sources.ts
│       ├── inbox.ts
│       ├── articles.ts
│       └── qa.ts
│
├── fixtures/
│   └── mock-data.ts             All mock data — remove when backend is live
│
└── types/
    └── lucide-react.d.ts        Icon type declarations
```

## Connecting the backend

Each API file follows the same pattern:

```ts
const MOCK = true   // ← flip to false (or env-gate)

export async function listSources(projectId: string): Promise<Source[]> {
  if (MOCK) { await delay(); return mockSources.filter(...) }
  // ↓ this path activates when MOCK = false
  return apiFetch(`/api/projects/${projectId}/sources`)
}
```

The frontend expects a FastAPI backend with these endpoints:
- `GET  /api/projects`
- `POST /api/projects`
- `DELETE /api/projects/:id`
- `GET  /api/projects/:id/sources`
- `POST /api/projects/:id/sources`           (multipart file)
- `GET  /api/projects/:id/sources/:sid`
- `GET  /api/projects/:id/sources/:sid/fragments`
- `POST /api/projects/:id/sources/:sid/retry`
- `GET  /api/projects/:id/inbox`
- `PATCH /api/projects/:id/inbox/:cid`
- `POST /api/projects/:id/inbox/confirm-all`
- `POST /api/projects/:id/inbox/build`
- `GET  /api/projects/:id/articles`
- `GET  /api/projects/:id/articles/:aid`
- `POST /api/projects/:id/qa`
- `GET  /api/projects/:id/qa/suggestions`
