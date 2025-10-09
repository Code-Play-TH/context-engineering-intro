"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Filter, X, FileText, Clock, CheckCircle, XCircle } from "lucide-react";
import { useBriefs, useBriefStats } from "@/hooks/useBriefs";
import { BriefFilters } from "@/lib/api/briefs";

export default function BriefsPage() {
    const router = useRouter();
    const [showFilters, setShowFilters] = useState(false);

    // Filter state
    const [filters, setFilters] = useState<BriefFilters>({
        page: 1,
        page_size: 20,
    });

    // Temporary filter inputs
    const [tempFilters, setTempFilters] = useState({
        search: '',
        status: '' as any,
        campaign_id: '',
        kol_id: '',
    });

    const { data, isLoading, error } = useBriefs(filters);
    const { data: stats } = useBriefStats();

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            draft: "bg-gray-100 text-gray-800",
            pending_review: "bg-yellow-100 text-yellow-800",
            approved: "bg-green-100 text-green-800",
            sent: "bg-blue-100 text-blue-800",
            acknowledged: "bg-purple-100 text-purple-800",
            in_progress: "bg-orange-100 text-orange-800",
            completed: "bg-emerald-100 text-emerald-800",
            rejected: "bg-red-100 text-red-800",
        };
        return colors[status] || "bg-gray-100 text-gray-800";
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'draft':
                return <FileText className="h-4 w-4" />;
            case 'pending_review':
                return <Clock className="h-4 w-4" />;
            case 'approved':
            case 'completed':
                return <CheckCircle className="h-4 w-4" />;
            case 'rejected':
                return <XCircle className="h-4 w-4" />;
            default:
                return <FileText className="h-4 w-4" />;
        }
    };

    const applyFilters = () => {
        const newFilters: BriefFilters = {
            ...filters,
            page: 1,
            search: tempFilters.search || undefined,
            status: tempFilters.status || undefined,
            campaign_id: tempFilters.campaign_id ? parseInt(tempFilters.campaign_id) : undefined,
            kol_id: tempFilters.kol_id ? parseInt(tempFilters.kol_id) : undefined,
        };
        setFilters(newFilters);
        setShowFilters(false);
    };

    const clearFilters = () => {
        setTempFilters({
            search: '',
            status: '',
            campaign_id: '',
            kol_id: '',
        });
        setFilters({
            page: 1,
            page_size: 20,
        });
        setShowFilters(false);
    };

    // Count active filters
    const activeFilterCount = useMemo(() => {
        let count = 0;
        if (filters.search) count++;
        if (filters.status) count++;
        if (filters.campaign_id) count++;
        if (filters.kol_id) count++;
        return count;
    }, [filters]);

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Briefs</h1>
                        <p className="text-muted-foreground">
                            Manage KOL campaign briefs and templates
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            onClick={() => router.push("/briefs/templates")}
                        >
                            <FileText className="h-4 w-4 mr-2" />
                            Templates
                        </Button>
                        <Button onClick={() => router.push("/briefs/new")}>
                            <Plus className="h-4 w-4 mr-2" />
                            Create Brief
                        </Button>
                    </div>
                </div>

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center">
                                    <FileText className="h-8 w-8 text-blue-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-muted-foreground">Total Briefs</p>
                                        <p className="text-2xl font-bold">{stats.total_briefs}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center">
                                    <Clock className="h-8 w-8 text-yellow-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-muted-foreground">Pending Review</p>
                                        <p className="text-2xl font-bold">{stats.by_status.pending_review || 0}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center">
                                    <CheckCircle className="h-8 w-8 text-green-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-muted-foreground">Approved</p>
                                        <p className="text-2xl font-bold">{stats.by_status.approved || 0}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center">
                                    <CheckCircle className="h-8 w-8 text-emerald-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-muted-foreground">Completed</p>
                                        <p className="text-2xl font-bold">{stats.by_status.completed || 0}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Filters and List */}
                <Card>
                    <CardHeader>
                        <div className="space-y-4">
                            <div className="flex items-center gap-4">
                                <div className="relative flex-1">
                                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        placeholder="Search briefs by title or content..."
                                        value={tempFilters.search}
                                        onChange={(e) => {
                                            setTempFilters(prev => ({ ...prev, search: e.target.value }));
                                            setFilters(prev => ({ ...prev, search: e.target.value, page: 1 }));
                                        }}
                                        className="pl-10"
                                    />
                                </div>
                                <Button
                                    variant="outline"
                                    onClick={() => setShowFilters(!showFilters)}
                                    className="relative"
                                >
                                    <Filter className="h-4 w-4 mr-2" />
                                    Filters
                                    {activeFilterCount > 0 && (
                                        <Badge
                                            variant="destructive"
                                            className="absolute -top-2 -right-2 h-5 w-5 p-0 text-xs"
                                        >
                                            {activeFilterCount}
                                        </Badge>
                                    )}
                                </Button>
                            </div>

                            {/* Active Filters Display */}
                            {activeFilterCount > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    {filters.status && (
                                        <Badge variant="secondary" className="gap-1">
                                            Status: {filters.status}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => setFilters(prev => ({ ...prev, status: undefined }))}
                                            />
                                        </Badge>
                                    )}
                                    {filters.campaign_id && (
                                        <Badge variant="secondary" className="gap-1">
                                            Campaign ID: {filters.campaign_id}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => setFilters(prev => ({ ...prev, campaign_id: undefined }))}
                                            />
                                        </Badge>
                                    )}
                                    {filters.kol_id && (
                                        <Badge variant="secondary" className="gap-1">
                                            KOL ID: {filters.kol_id}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => setFilters(prev => ({ ...prev, kol_id: undefined }))}
                                            />
                                        </Badge>
                                    )}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={clearFilters}
                                        className="h-6 px-2 text-xs"
                                    >
                                        Clear all
                                    </Button>
                                </div>
                            )}

                            {/* Advanced Filters Panel */}
                            {showFilters && (
                                <div className="border-t pt-4 space-y-4">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Status</label>
                                            <select
                                                value={tempFilters.status}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, status: e.target.value }))}
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                            >
                                                <option value="">All Statuses</option>
                                                <option value="draft">Draft</option>
                                                <option value="pending_review">Pending Review</option>
                                                <option value="approved">Approved</option>
                                                <option value="sent">Sent</option>
                                                <option value="acknowledged">Acknowledged</option>
                                                <option value="in_progress">In Progress</option>
                                                <option value="completed">Completed</option>
                                                <option value="rejected">Rejected</option>
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Campaign ID</label>
                                            <Input
                                                type="number"
                                                placeholder="Enter campaign ID"
                                                value={tempFilters.campaign_id}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, campaign_id: e.target.value }))}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">KOL ID</label>
                                            <Input
                                                type="number"
                                                placeholder="Enter KOL ID"
                                                value={tempFilters.kol_id}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, kol_id: e.target.value }))}
                                            />
                                        </div>
                                    </div>

                                    <div className="flex gap-2 pt-2">
                                        <Button onClick={applyFilters}>Apply Filters</Button>
                                        <Button variant="outline" onClick={clearFilters}>Clear All</Button>
                                        <Button variant="ghost" onClick={() => setShowFilters(false)}>Cancel</Button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <div className="text-center py-8">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                            </div>
                        ) : error ? (
                            <div className="text-center py-8 text-destructive">
                                Failed to load briefs. Please try again.
                            </div>
                        ) : data?.briefs?.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                {activeFilterCount > 0 ? 'No briefs match your filters.' : 'No briefs found. Create your first brief to get started.'}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {data?.briefs?.map((brief) => (
                                    <div
                                        key={brief.id}
                                        onClick={() => router.push(`/briefs/${brief.id}`)}
                                        className="p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="font-semibold text-lg">{brief.title}</h3>
                                                    <div className="flex items-center gap-1">
                                                        {getStatusIcon(brief.status)}
                                                        <Badge className={getStatusColor(brief.status)}>
                                                            {brief.status.replace('_', ' ')}
                                                        </Badge>
                                                    </div>
                                                </div>
                                                <div className="space-y-1 text-sm text-muted-foreground">
                                                    <p>📋 Campaign: {brief.campaign_name}</p>
                                                    <p>👤 KOL: {brief.kol_name}</p>
                                                    {brief.template_name && <p>📄 Template: {brief.template_name}</p>}
                                                    <p>👨‍💼 Created by: {brief.creator_name}</p>
                                                    {brief.approver_name && <p>✅ Approved by: {brief.approver_name}</p>}
                                                </div>
                                                <div className="mt-3 text-sm text-muted-foreground">
                                                    <p className="line-clamp-2">{brief.content.substring(0, 150)}...</p>
                                                </div>
                                                <div className="mt-2 text-xs text-muted-foreground">
                                                    Created: {new Date(brief.created_at).toLocaleDateString()}
                                                    {brief.updated_at && (
                                                        <span> • Updated: {new Date(brief.updated_at).toLocaleDateString()}</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {data && data.total > (filters.page_size || 20) && (
                            <div className="flex items-center justify-between mt-6 pt-6 border-t">
                                <p className="text-sm text-muted-foreground">
                                    Showing {((filters.page || 1) - 1) * (filters.page_size || 20) + 1} to{" "}
                                    {Math.min((filters.page || 1) * (filters.page_size || 20), data.total)} of {data.total} briefs
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setFilters(prev => ({ ...prev, page: (prev.page || 1) - 1 }))}
                                        disabled={(filters.page || 1) === 1}
                                    >
                                        Previous
                                    </Button>
                                    <span className="flex items-center px-3 text-sm">
                                        Page {filters.page || 1} of {data.total_pages}
                                    </span>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setFilters(prev => ({ ...prev, page: (prev.page || 1) + 1 }))}
                                        disabled={(filters.page || 1) >= data.total_pages}
                                    >
                                        Next
                                    </Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}