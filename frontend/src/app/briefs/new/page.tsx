"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, FileText, Wand2 } from "lucide-react";
import { useCreateBrief, useGenerateBriefFromTemplate, useBriefTemplates } from "@/hooks/useBriefs";
import { useCampaigns } from "@/hooks/useCampaigns";
import { useKOLs } from "@/hooks/useKOLs";
import { CreateBriefData } from "@/lib/api/briefs";

interface BriefFormData {
    title: string;
    content: string;
    campaign_id: string;
    kol_id: string;
    template_id: string;
    internal_notes: string;
    deliverables: string;
    timeline: string;
    compensation: string;
    requirements: string;
}

export default function NewBriefPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
    const [showTemplatePreview, setShowTemplatePreview] = useState(false);

    const createBrief = useCreateBrief();
    const generateFromTemplate = useGenerateBriefFromTemplate();
    const { data: campaigns } = useCampaigns({ page_size: 100 });
    const { data: kols } = useKOLs({ page_size: 100 });
    const { data: templates } = useBriefTemplates({ is_active: true, page_size: 50 });

    const { register, handleSubmit, formState: { errors }, setValue, watch, reset } = useForm<BriefFormData>({
        defaultValues: {
            campaign_id: searchParams?.get('campaign_id') || '',
            kol_id: searchParams?.get('kol_id') || '',
            template_id: '',
            title: '',
            content: '',
            internal_notes: '',
            deliverables: '',
            timeline: '',
            compensation: '',
            requirements: '',
        },
    });

    const watchedCampaignId = watch('campaign_id');
    const watchedKolId = watch('kol_id');
    const watchedTemplateId = watch('template_id');

    // Auto-generate title when campaign and KOL are selected
    useEffect(() => {
        if (watchedCampaignId && watchedKolId) {
            const campaign = campaigns?.campaigns?.find(c => c.id === parseInt(watchedCampaignId));
            const kol = kols?.kols?.find(k => k.id === parseInt(watchedKolId));

            if (campaign && kol) {
                setValue('title', `${campaign.name} - ${kol.name} Brief`);
            }
        }
    }, [watchedCampaignId, watchedKolId, campaigns, kols, setValue]);

    // Handle template selection
    useEffect(() => {
        if (watchedTemplateId) {
            const template = templates?.templates?.find(t => t.id === parseInt(watchedTemplateId));
            setSelectedTemplate(template);

            if (template) {
                setValue('content', template.content);
            }
        } else {
            setSelectedTemplate(null);
        }
    }, [watchedTemplateId, templates, setValue]);

    const onSubmit = async (data: BriefFormData) => {
        try {
            // Prepare brief data
            const briefData: CreateBriefData = {
                title: data.title,
                content: data.content,
                campaign_id: parseInt(data.campaign_id),
                kol_id: parseInt(data.kol_id),
                template_id: data.template_id ? parseInt(data.template_id) : undefined,
                internal_notes: data.internal_notes,
                brief_data: {
                    deliverables: data.deliverables.split('\n').filter(d => d.trim()),
                    timeline: data.timeline,
                    compensation: data.compensation,
                    requirements: data.requirements.split('\n').filter(r => r.trim()),
                }
            };

            await createBrief.mutateAsync(briefData);
            router.push('/briefs');
        } catch (error) {
            console.error('Failed to create brief:', error);
        }
    };

    const handleGenerateFromTemplate = async () => {
        if (!selectedTemplate || !watchedCampaignId || !watchedKolId) return;

        try {
            const campaign = campaigns?.campaigns?.find(c => c.id === parseInt(watchedCampaignId));
            const kol = kols?.kols?.find(k => k.id === parseInt(watchedKolId));

            const variableValues = {
                campaign_name: campaign?.name || '',
                kol_name: kol?.name || '',
                campaign_objectives: campaign?.objectives || '',
                campaign_budget: campaign?.total_budget?.toString() || '',
                campaign_start_date: campaign?.start_date || '',
                campaign_end_date: campaign?.end_date || '',
            };

            const brief = await generateFromTemplate.mutateAsync({
                template_id: selectedTemplate.id,
                campaign_id: parseInt(watchedCampaignId),
                kol_id: parseInt(watchedKolId),
                variable_values: variableValues,
            });

            router.push(`/briefs/${brief.id}`);
        } catch (error) {
            console.error('Failed to generate brief from template:', error);
        }
    };

    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold">Create New Brief</h1>
                        <p className="text-muted-foreground">Create a detailed brief for KOL campaign</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    {/* Basic Information */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Basic Information</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="campaign_id">Campaign *</Label>
                                    <select
                                        id="campaign_id"
                                        {...register("campaign_id", { required: "Campaign is required" })}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="">Select Campaign</option>
                                        {campaigns?.campaigns?.map((campaign) => (
                                            <option key={campaign.id} value={campaign.id}>
                                                {campaign.name}
                                            </option>
                                        ))}
                                    </select>
                                    {errors.campaign_id && (
                                        <p className="text-sm text-destructive">{errors.campaign_id.message}</p>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="kol_id">KOL *</Label>
                                    <select
                                        id="kol_id"
                                        {...register("kol_id", { required: "KOL is required" })}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="">Select KOL</option>
                                        {kols?.kols?.map((kol) => (
                                            <option key={kol.id} value={kol.id}>
                                                {kol.name}
                                            </option>
                                        ))}
                                    </select>
                                    {errors.kol_id && (
                                        <p className="text-sm text-destructive">{errors.kol_id.message}</p>
                                    )}
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="title">Brief Title *</Label>
                                <Input
                                    id="title"
                                    {...register("title", { required: "Title is required" })}
                                    placeholder="Campaign Name - KOL Name Brief"
                                />
                                {errors.title && (
                                    <p className="text-sm text-destructive">{errors.title.message}</p>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Template Selection */}
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <CardTitle>Template (Optional)</CardTitle>
                                {selectedTemplate && watchedCampaignId && watchedKolId && (
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={handleGenerateFromTemplate}
                                        disabled={generateFromTemplate.isPending}
                                    >
                                        <Wand2 className="h-4 w-4 mr-2" />
                                        {generateFromTemplate.isPending ? 'Generating...' : 'Generate from Template'}
                                    </Button>
                                )}
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="template_id">Select Template</Label>
                                <select
                                    id="template_id"
                                    {...register("template_id")}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                >
                                    <option value="">No Template (Create from scratch)</option>
                                    {templates?.templates?.map((template) => (
                                        <option key={template.id} value={template.id}>
                                            {template.name} {template.category && `(${template.category})`}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {selectedTemplate && (
                                <div className="p-4 bg-blue-50 rounded-lg">
                                    <div className="flex items-start gap-3">
                                        <FileText className="h-5 w-5 text-blue-600 mt-0.5" />
                                        <div className="flex-1">
                                            <h4 className="font-medium text-blue-900">{selectedTemplate.name}</h4>
                                            {selectedTemplate.description && (
                                                <p className="text-sm text-blue-700 mt-1">{selectedTemplate.description}</p>
                                            )}
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => setShowTemplatePreview(!showTemplatePreview)}
                                                className="mt-2 text-blue-600 hover:text-blue-800"
                                            >
                                                {showTemplatePreview ? 'Hide' : 'Show'} Template Preview
                                            </Button>
                                        </div>
                                    </div>
                                    {showTemplatePreview && (
                                        <div className="mt-4 p-3 bg-white rounded border">
                                            <pre className="text-sm whitespace-pre-wrap">{selectedTemplate.content}</pre>
                                        </div>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Brief Content */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Brief Content</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="content">Brief Description *</Label>
                                <textarea
                                    id="content"
                                    {...register("content", { required: "Brief content is required" })}
                                    className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    placeholder="Describe the campaign objectives, brand message, and overall requirements..."
                                />
                                {errors.content && (
                                    <p className="text-sm text-destructive">{errors.content.message}</p>
                                )}
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="deliverables">Deliverables (one per line)</Label>
                                    <textarea
                                        id="deliverables"
                                        {...register("deliverables")}
                                        className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                        placeholder="1 Instagram post&#10;3 Instagram stories&#10;1 TikTok video"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="requirements">Requirements (one per line)</Label>
                                    <textarea
                                        id="requirements"
                                        {...register("requirements")}
                                        className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                        placeholder="Must include product shot&#10;Use hashtag #brand&#10;Tag @brandaccount"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="timeline">Timeline</Label>
                                    <Input
                                        id="timeline"
                                        {...register("timeline")}
                                        placeholder="e.g., Post by January 15, 2024"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="compensation">Compensation</Label>
                                    <Input
                                        id="compensation"
                                        {...register("compensation")}
                                        placeholder="e.g., $500 + product"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="internal_notes">Internal Notes</Label>
                                <textarea
                                    id="internal_notes"
                                    {...register("internal_notes")}
                                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    placeholder="Internal notes for team members (not visible to KOL)..."
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Error Display */}
                    {createBrief.error && (
                        <div className="p-4 bg-destructive/10 text-destructive rounded-md">
                            {createBrief.error instanceof Error ? createBrief.error.message : 'Failed to create brief'}
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-4">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => router.back()}
                            className="flex-1"
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            disabled={createBrief.isPending}
                            className="flex-1"
                        >
                            {createBrief.isPending ? "Creating..." : "Create Brief"}
                        </Button>
                    </div>
                </form>
            </div>
        </DashboardLayout>
    );
}