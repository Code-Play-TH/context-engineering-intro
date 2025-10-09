"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useBrief, useUpdateBriefStatus, useDeleteBrief } from "@/hooks/useBriefs";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Edit, Trash2, Send, CheckCircle, XCircle, Clock, FileText, MessageSquare } from "lucide-react";
import { BriefStatusUpdate } from "@/lib/api/briefs";

interface BriefDetailPageProps {
    params: {
        id: string;
    };
}

export default function BriefDetailPage({ params }: BriefDetailPageProps) {
    const router = useRouter();
    const briefId = parseInt(params.id);

    const [statusNotes, setStatusNotes] = useState("");
    const [showStatusUpdate, setShowStatusUpdate] = useState(false);

    const { data: brief, isLoading, error } = useBrief(briefId);
    const updateStatus = useUpdateBriefStatus();
    const deleteBrief = useDeleteBrief();

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
                return <FileText className="h-5 w-5" />;
            case 'pending_review':
                return <Clock className="h-5 w-5" />;
            case 'approved':
            case 'completed':
                return <CheckCircle className="h-5 w-5" />;
            case 'rejected':
                return <XCircle className="h-5 w-5" />;
            case 'sent':
                return <Send className="h-5 w-5" />;
            default:
                return <FileText className="h-5 w-5" />;
        }
    };

    const getAvailableStatusTransitions = (currentStatus: string) => {
        const transitions: Record<string, Array<{ status: string; label: string; color: string }>> = {
            draft: [
                { status: 'pending_review', label: 'Submit for Review', color: 'bg-yellow-600' },
            ],
            pending_review: [
                { status: 'approved', label: 'Approve', color: 'bg-green-600' },
                { status: 'rejected', label: 'Reject', color: 'bg-red-600' },
                { status: 'draft', label: 'Back to Draft', color: 'bg-gray-600' },
            ],
            approved: [
                { status: 'sent', label: 'Send to KOL', color: 'bg-blue-600' },
                { status: 'rejected', label: 'Reject', color: 'bg-red-600' },
            ],
            sent: [
                { status: 'acknowledged', label: 'Mark Acknowledged', color: 'bg-purple-600' },
                { status: 'in_progress', label: 'Mark In Progress', color: 'bg-orange-600' },
            ],
            acknowledged: [
                { status: 'in_progress', label: 'Mark In Progress', color: 'bg-orange-600' },
            ],
            in_progress: [
                { status: 'completed', label: 'Mark Completed', color: 'bg-emerald-600' },
            ],
            rejected: [
                { status: 'draft', label: 'Back to Draft', color: 'bg-gray-600' },
            ],
        };
        return transitions[currentStatus] || [];
    };

    const handleStatusUpdate = async (newStatus: string) => {
        try {
            const statusData: BriefStatusUpdate = {
                status: newStatus as any,
                notes: statusNotes || undefined,
            };

            await updateStatus.mutateAsync({ id: briefId, data: statusData });
            setStatusNotes("");
            setShowStatusUpdate(false);
        } catch (error) {
            console.error("Failed to update status:", error);
        }
    };

    const handleDelete = async () => {
        if (!brief || !confirm("Are you sure you want to delete this brief? This action cannot be undone.")) {
            return;
        }

        try {
            await deleteBrief.mutateAsync(brief.id);
            router.push("/briefs");
        } catch (error) {
            console.error("Failed to delete brief:", error);
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

    if (error || !brief) {
        return (
            <DashboardLayout>
                <div className="text-center py-8 text-destructive">
                    Failed to load brief details. Please try again.
                </div>
            </DashboardLayout>
        );
    }

    const availableTransitions = getAvailableStatusTransitions(brief.status);

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
                            <h1 className="text-3xl font-bold">{brief.title}</h1>
                            <div className="flex items-center gap-1">
                                {getStatusIcon(brief.status)}
                                <Badge className={getStatusColor(brief.status)}>
                                    {brief.status.replace('_', ' ')}
                                </Badge>
                            </div>
                        </div>
                        <p className="text-muted-foreground">
                            Brief ID: {brief.id} • Created {new Date(brief.created_at).toLocaleDateString()}
                        </p>
                    </div>
                    <div className="flex gap-2">
                        {brief.status === 'draft' && (
                            <Button variant="outline" onClick={() => router.push(`/briefs/${brief.id}/edit`)}>
                                <Edit className="h-4 w-4 mr-2" />
                                Edit
                            </Button>
                        )}
                        {brief.status === 'draft' && (
                            <Button variant="destructive" onClick={handleDelete}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                            </Button>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Brief Content */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Brief Content</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="prose max-w-none">
                                    <div className="whitespace-pre-wrap text-sm">{brief.content}</div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Brief Details */}
                        {brief.brief_data && Object.keys(brief.brief_data).length > 0 && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Brief Details</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {brief.brief_data.deliverables && brief.brief_data.deliverables.length > 0 && (
                                        <div>
                                            <h4 className="font-medium mb-2">Deliverables</h4>
                                            <ul className="list-disc list-inside space-y-1 text-sm">
                                                {brief.brief_data.deliverables.map((deliverable: string, index: number) => (
                                                    <li key={index}>{deliverable}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {brief.brief_data.requirements && brief.brief_data.requirements.length > 0 && (
                                        <div>
                                            <h4 className="font-medium mb-2">Requirements</h4>
                                            <ul className="list-disc list-inside space-y-1 text-sm">
                                                {brief.brief_data.requirements.map((requirement: string, index: number) => (
                                                    <li key={index}>{requirement}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-2 gap-4">
                                        {brief.brief_data.timeline && (
                                            <div>
                                                <h4 className="font-medium mb-1">Timeline</h4>
                                                <p className="text-sm text-muted-foreground">{brief.brief_data.timeline}</p>
                                            </div>
                                        )}

                                        {brief.brief_data.compensation && (
                                            <div>
                                                <h4 className="font-medium mb-1">Compensation</h4>
                                                <p className="text-sm text-muted-foreground">{brief.brief_data.compensation}</p>
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* KOL Feedback */}
                        {brief.kol_feedback && (
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <MessageSquare className="h-5 w-5" />
                                        KOL Feedback
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="p-4 bg-blue-50 rounded-lg">
                                        <p className="text-sm whitespace-pre-wrap">{brief.kol_feedback}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Internal Notes */}
                        {brief.internal_notes && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Internal Notes</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <p className="text-sm whitespace-pre-wrap">{brief.internal_notes}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Status Actions */}
                        {availableTransitions.length > 0 && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Status Actions</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    {availableTransitions.map((transition) => (
                                        <Button
                                            key={transition.status}
                                            onClick={() => handleStatusUpdate(transition.status)}
                                            disabled={updateStatus.isPending}
                                            className={`w-full ${transition.color} hover:opacity-90`}
                                        >
                                            {transition.label}
                                        </Button>
                                    ))}

                                    {showStatusUpdate && (
                                        <div className="space-y-2 pt-2 border-t">
                                            <label className="text-sm font-medium">Add Notes (Optional)</label>
                                            <textarea
                                                value={statusNotes}
                                                onChange={(e) => setStatusNotes(e.target.value)}
                                                className="w-full p-2 text-sm border rounded"
                                                placeholder="Add notes about this status change..."
                                                rows={3}
                                            />
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        )}

                        {/* Brief Information */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Brief Information</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <label className="text-sm font-medium text-muted-foreground">Campaign</label>
                                    <p className="mt-1">{brief.campaign_name}</p>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-muted-foreground">KOL</label>
                                    <p className="mt-1">{brief.kol_name}</p>
                                </div>
                                {brief.template_name && (
                                    <div>
                                        <label className="text-sm font-medium text-muted-foreground">Template</label>
                                        <p className="mt-1">{brief.template_name}</p>
                                    </div>
                                )}
                                <div>
                                    <label className="text-sm font-medium text-muted-foreground">Created By</label>
                                    <p className="mt-1">{brief.creator_name}</p>
                                </div>
                                {brief.approver_name && (
                                    <div>
                                        <label className="text-sm font-medium text-muted-foreground">Approved By</label>
                                        <p className="mt-1">{brief.approver_name}</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Timeline */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Timeline</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3 text-sm">
                                <div>
                                    <span className="font-medium">Created:</span>
                                    <p className="text-muted-foreground">{new Date(brief.created_at).toLocaleString()}</p>
                                </div>
                                {brief.updated_at && (
                                    <div>
                                        <span className="font-medium">Last Updated:</span>
                                        <p className="text-muted-foreground">{new Date(brief.updated_at).toLocaleString()}</p>
                                    </div>
                                )}
                                {brief.approved_at && (
                                    <div>
                                        <span className="font-medium">Approved:</span>
                                        <p className="text-muted-foreground">{new Date(brief.approved_at).toLocaleString()}</p>
                                    </div>
                                )}
                                {brief.sent_at && (
                                    <div>
                                        <span className="font-medium">Sent:</span>
                                        <p className="text-muted-foreground">{new Date(brief.sent_at).toLocaleString()}</p>
                                    </div>
                                )}
                                {brief.acknowledged_at && (
                                    <div>
                                        <span className="font-medium">Acknowledged:</span>
                                        <p className="text-muted-foreground">{new Date(brief.acknowledged_at).toLocaleString()}</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}