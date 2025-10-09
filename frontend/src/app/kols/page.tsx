"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Filter, X, Upload, SortAsc, SortDesc } from "lucide-react";
import { useKOLs } from "@/hooks/useKOLs";
import { KOLFilters } from "@/lib/api/kols";

export default function KOLsPage() {
    const router = useRouter();
    const [showFilters, setShowFilters] = useState(false);

    // Filter state
    const [filters, setFilters] = useState<KOLFilters>({
        page: 1,
        page_size: 20,
        sort_by: 'created_at',
        sort_order: 'desc',
    });

    // Temporary filter inputs (before applying)
    const [tempFilters, setTempFilters] = useState({
        search: '',
        niche: '',
        location: '',
        tier: [] as string[],
        tags: '',
        status: '' as 'active' | 'inactive' | '',
    });

    const { data, isLoading, error } = useKOLs(filters);

    const getTierColor = (tier: string) => {
        const colors: Record<string, string> = {
            nano: "bg-gray-100 text-gray-800",
            micro: "bg-blue-100 text-blue-800",
            mid: "bg-green-100 text-green-800",
            macro: "bg-yellow-100 text-yellow-800",
            mega: "bg-purple-100 text-purple-800",
        };
        return colors[tier] || "bg-gray-100 text-gray-800";
    };

    const applyFilters = () => {
        const newFilters: KOLFilters = {
            ...filters,
            page: 1, // Reset to first page when applying filters
            search: tempFilters.search || undefined,
            niche: tempFilters.niche ? tempFilters.niche.split(',').map(n => n.trim()) : undefined,
            location: tempFilters.location || undefined,
            tier: tempFilters.tier.length > 0 ? tempFilters.tier : undefined,
            tags: tempFilters.tags ? tempFilters.tags.split(',').map(t => t.trim()) : undefined,
            status: tempFilters.status || undefined,
        };
        setFilters(newFilters);
        setShowFilters(false);
    };

    const clearFilters = () => {
        setTempFilters({
            search: '',
            niche: '',
            location: '',
            tier: [],
            tags: '',
            status: '',
        });
        setFilters({
            page: 1,
            page_size: 20,
            sort_by: 'created_at',
            sort_order: 'desc',
        });
        setShowFilters(false);
    };

    const toggleSort = (field: 'name' | 'created_at' | 'updated_at') => {
        setFilters(prev => ({
            ...prev,
            sort_by: field,
            sort_order: prev.sort_by === field && prev.sort_order === 'asc' ? 'desc' : 'asc',
        }));
    };

    const toggleTierFilter = (tier: string) => {
        setTempFilters(prev => ({
            ...prev,
            tier: prev.tier.includes(tier)
                ? prev.tier.filter(t => t !== tier)
                : [...prev.tier, tier]
        }));
    };

    // Count active filters
    const activeFilterCount = useMemo(() => {
        let count = 0;
        if (filters.search) count++;
        if (filters.niche?.length) count++;
        if (filters.location) count++;
        if (filters.tier?.length) count++;
        if (filters.tags?.length) count++;
        if (filters.status) count++;
        return count;
    }, [filters]);

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">KOLs</h1>
                        <p className="text-muted-foreground">
                            Manage your influencer database
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            onClick={() => router.push("/kols/import")}
                        >
                            <Upload className="h-4 w-4 mr-2" />
                            Import CSV
                        </Button>
                        <Button onClick={() => router.push("/kols/new")}>
                            <Plus className="h-4 w-4 mr-2" />
                            Add KOL
                        </Button>
                    </div>
                </div>

                <Card>
                    <CardHeader>
                        <div className="space-y-4">
                            <div className="flex items-center gap-4">
                                <div className="relative flex-1">
                                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        placeholder="Search by name, email, or handle..."
                                        value={tempFilters.search}
                                        onChange={(e) => {
                                            setTempFilters(prev => ({ ...prev, search: e.target.value }));
                                            // Apply search immediately for better UX
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
                                    {filters.niche?.map(niche => (
                                        <Badge key={niche} variant="secondary" className="gap-1">
                                            Niche: {niche}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => {
                                                    const newNiche = filters.niche?.filter(n => n !== niche);
                                                    setFilters(prev => ({ ...prev, niche: newNiche?.length ? newNiche : undefined }));
                                                }}
                                            />
                                        </Badge>
                                    ))}
                                    {filters.location && (
                                        <Badge variant="secondary" className="gap-1">
                                            Location: {filters.location}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => setFilters(prev => ({ ...prev, location: undefined }))}
                                            />
                                        </Badge>
                                    )}
                                    {filters.tier?.map(tier => (
                                        <Badge key={tier} variant="secondary" className="gap-1">
                                            Tier: {tier}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => {
                                                    const newTier = filters.tier?.filter(t => t !== tier);
                                                    setFilters(prev => ({ ...prev, tier: newTier?.length ? newTier : undefined }));
                                                }}
                                            />
                                        </Badge>
                                    ))}
                                    {filters.status && (
                                        <Badge variant="secondary" className="gap-1">
                                            Status: {filters.status}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => setFilters(prev => ({ ...prev, status: undefined }))}
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
                                            <label className="text-sm font-medium">Niche</label>
                                            <Input
                                                placeholder="fashion, lifestyle, beauty"
                                                value={tempFilters.niche}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, niche: e.target.value }))}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Location</label>
                                            <Input
                                                placeholder="Bangkok, Thailand"
                                                value={tempFilters.location}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, location: e.target.value }))}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Tags</label>
                                            <Input
                                                placeholder="micro-influencer, fashion"
                                                value={tempFilters.tags}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, tags: e.target.value }))}
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Tier</label>
                                            <div className="flex flex-wrap gap-2">
                                                {['nano', 'micro', 'mid', 'macro', 'mega'].map(tier => (
                                                    <Button
                                                        key={tier}
                                                        variant={tempFilters.tier.includes(tier) ? "default" : "outline"}
                                                        size="sm"
                                                        onClick={() => toggleTierFilter(tier)}
                                                    >
                                                        {tier}
                                                    </Button>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Status</label>
                                            <select
                                                value={tempFilters.status}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, status: e.target.value as any }))}
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                            >
                                                <option value="">All</option>
                                                <option value="active">Active</option>
                                                <option value="inactive">Inactive</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="flex gap-2 pt-2">
                                        <Button onClick={applyFilters}>Apply Filters</Button>
                                        <Button variant="outline" onClick={clearFilters}>Clear All</Button>
                                        <Button variant="ghost" onClick={() => setShowFilters(false)}>Cancel</Button>
                                    </div>
                                </div>
                            )}

                            {/* Sort Options */}
                            <div className="flex items-center gap-2 text-sm">
                                <span className="text-muted-foreground">Sort by:</span>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => toggleSort('name')}
                                    className="h-8 px-2"
                                >
                                    Name
                                    {filters.sort_by === 'name' && (
                                        filters.sort_order === 'asc' ? <SortAsc className="h-3 w-3 ml-1" /> : <SortDesc className="h-3 w-3 ml-1" />
                                    )}
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => toggleSort('created_at')}
                                    className="h-8 px-2"
                                >
                                    Created
                                    {filters.sort_by === 'created_at' && (
                                        filters.sort_order === 'asc' ? <SortAsc className="h-3 w-3 ml-1" /> : <SortDesc className="h-3 w-3 ml-1" />
                                    )}
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => toggleSort('updated_at')}
                                    className="h-8 px-2"
                                >
                                    Updated
                                    {filters.sort_by === 'updated_at' && (
                                        filters.sort_order === 'asc' ? <SortAsc className="h-3 w-3 ml-1" /> : <SortDesc className="h-3 w-3 ml-1" />
                                    )}
                                </Button>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <div className="text-center py-8">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                            </div>
                        ) : error ? (
                            <div className="text-center py-8 text-destructive">
                                Failed to load KOLs. Please try again.
                            </div>
                        ) : data?.kols?.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                {activeFilterCount > 0 ? 'No KOLs match your filters.' : 'No KOLs found. Create your first KOL to get started.'}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {data?.kols?.map((kol) => (
                                    <div
                                        key={kol.id}
                                        onClick={() => router.push(`/kols/${kol.id}`)}
                                        className="p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="font-semibold text-lg">{kol.name}</h3>
                                                    {kol.tier && (
                                                        <Badge className={getTierColor(kol.tier)}>
                                                            {kol.tier}
                                                        </Badge>
                                                    )}
                                                    <Badge
                                                        variant={kol.status === 'active' ? 'default' : 'secondary'}
                                                        className="text-xs"
                                                    >
                                                        {kol.status}
                                                    </Badge>
                                                </div>
                                                <div className="space-y-1 text-sm text-muted-foreground">
                                                    {kol.email && <p>📧 {kol.email}</p>}
                                                    {kol.location && <p>📍 {kol.location}</p>}
                                                    {kol.niche?.length > 0 && (
                                                        <p>🎯 {kol.niche.join(", ")}</p>
                                                    )}
                                                </div>
                                                {kol.tags?.length > 0 && (
                                                    <div className="flex flex-wrap gap-1 mt-2">
                                                        {kol.tags.slice(0, 3).map((tag) => (
                                                            <Badge key={tag} variant="outline" className="text-xs">
                                                                {tag}
                                                            </Badge>
                                                        ))}
                                                        {kol.tags.length > 3 && (
                                                            <Badge variant="outline" className="text-xs">
                                                                +{kol.tags.length - 3} more
                                                            </Badge>
                                                        )}
                                                    </div>
                                                )}
                                                {kol.social_handles?.length > 0 && (
                                                    <div className="flex gap-3 mt-3">
                                                        {kol.social_handles.map((handle, idx) => (
                                                            <div
                                                                key={idx}
                                                                className="text-xs bg-gray-100 px-2 py-1 rounded flex items-center gap-1"
                                                            >
                                                                <span className="capitalize">{handle.platform}:</span>
                                                                <span className="font-medium">
                                                                    {handle.follower_count?.toLocaleString() || 0}
                                                                </span>
                                                                {handle.is_verified && <span className="text-blue-500">✓</span>}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
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
                                    {Math.min((filters.page || 1) * (filters.page_size || 20), data.total)} of {data.total} KOLs
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
