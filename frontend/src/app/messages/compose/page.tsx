"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Send, Save, Wand2, FileText } from "lucide-react";
import { useCreateMessage, useGenerateMessageFromTemplate, useMessageTemplates, useSendMessage } from "@/hooks/useMessages";
import { useCampaigns } from "@/hooks/useCampaigns";
import { useKOLs } from "@/hooks/useKOLs";
import { useBriefs } from "@/hooks/useBriefs";
import { CreateMessageData } from "@/lib/api/messages";

interface MessageFormData {
    subject: string;
    content: string;
    message_type: 'email' | 'sms' | 'line' | 'discord' | 'whatsapp';
    priority: 'low' | 'normal' | 'high' | 'urgent';
    recipient_email: string;
    recipient_phone: string;
    sender_email: string;
    sender_name: string;
    kol_id: string;
    campaign_id: string;
    brief_id: string;
    template_id: string;
    scheduled_at: string;
}

export default function ComposeMessagePage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
    const [showTemplatePreview, setShowTemplatePreview] = useState(false);

    const createMessage = useCreateMessage();
    const sendMessage = useSendMessage();
    const generateFromTemplate = useGenerateMessageFromTemplate();
    const { data: campaigns } = useCampaigns({ page_size: 100 });
    const { data: kols } = useKOLs({ page_size: 100 });
    const { data: briefs } = useBriefs({ page_size: 100 });
    const { data: templates } = useMessageTemplates({ is_active: true, page_size: 50 });

    const { register, handleSubmit, formState: { errors }, setValue, watch, reset } = useForm<MessageFormData>({
        defaultValues: {
            message_type: 'email',
            priority: 'normal',
            kol_id: searchParams?.get('kol_id') || '',
            campaign_id: searchParams?.get('campaign_id') || '',
            brief_id: searchParams?.get('brief_id') || '',
            template_id: '',
            subject: '',
            content: '',
            recipient_email: '',
            recipient_phone: '',
            sender_email: '',
            sender_name: '',
            scheduled_at: '',
        },
    });

    const watchedKolId = watch('kol_id');
    const watchedCampaignId = watch('campaign_id');
    const watchedBriefId = watch('brief_id');
    const watchedTemplateId = watch('template_id');
    const watchedMessageType = watch('message_type');

    // Auto-populate recipient info when KOL is selected
    useEffect(() => {
        if (watchedKolId) {
            const kol = kols?.kols?.find(k => k.id === parseInt(watchedKolId));
            if (kol) {
                if (watchedMessageType === 'email' && kol.email) {
                    setValue('recipient_email', kol.email);
                }
                if (watchedMessageType === 'sms' && kol.phone) {
                    setValue('recipient_phone', kol.phone);
                }
            }
        }
    }, [watchedKolId, watchedMessageType, kols, setValue]);

    // Handle template selection
    useEffect(() => {
        if (watchedTemplateId) {
            const template = templates?.templates?.find(t => t.id === parseInt(watchedTemplateId));
            setSelectedTemplate(template);

            if (template) {
                setValue('content', template.content);
                if (template.subject) {
                    setValue('subject', template.subject);
                }
                setValue('message_type', template.message_type);
            }
        } else {
            setSelectedTemplate(null);
        }
    }, [watchedTemplateId, templates, setValue]);

    const onSubmit = async (data: MessageFormData, sendImmediately: boolean = false) => {
        try {
            // Prepare message data
            const messageData: CreateMessageData = {
                subject: data.subject,
                content: data.content,
                message_type: data.message_type,
                priority: data.priority,
                recipient_email: data.recipient_email || undefined,
                recipient_phone: data.recipient_phone || undefined,
                sender_email: data.sender_email || undefined,
                sender_name: data.sender_name || undefined,
                kol_id: data.kol_id ? parseInt(data.kol_id) : undefined,
                campaign_id: data.campaign_id ? parseInt(data.campaign_id) : undefined,
                brief_id: data.brief_id ? parseInt(data.brief_id) : undefined,
                template_id: data.template_id ? parseInt(data.template_id) : undefined,
                scheduled_at: data.scheduled_at || undefined,
            };

            const message = await createMessage.mutateAsync(messageData);

            if (sendImmediately) {
                await sendMessage.mutateAsync({ id: message.id });
            }

            router.push('/messages');
        } catch (error) {
            console.error('Failed to create/send message:', error);
        }
    };

    const handleGenerateFromTemplate = async () => {
        if (!selectedTemplate || !watchedKolId) return;

        try {
            const kol = kols?.kols?.find(k => k.id === parseInt(watchedKolId));
            const campaign = campaigns?.campaigns?.find(c => c.id === parseInt(watchedCampaignId));
            const brief = briefs?.briefs?.find(b => b.id === parseInt(watchedBriefId));

            const variableValues = {
                kol_name: kol?.name || '',
                kol_email: kol?.email || '',
                campaign_name: campaign?.name || '',
                campaign_objectives: campaign?.objectives || '',
                brief_title: brief?.title || '',
            };

            const message = await generateFromTemplate.mutateAsync({
                template_id: selectedTemplate.id,
                kol_id: parseInt(watchedKolId),
                campaign_id: watchedCampaignId ? parseInt(watchedCampaignId) : undefined,
                brief_id: watchedBriefId ? parseInt(watchedBriefId) : undefined,
                variable_values: variableValues,
            });

            router.push(`/messages/${message.id}`);
        } catch (error) {
            console.error('Failed to generate message from template:', error);
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
                        <h1 className="text-3xl font-bold">Compose Message</h1>
                        <p className="text-muted-foreground">Create and send a message to KOLs</p>
                    </div>
                </div>

                <form className="space-y-6">
                    {/* Basic Information */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Message Details</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="message_type">Message Type *</Label>
                                    <select
                                        id="message_type"
                                        {...register("message_type", { required: "Message type is required" })}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="email">Email</option>
                                        <option value="sms">SMS</option>
                                        <option value="line">Line</option>
                                        <option value="discord">Discord</option>
                                        <option value="whatsapp">WhatsApp</option>
                                    </select>
                                    {errors.message_type && (
                                        <p className="text-sm text-destructive">{errors.message_type.message}</p>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="priority">Priority</Label>
                                    <select
                                        id="priority"
                                        {...register("priority")}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="low">Low</option>
                                        <option value="normal">Normal</option>
                                        <option value="high">High</option>
                                        <option value="urgent">Urgent</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="kol_id">KOL</Label>
                                    <select
                                        id="kol_id"
                                        {...register("kol_id")}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="">Select KOL</option>
                                        {kols?.kols?.map((kol) => (
                                            <option key={kol.id} value={kol.id}>
                                                {kol.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="campaign_id">Campaign</Label>
                                    <select
                                        id="campaign_id"
                                        {...register("campaign_id")}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="">Select Campaign</option>
                                        {campaigns?.campaigns?.map((campaign) => (
                                            <option key={campaign.id} value={campaign.id}>
                                                {campaign.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="brief_id">Brief</Label>
                                    <select
                                        id="brief_id"
                                        {...register("brief_id")}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="">Select Brief</option>
                                        {briefs?.briefs?.map((brief) => (
                                            <option key={brief.id} value={brief.id}>
                                                {brief.title}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Template Selection */}
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <CardTitle>Template (Optional)</CardTitle>
                                {selectedTemplate && watchedKolId && (
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
                                    {templates?.templates?.filter(t => t.message_type === watchedMessageType).map((template) => (
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
                                            <div className="space-y-2">
                                                {selectedTemplate.subject && (
                                                    <div>
                                                        <p className="text-sm font-medium">Subject:</p>
                                                        <p className="text-sm">{selectedTemplate.subject}</p>
                                                    </div>
                                                )}
                                                <div>
                                                    <p className="text-sm font-medium">Content:</p>
                                                    <pre className="text-sm whitespace-pre-wrap">{selectedTemplate.content}</pre>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Recipient Information */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Recipient Information</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {watchedMessageType === 'email' && (
                                <div className="space-y-2">
                                    <Label htmlFor="recipient_email">Recipient Email *</Label>
                                    <Input
                                        id="recipient_email"
                                        type="email"
                                        {...register("recipient_email", {
                                            required: watchedMessageType === 'email' ? "Recipient email is required" : false
                                        })}
                                        placeholder="recipient@example.com"
                                    />
                                    {errors.recipient_email && (
                                        <p className="text-sm text-destructive">{errors.recipient_email.message}</p>
                                    )}
                                </div>
                            )}

                            {watchedMessageType === 'sms' && (
                                <div className="space-y-2">
                                    <Label htmlFor="recipient_phone">Recipient Phone *</Label>
                                    <Input
                                        id="recipient_phone"
                                        {...register("recipient_phone", {
                                            required: watchedMessageType === 'sms' ? "Recipient phone is required" : false
                                        })}
                                        placeholder="+1234567890"
                                    />
                                    {errors.recipient_phone && (
                                        <p className="text-sm text-destructive">{errors.recipient_phone.message}</p>
                                    )}
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="sender_email">Sender Email</Label>
                                    <Input
                                        id="sender_email"
                                        type="email"
                                        {...register("sender_email")}
                                        placeholder="sender@company.com"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="sender_name">Sender Name</Label>
                                    <Input
                                        id="sender_name"
                                        {...register("sender_name")}
                                        placeholder="Your Name"
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Message Content */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Message Content</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {watchedMessageType === 'email' && (
                                <div className="space-y-2">
                                    <Label htmlFor="subject">Subject *</Label>
                                    <Input
                                        id="subject"
                                        {...register("subject", {
                                            required: watchedMessageType === 'email' ? "Subject is required" : false
                                        })}
                                        placeholder="Message subject"
                                    />
                                    {errors.subject && (
                                        <p className="text-sm text-destructive">{errors.subject.message}</p>
                                    )}
                                </div>
                            )}

                            <div className="space-y-2">
                                <Label htmlFor="content">Message Content *</Label>
                                <textarea
                                    id="content"
                                    {...register("content", { required: "Message content is required" })}
                                    className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    placeholder="Type your message here..."
                                />
                                {errors.content && (
                                    <p className="text-sm text-destructive">{errors.content.message}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="scheduled_at">Schedule Send (Optional)</Label>
                                <Input
                                    id="scheduled_at"
                                    type="datetime-local"
                                    {...register("scheduled_at")}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Error Display */}
                    {(createMessage.error || sendMessage.error) && (
                        <div className="p-4 bg-destructive/10 text-destructive rounded-md">
                            {createMessage.error instanceof Error ? createMessage.error.message :
                                sendMessage.error instanceof Error ? sendMessage.error.message : 'Failed to create/send message'}
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
                            type="button"
                            variant="outline"
                            onClick={handleSubmit((data) => onSubmit(data, false))}
                            disabled={createMessage.isPending}
                            className="flex-1"
                        >
                            <Save className="h-4 w-4 mr-2" />
                            {createMessage.isPending ? "Saving..." : "Save Draft"}
                        </Button>
                        <Button
                            type="button"
                            onClick={handleSubmit((data) => onSubmit(data, true))}
                            disabled={createMessage.isPending || sendMessage.isPending}
                            className="flex-1"
                        >
                            <Send className="h-4 w-4 mr-2" />
                            {(createMessage.isPending || sendMessage.isPending) ? "Sending..." : "Send Now"}
                        </Button>
                    </div>
                </form>
            </div>
        </DashboardLayout>
    );
}