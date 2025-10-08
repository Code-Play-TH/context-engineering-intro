"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/lib/auth";
import { useAuthStore } from "@/store/auth";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Target, TrendingUp, Calendar } from "lucide-react";
import api from "@/lib/api";

export default function DashboardPage() {
    const router = useRouter();
    const { user, setUser } = useAuthStore();

    useEffect(() => {
        if (!authApi.isAuthenticated()) {
            router.push("/login");
            return;
        }

        if (!user) {
            authApi.getCurrentUser().then(setUser).catch(() => router.push("/login"));
        }
    }, [user, setUser, router]);

    const { data: stats } = useQuery({
        queryKey: ["dashboard-stats"],
        queryFn: async () => {
            const [kols, campaigns] = await Promise.all([
                api.get("/kols?page=1&page_size=1"),
                api.get("/campaigns?page=1&page_size=1"),
            ]);
            return {
                totalKOLs: kols.data.total || 0,
                totalCampaigns: campaigns.data.total || 0,
                activeCampaigns: 0,
                totalReach: 0,
            };
        },
        enabled: !!user,
    });

    if (!user) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold">Dashboard</h1>
                    <p className="text-muted-foreground">
                        Welcome back, {user.full_name}
                    </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total KOLs</CardTitle>
                            <Users className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{stats?.totalKOLs || 0}</div>
                            <p className="text-xs text-muted-foreground">
                                Influencers in database
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Campaigns</CardTitle>
                            <Target className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{stats?.totalCampaigns || 0}</div>
                            <p className="text-xs text-muted-foreground">
                                Total campaigns created
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Active</CardTitle>
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{stats?.activeCampaigns || 0}</div>
                            <p className="text-xs text-muted-foreground">
                                Currently running
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Reach</CardTitle>
                            <TrendingUp className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {(stats?.totalReach || 0).toLocaleString()}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Across all platforms
                            </p>
                        </CardContent>
                    </Card>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                        <CardHeader>
                            <CardTitle>Quick Actions</CardTitle>
                            <CardDescription>Common tasks and shortcuts</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <button
                                onClick={() => router.push("/kols/new")}
                                className="w-full text-left px-4 py-2 rounded-md hover:bg-accent transition-colors"
                            >
                                + Add New KOL
                            </button>
                            <button
                                onClick={() => router.push("/campaigns/new")}
                                className="w-full text-left px-4 py-2 rounded-md hover:bg-accent transition-colors"
                            >
                                + Create Campaign
                            </button>
                            <button
                                onClick={() => router.push("/kols")}
                                className="w-full text-left px-4 py-2 rounded-md hover:bg-accent transition-colors"
                            >
                                📋 View All KOLs
                            </button>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Recent Activity</CardTitle>
                            <CardDescription>Latest updates and changes</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground">
                                No recent activity to display
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
