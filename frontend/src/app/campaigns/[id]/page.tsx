'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCampaign, useChangeStatus, useDeleteCampaign } from '@/hooks/useCampaigns';
import { Card } from '@/components/ui/card';

const STATUS_COLORS = {
    draft: 'bg-gray-100 text-gray-800',
    pending_approval: 'bg-yellow-100 text-yellow-800',
    active: 'bg-green-100 text-green-800',
    completed: 'bg-blue-100 text-blue-800',
    cancelled: 'bg-red-100 text-red-800',
};

const STATUS_LABELS = {
    draft: 'Draft',
    pending_approval: 'Pending Approval',
    active: 'Active',
    completed: 'Completed',
    cancelled: 'Cancelled',
};

const STATUS_TRANSITIONS: Record<string, string[]> = {
    draft: ['pending_approval', 'cancelled'],
    pending_approval: ['active', 'draft', 'cancelled'],
    active: ['completed', 'cancelled'],
    completed: [],
    cancelled: [],
};

export default function CampaignDetailPage() {
    const params = useParams();
    const router = useRouter();
    const id = parseInt(params.id as string);

    const { data: campaign, isLoading, error } = useCampaign(id);
    const changeStatusMutation = useChangeStatus();
    const deleteMutation = useDeleteCampaign();

    const handleStatusChange = async (newStatus: string) => {
        if (confirm(`Change status to ${STATUS_LABELS[newStatus as keyof typeof STATUS_LABELS]}?`)) {
            try {
                await changeStatusMutation.mutateAsync({ id, status: newStatus });
                alert('Status changed successfully');
            } catch (error: any) {
                alert(error.message || 'Failed to change status');
            }
        }
    };

    const handleDelete = async () => {
        if (confirm('Are you sure you want to delete this campaign?')) {
            try {
                await deleteMutation.mutateAsync(id);
                alert('Campaign deleted successfully');
                router.push('/campaigns');
            } catch (error: any) {
                alert(error.message || 'Failed to delete campaign');
            }
        }
    };

    const formatDate = (date: string | null) => {
        if (!date) return 'Not set';
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    };

    const formatCurrency = (amount: number | null, currency: string) => {
        if (amount === null) return 'Not set';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency || 'USD',
        }).format(amount);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (error || !campaign) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <p className="text-red-600 mb-4">Campaign not found</p>
                    <button
                        onClick={() => router.push('/campaigns')}
                        className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
                    >
                        Back to Campaigns
                    </button>
                </div>
            </div>
        );
    }

    const availableTransitions = STATUS_TRANSITIONS[campaign.status] || [];

    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl">
            {/* Header */}
            <div className="mb-6">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">{campaign.name}</h1>
                        <span
                            className={`inline-block px-3 py-1 rounded text-sm font-medium ${STATUS_COLORS[campaign.status]
                                }`}
                        >
                            {STATUS_LABELS[campaign.status]}
                        </span>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => router.push(`/campaigns/${id}/edit`)}
                            className="px-4 py-2 border rounded hover:bg-gray-50"
                        >
                            Edit
                        </button>
                        {campaign.status !== 'active' && (
                            <button
                                onClick={handleDelete}
                                disabled={deleteMutation.isPending}
                                className="px-4 py-2 border border-red-300 text-red-600 rounded hover:bg-red-50"
                            >
                                Delete
                            </button>
                        )}
                    </div>
                </div>

                {/* Status Actions */}
                {availableTransitions.length > 0 && (
                    <div className="flex gap-2">
                        <span className="text-sm text-gray-600 py-2">Change status to:</span>
                        {availableTransitions.map((status) => (
                            <button
                                key={status}
                                onClick={() => handleStatusChange(status)}
                                disabled={changeStatusMutation.isPending}
                                className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
                            >
                                {STATUS_LABELS[status as keyof typeof STATUS_LABELS]}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Basic Info */}
            <Card className="p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">Campaign Details</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    <div>
                        <p className="text-sm text-gray-500 mb-1">Start Date</p>
                        <p className="font-medium">{formatDate(campaign.start_date)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500 mb-1">End Date</p>
                        <p className="font-medium">{formatDate(campaign.end_date)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500 mb-1">Budget</p>
                        <p className="font-medium">{formatCurrency(campaign.total_budget, campaign.currency)}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-500 mb-1">Currency</p>
                        <p className="font-medium">{campaign.currency}</p>
                    </div>
                </div>

                {campaign.objectives && (
                    <div className="mt-6">
                        <p className="text-sm text-gray-500 mb-2">Objectives</p>
                        <p className="text-gray-700 whitespace-pre-wrap">{campaign.objectives}</p>
                    </div>
                )}

                {campaign.target_audience && (
                    <div className="mt-6">
                        <p className="text-sm text-gray-500 mb-2">Target Audience</p>
                        <pre className="bg-gray-50 p-3 rounded text-sm overflow-x-auto">
                            {JSON.stringify(campaign.target_audience, null, 2)}
                        </pre>
                    </div>
                )}
            </Card>

            {/* KPIs */}
            <Card className="p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">KPIs ({campaign.kpis.length})</h2>
                {campaign.kpis.length === 0 ? (
                    <p className="text-gray-500">No KPIs defined</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-2 px-3">Type</th>
                                    <th className="text-right py-2 px-3">Target</th>
                                    <th className="text-right py-2 px-3">Actual</th>
                                    <th className="text-left py-2 px-3">Unit</th>
                                    <th className="text-right py-2 px-3">Progress</th>
                                </tr>
                            </thead>
                            <tbody>
                                {campaign.kpis.map((kpi) => {
                                    const progress = kpi.actual_value
                                        ? Math.round((kpi.actual_value / kpi.target_value) * 100)
                                        : 0;
                                    return (
                                        <tr key={kpi.id} className="border-b">
                                            <td className="py-3 px-3">{kpi.kpi_type}</td>
                                            <td className="text-right py-3 px-3">{kpi.target_value.toLocaleString()}</td>
                                            <td className="text-right py-3 px-3">
                                                {kpi.actual_value?.toLocaleString() || '-'}
                                            </td>
                                            <td className="py-3 px-3">{kpi.unit}</td>
                                            <td className="text-right py-3 px-3">
                                                <span
                                                    className={`px-2 py-1 rounded text-xs ${progress >= 100
                                                            ? 'bg-green-100 text-green-800'
                                                            : progress >= 50
                                                                ? 'bg-yellow-100 text-yellow-800'
                                                                : 'bg-gray-100 text-gray-800'
                                                        }`}
                                                >
                                                    {progress}%
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>

            {/* Deliverables */}
            <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">Deliverables ({campaign.deliverables.length})</h2>
                {campaign.deliverables.length === 0 ? (
                    <p className="text-gray-500">No deliverables defined</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-2 px-3">Type</th>
                                    <th className="text-center py-2 px-3">Quantity</th>
                                    <th className="text-left py-2 px-3">Deadline</th>
                                    <th className="text-left py-2 px-3">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {campaign.deliverables.map((deliverable) => (
                                    <tr key={deliverable.id} className="border-b">
                                        <td className="py-3 px-3">{deliverable.deliverable_type}</td>
                                        <td className="text-center py-3 px-3">{deliverable.quantity}</td>
                                        <td className="py-3 px-3">{formatDate(deliverable.deadline)}</td>
                                        <td className="py-3 px-3">
                                            <span
                                                className={`px-2 py-1 rounded text-xs ${deliverable.status === 'completed'
                                                        ? 'bg-green-100 text-green-800'
                                                        : deliverable.status === 'in_progress'
                                                            ? 'bg-yellow-100 text-yellow-800'
                                                            : 'bg-gray-100 text-gray-800'
                                                    }`}
                                            >
                                                {deliverable.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>

            {/* Metadata */}
            <div className="mt-6 text-sm text-gray-500">
                <p>Created: {new Date(campaign.created_at).toLocaleString()}</p>
                <p>Last Updated: {new Date(campaign.updated_at).toLocaleString()}</p>
            </div>
        </div>
    );
}
