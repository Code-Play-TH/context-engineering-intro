import { SimpleLayout } from '@/components/layout/SimpleLayout'
import { UsersManager } from '@/components/admin/UsersManager'

export default function UsersPage() {
  return (
    <SimpleLayout title="User Management">
      <UsersManager />
    </SimpleLayout>
  )
}