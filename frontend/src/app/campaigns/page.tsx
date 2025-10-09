'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCampaigns, useDeleteCampaign, useDuplicateCampaign } from '@/hooks/useCampaigns';
import { Card } from '@/components/ui/card';
import { Campaign } from '@/lib/api/campaigns';

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

export default function CampaignsPage() {
    const router = useRouter();
    const [page, setPage] = useState(1);
    const [statusFilter, setStatusFilter] = useState<string>('');

    const { data, isLoading, error } = useCampaigns({
        page,
        page_size: 20,
        status: statusFilter || undefined,
    });

    const deleteMutation = useDeleteCampaign();
    const duplicateMutation = useDuplicateCampaign();

    const handleDelete = async (id: number) => {
        if (confirm('Are you sure you want to delete this campaign?')) {
            try {
                await deleteMutation.mutateAsync(id);
                alert('Campaign deleted successfully');
            } catch (error: any) {
                alert(error.message || 'Failed to delete campaign');
            }
        }
    };

    const handleDuplicate = async (id: number) => {
        try {
            const newCampaign = await duplicateMutation.mutateAsync(id);
            alert('Campaign duplicated successfully');
            router.push(`/campaigns/${newCampaign.id}`);
        } catch (error: any) {
            alert(error.message || 'Failed to duplicate campaign');
        }
    };

    const formatDate = (date: string | null) => {
        if (!date) return 'N/A';
        return new Date(date).toLocaleDateString();
    };

    const formatCurrency = (amount: number | null, currency: string) => {
        if (amount === null) return 'N/A';
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

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <p className="text-red-600 mb-4">Failed to load campaigns</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    const campaigns = data?.campaigns || [];
    const total = data?.total || 0;
    const totalPages = Math.ceil(total / 20);

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Campaigns</h1>
                <button
                    onClick={() => router.push('/campaigns/new')}
                    className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
                >
                    Create Campaign
                </button>
            </div>

            {/* Filters */}
            <div className="mb-6 flex gap-4">
                <select
                    value={statusFilter}
                    onChange={(e) => {
                        setStatusFilter(e.target.value);
                        setPage(1);
                    }}
                    className="px-4 py-2 border rounded"
                >
                    <option value="">All Statuses</option>
                    <option value="draft">Draft</option>
                    <option value="pending_approval">Pending Approval</option>
                    <option value="active">Active</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                </select>
            </div>

            {/* Campaign List */}
            {campaigns.length === 0 ? (
                <Card className="p-8 text-center">
                    <p className="text-gray-500 mb-4">No campaigns found</p>
                    <button
                        onClick={() => router.push('/campaigns/new')}
                        className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
                    >
                        Create Your First Campaign
                    </button>
                </Card>
            ) : (
                <div className="grid gap-4">
                    {campaigns.map((campaign: Campaign) => (
                        <Card key={campaign.id} className="p-6 hover:shadow-lg transition-shadow">
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h3
                                            className="text-xl font-semibold cursor-pointer hover:text-primary"
                                            onClick={() => router.push(`/campaigns/${campaign.id}`)}
                                        >
                                            {campaign.name}
                                        </h3>
                                        <span
                                            className={`px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[campaign.status]
                                                }`}
                                        >
                                            {STATUS_LABELS[campaign.status]}
                                        </span>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
                                        <div>
                                            <p className="text-gray-500">Start Date</p>
                                            <p className="font-medium">{formatDate(campaign.start_date)}</p>
                                        </div>
                                        <div>
                                            <p className="text-gray-500">End Date</p>
                                            <p className="font-medium">{formatDate(campaign.end_date)}</p>
                                        </div>
                                        <div>
                                            <p className="text-gray-500">Budget</p>
                                            <p className="font-medium">
                                                {formatCurrency(campaign.total_budget, campaign.currency)}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-gray-500">KPIs / Deliverables</p>
                                            <p className="font-medium">
                                                {campaign.kpis.length} / {campaign.deliverables.length}
                                            </p>
                                        </div>
                                    </div>

                                    {campaign.objectives && (
                                        <p className="mt-3 text-sm text-gray-600 line-clamp-2">
                                            {campaign.objectives}
                                        </p>
                                    )}
                                </div>

                                <div className="flex gap-2 ml-4">
                                    <button
                                        onClick={() => router.push(`/campaigns/${campaign.id}`)}
                                        className="px-3 py-1 text-sm border rounded hover:bg-gray-50"
                                    >
                                        View
                                    </button>
                                    <button
                                        onClick={() => handleDuplicate(campaign.id)}
                                        className="px-3 py-1 text-sm border rounded hover:bg-gray-50"
                                        disabled={duplicateMutation.isPending}
                                    >
                                        Duplicate
                                    </button>
                                    {campaign.status !== 'active' && (
                                        <button
                                            onClick={() => handleDelete(campaign.id)}
                                            className="px-3 py-1 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50"
                                            disabled={deleteMutation.isPending}
                                        >
                                            Delete
                                        </button>
                                    )}
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="mt-6 flex justify-center gap-2">
                    <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                        Previous
                    </button>
                    <span className="px-4 py-2">
                        Page {page} of {totalPages}
                    </span>
                    <button
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    );
}
