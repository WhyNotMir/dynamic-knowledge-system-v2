import { redirect } from 'next/navigation'
import { getProject } from '@/lib/api/projects'
import { ApiError } from '@/lib/api/client'
import { ProjectShellClient } from './ProjectShellClient'

export default async function ProjectLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: { projectId: string }
}) {
  let project
  try {
    project = await getProject(params.projectId)
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 422)) {
      redirect('/projects')
    }
    throw error
  }

  return <ProjectShellClient project={project}>{children}</ProjectShellClient>
}
