"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Search, Filter } from "lucide-react";
import api from "@/lib/api";

interface KOL {
    id: number;
    name: string;
    email: string;
    location: string;
    tier: string;
    niche: string[];
    tags: string[];
    status: string;
    social_handles: Array<{
        platform: string;
        handle: string;
        follower_count: number;
    }>;
}

export default function KOLsPage() {
    const router = useRouter();
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");

    const { data, isLoading } = useQuery({
        queryKey: ["kols", page, search],
        queryFn: async () => {
            const params = new URLSearchParams({
                page: page.toString(),
                page_size: "20",
                ...(search && { search }),
            });
            const response = await api.get(`/kols?${params}`);
            return response.data;
        },
    });

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
                    <Button onClick={() => router.push("/kols/new")}>
                        <Plus className="h-4 w-4 mr-2" />
                        Add KOL
                    </Button>
                </div>

                <Card>
                    <CardHeader>
                        <div className="flex items-center gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search by name, email, or handle..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className="pl-10"
                                />
                            </div>
                            <Button variant="outline">
                                <Filter className="h-4 w-4 mr-2" />
                                Filters
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <div className="text-center py-8">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                            </div>
                        ) : data?.kols?.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                No KOLs found. Create your first KOL to get started.
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {data?.kols?.map((kol: KOL) => (
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
                                                        <span
                                                            className={`px-2 py-1 rounded-full text-xs font-medium ${getTierColor(
                                                                kol.tier
                                                            )}`}
                                                        >
                                                            {kol.tier}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="space-y-1 text-sm text-muted-foreground">
                                                    {kol.email && <p>📧 {kol.email}</p>}
                                                    {kol.location && <p>📍 {kol.location}</p>}
                                                    {kol.niche?.length > 0 && (
                                                        <p>🎯 {kol.niche.join(", ")}</p>
                                                    )}
                                                </div>
                                                {kol.social_handles?.length > 0 && (
                                                    <div className="flex gap-3 mt-3">
                                                        {kol.social_handles.map((handle, idx) => (
                                                            <div
                                                                key={idx}
                                                                className="text-xs bg-gray-100 px-2 py-1 rounded"
                                                            >
                                                                {handle.platform}: {handle.follower_count?.toLocaleString() || 0}
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

                        {data && data.total > 20 && (
                            <div className="flex items-center justify-between mt-6 pt-6 border-t">
                                <p className="text-sm text-muted-foreground">
                                    Showing {(page - 1) * 20 + 1} to{" "}
                                    {Math.min(page * 20, data.total)} of {data.total} KOLs
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setPage(page - 1)}
                                        disabled={page === 1}
                                    >
                                        Previous
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setPage(page + 1)}
                                        disabled={page * 20 >= data.total}
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
