import { SimpleLayout } from '@/components/layout/SimpleLayout'
import { ReportDashboard } from '@/components/reports/ReportDashboard'

export default function ReportsPage() {
  return (
    <SimpleLayout title="Performance Reports">
      <ReportDashboard />
    </SimpleLayout>
  )
}