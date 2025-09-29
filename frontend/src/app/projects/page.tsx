import { SimpleLayout } from '@/components/layout/SimpleLayout'
import { ProjectsManager } from '@/components/projects/ProjectsManager'

export default function ProjectsPage() {
  return (
    <SimpleLayout title="Projects">
      <ProjectsManager />
    </SimpleLayout>
  )
}