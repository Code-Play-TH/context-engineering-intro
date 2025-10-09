"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useKOL, useUpdateKOL, useDeleteKOL, useAddKOLTag, useRemoveKOLTag, useKOLDuplicates } from "@/hooks/useKOLs";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Edit, Trash2, Plus, X, AlertTriangle, ExternalLink } from "lucide-react";

interface KOLDetailPageProps {
    params: {
        id: string;
    };
}

export default function KOLDetailPage({ params }: KOLDetailPageProps) {
    const router = useRouter();
    const kolId = parseInt(params.id);

    const [isEditing, setIsEditing] = useState(false);
    const [newTag, setNewTag] = useState("");
    const [showDuplicates, setShowDuplicates] = useState(false);

    const { data: kol, isLoading, error } = useKOL(kolId);
    const { data: duplicates } = useKOLDuplicates(kolId);
    const updateKOL = useUpdateKOL();
    const deleteKOL = useDeleteKOL();
    const addTag = useAddKOLTag();
    const removeTag = useRemoveKOLTag();

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

    const getPlatformIcon = (platform: string) => {
        const icons: Record<string, string> = {
            instagram: "📷",
            tiktok: "🎵",
            youtube: "📺",
            twitter: "🐦",
            facebook: "👥",
        };
        return icons[platform] || "🌐";
    };

    const handleAddTag = async () => {
        if (!newTag.trim() || !kol) return;

        try {
            await addTag.mutateAsync({ id: kol.id, tag: newTag.trim() });
            setNewTag("");
        } catch (error) {
            console.error("Failed to add tag:", error);
        }
    };

    const handleRemoveTag = async (tag: string) => {
        if (!kol) return;

        try {
            await removeTag.mutateAsync({ id: kol.id, tag });
        } catch (error) {
            console.error("Failed to remove tag:", error);
        }
    };

    const handleDelete = async () => {
        if (!kol || !confirm("Are you sure you want to delete this KOL? This action cannot be undone.")) {
            return;
        }

        try {
            await deleteKOL.mutateAsync(kol.id);
            router.push("/kols");
        } catch (error) {
            console.error("Failed to delete KOL:", error);
        }
    };

    if (isLoading) {
        return (
            <DashboardLayout>
                <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                </div>
            </DashboardLayout>
        );
    }

    if (error || !kol) {
        return (
            <DashboardLayout>
                <div className="text-center py-8 text-destructive">
                    Failed to load KOL details. Please try again.
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-3xl font-bold">{kol.name}</h1>
                            <Badge className={getTierColor(kol.tier)}>
                                {kol.tier}
                            </Badge>
                            <Badge variant={kol.status === 'active' ? 'default' : 'secondary'}>
                                {kol.status}
                            </Badge>
                        </div>
                        <p className="text-muted-foreground">
                            KOL ID: {kol.id} • Created {new Date(kol.created_at).toLocaleDateString()}
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={() => setIsEditing(true)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                        </Button>
                        <Button variant="destructive" onClick={handleDelete}>
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                        </Button>
                    </div>
                </div>

                {/* Duplicate Warning */}
                {duplicates && duplicates.length > 0 && (
                    <Card className="border-yellow-200 bg-yellow-50">
                        <CardContent className="pt-6">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                                <div className="flex-1">
                                    <h3 className="font-medium text-yellow-800">Potential Duplicates Found</h3>
                                    <p className="text-sm text-yellow-700 mt-1">
                                        This KOL may be a duplicate of {duplicates.length} other KOL(s).
                                    </p>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="mt-2"
                                        onClick={() => setShowDuplicates(!showDuplicates)}
                                    >
                                        {showDuplicates ? 'Hide' : 'Show'} Duplicates
                                    </Button>
                                </div>
                            </div>
                            {showDuplicates && (
                                <div className="mt-4 space-y-2">
                                    {duplicates.map((duplicate) => (
                                        <div key={duplicate.id} className="p-3 bg-white rounded border">
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <p className="font-medium">{duplicate.name}</p>
                                                    <p className="text-sm text-muted-foreground">
                                                        {duplicate.email} • {duplicate.location}
                                                    </p>
                                                </div>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => router.push(`/kols/${duplicate.id}`)}
                                                >
                                                    View
                                                </Button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Basic Information */}
                    <div className="lg:col-span-2 space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Basic Information</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-muted-foreground">Email</label>
                                        <p className="mt-1">{kol.email || "Not provided"}</p>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-muted-foreground">Phone</label>
                                        <p className="mt-1">{kol.phone || "Not provided"}</p>
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-muted-foreground">Location</label>
                                    <p className="mt-1">{kol.location || "Not provided"}</p>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-muted-foreground">Niche</label>
                                    <div className="mt-1 flex flex-wrap gap-1">
                                        {kol.niche.length > 0 ? (
                                            kol.niche.map((n) => (
                                                <Badge key={n} variant="outline">{n}</Badge>
                                            ))
                                        ) : (
                                            <span className="text-muted-foreground">No niche specified</span>
                                        )}
                                    </div>
                                </div>
                                {kol.notes && (
                                    <div>
                                        <label className="text-sm font-medium text-muted-foreground">Notes</label>
                                        <p className="mt-1 text-sm bg-gray-50 p-3 rounded">{kol.notes}</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Social Media Handles */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Social Media Handles</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {kol.social_handles.length > 0 ? (
                                    <div className="space-y-4">
                                        {kol.social_handles.map((handle) => (
                                            <div key={handle.id} className="p-4 border rounded-lg">
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-lg">{getPlatformIcon(handle.platform)}</span>
                                                        <span className="font-medium capitalize">{handle.platform}</span>
                                                        {handle.is_verified && (
                                                            <Badge variant="secondary" className="text-xs">
                                                                ✓ Verified
                                                            </Badge>
                                                        )}
                                                        {!handle.is_active && (
                                                            <Badge variant="destructive" className="text-xs">
                                                                Inactive
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    {handle.url && (
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => window.open(handle.url, '_blank')}
                                                        >
                                                            <ExternalLink className="h-4 w-4" />
                                                        </Button>
                                                    )}
                                                </div>
                                                <div className="space-y-1 text-sm">
                                                    <p><span className="font-medium">Handle:</span> {handle.handle}</p>
                                                    <p><span className="font-medium">Followers:</span> {handle.follower_count.toLocaleString()}</p>
                                                    {handle.last_enriched_at && (
                                                        <p className="text-muted-foreground">
                                                            Last updated: {new Date(handle.last_enriched_at).toLocaleDateString()}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-muted-foreground">No social media handles added</p>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Tags & Metadata */}
                    <div className="space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Tags</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex flex-wrap gap-1">
                                    {kol.tags.map((tag) => (
                                        <Badge key={tag} variant="secondary" className="gap-1">
                                            {tag}
                                            <X
                                                className="h-3 w-3 cursor-pointer hover:text-destructive"
                                                onClick={() => handleRemoveTag(tag)}
                                            />
                                        </Badge>
                                    ))}
                                    {kol.tags.length === 0 && (
                                        <span className="text-muted-foreground text-sm">No tags added</span>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <Input
                                        placeholder="Add tag..."
                                        value={newTag}
                                        onChange={(e) => setNewTag(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                                        className="flex-1"
                                    />
                                    <Button
                                        size="sm"
                                        onClick={handleAddTag}
                                        disabled={!newTag.trim() || addTag.isPending}
                                    >
                                        <Plus className="h-4 w-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Statistics</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <label className="text-sm font-medium text-muted-foreground">Total Followers</label>
                                    <p className="text-2xl font-bold">
                                        {kol.social_handles.reduce((sum, handle) => sum + handle.follower_count, 0).toLocaleString()}
                                    </p>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-muted-foreground">Platforms</label>
                                    <p className="text-lg font-semibold">{kol.social_handles.length}</p>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-muted-foreground">Tier</label>
                                    <Badge className={getTierColor(kol.tier)}>
                                        {kol.tier}
                                    </Badge>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Metadata</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm">
                                <div>
                                    <span className="font-medium">Created:</span>
                                    <p className="text-muted-foreground">{new Date(kol.created_at).toLocaleString()}</p>
                                </div>
                                <div>
                                    <span className="font-medium">Last Updated:</span>
                                    <p className="text-muted-foreground">{new Date(kol.updated_at).toLocaleString()}</p>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}