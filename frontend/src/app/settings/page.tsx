import { SimpleLayout } from '@/components/layout/SimpleLayout'
import { SettingsManager } from '@/components/settings/SettingsManager'

export default function SettingsPage() {
  return (
    <SimpleLayout title="Settings">
      <SettingsManager />
    </SimpleLayout>
  )
}