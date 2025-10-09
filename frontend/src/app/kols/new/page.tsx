"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useFieldArray } from "react-hook-form";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, ArrowLeft } from "lucide-react";
import { useCreateKOL } from "@/hooks/useKOLs";
import { CreateKOLData } from "@/lib/api/kols";

interface KOLFormData {
    name: string;
    email: string;
    phone: string;
    location: string;
    niche: string;
    tags: string;
    notes: string;
    social_handles: Array<{
        platform: 'instagram' | 'tiktok' | 'youtube' | 'twitter' | 'facebook';
        handle: string;
        url: string;
        follower_count: number;
        is_verified: boolean;
        is_active: boolean;
    }>;
}

export default function NewKOLPage() {
    const router = useRouter();
    const createKOL = useCreateKOL();

    const { register, control, handleSubmit, formState: { errors } } = useForm<KOLFormData>({
        defaultValues: {
            social_handles: [{ platform: "instagram", handle: "", url: "", follower_count: 0, is_verified: false, is_active: true }],
        },
    });

    const { fields, append, remove } = useFieldArray({
        control,
        name: "social_handles",
    });

    const onSubmit = async (data: KOLFormData) => {
        try {
            const payload: CreateKOLData = {
                ...data,
                niche: data.niche ? data.niche.split(",").map((n) => n.trim()).filter(n => n) : [],
                tags: data.tags ? data.tags.split(",").map((t) => t.trim()).filter(t => t) : [],
                social_handles: data.social_handles.filter(handle => handle.handle.trim()),
            };

            await createKOL.mutateAsync(payload);
            router.push("/kols");
        } catch (error) {
            console.error("Failed to create KOL:", error);
        }
    };

    return (
        <DashboardLayout>
            <div className="max-w-3xl mx-auto space-y-6">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold">Add New KOL</h1>
                        <p className="text-muted-foreground">Create a new influencer profile</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Basic Information</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Name *</Label>
                                <Input
                                    id="name"
                                    {...register("name", { required: "Name is required" })}
                                    placeholder="John Influencer"
                                />
                                {errors.name && (
                                    <p className="text-sm text-destructive">{errors.name.message}</p>
                                )}
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        {...register("email")}
                                        placeholder="john@example.com"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="phone">Phone</Label>
                                    <Input
                                        id="phone"
                                        {...register("phone")}
                                        placeholder="+1234567890"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="location">Location</Label>
                                <Input
                                    id="location"
                                    {...register("location")}
                                    placeholder="Bangkok, Thailand"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="niche">Niche (comma-separated)</Label>
                                <Input
                                    id="niche"
                                    {...register("niche")}
                                    placeholder="fashion, lifestyle, beauty"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="tags">Tags (comma-separated)</Label>
                                <Input
                                    id="tags"
                                    {...register("tags")}
                                    placeholder="micro-influencer, fashion"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="notes">Notes</Label>
                                <textarea
                                    id="notes"
                                    {...register("notes")}
                                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                    placeholder="Additional notes about this KOL..."
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <CardTitle>Social Media Handles *</CardTitle>
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() =>
                                        append({ platform: "instagram", handle: "", url: "", follower_count: 0, is_verified: false, is_active: true })
                                    }
                                >
                                    <Plus className="h-4 w-4 mr-2" />
                                    Add Handle
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {fields.map((field, index) => (
                                <div key={field.id} className="p-4 border rounded-lg space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h4 className="font-medium">Handle {index + 1}</h4>
                                        {fields.length > 1 && (
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => remove(index)}
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        )}
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Platform</Label>
                                            <select
                                                {...register(`social_handles.${index}.platform`)}
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                            >
                                                <option value="instagram">Instagram</option>
                                                <option value="tiktok">TikTok</option>
                                                <option value="youtube">YouTube</option>
                                                <option value="twitter">Twitter</option>
                                                <option value="facebook">Facebook</option>
                                            </select>
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Handle/Username</Label>
                                            <Input
                                                {...register(`social_handles.${index}.handle`, {
                                                    required: "Handle is required",
                                                })}
                                                placeholder="@username"
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Profile URL</Label>
                                            <Input
                                                {...register(`social_handles.${index}.url`)}
                                                placeholder="https://..."
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Follower Count</Label>
                                            <Input
                                                type="number"
                                                {...register(`social_handles.${index}.follower_count`, {
                                                    valueAsNumber: true,
                                                })}
                                                placeholder="50000"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                id={`verified-${index}`}
                                                {...register(`social_handles.${index}.is_verified`)}
                                                className="h-4 w-4 rounded border-gray-300"
                                            />
                                            <Label htmlFor={`verified-${index}`}>Verified Account</Label>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                id={`active-${index}`}
                                                {...register(`social_handles.${index}.is_active`)}
                                                className="h-4 w-4 rounded border-gray-300"
                                                defaultChecked
                                            />
                                            <Label htmlFor={`active-${index}`}>Active Account</Label>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>

                    {createKOL.error && (
                        <div className="p-4 bg-destructive/10 text-destructive rounded-md">
                            {createKOL.error instanceof Error ? createKOL.error.message : 'Failed to create KOL'}
                        </div>
                    )}

                    <div className="flex gap-4">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => router.back()}
                            className="flex-1"
                        >
                            Cancel
                        </Button>
                        <Button type="submit" disabled={createKOL.isPending} className="flex-1">
                            {createKOL.isPending ? "Creating..." : "Create KOL"}
                        </Button>
                    </div>
                </form>
            </div>
        </DashboardLayout>
    );
}
