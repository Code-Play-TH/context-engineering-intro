import { SimpleLayout } from '@/components/layout/SimpleLayout'
import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard'

export default function AnalyticsPage() {
  return (
    <SimpleLayout title="Analytics">
      <AnalyticsDashboard />
    </SimpleLayout>
  )
}