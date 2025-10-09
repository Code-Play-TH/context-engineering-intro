"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Filter, X, Mail, MessageSquare, Send, Clock, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { useMessages, useMessageStats } from "@/hooks/useMessages";
import { MessageFilters } from "@/lib/api/messages";

export default function MessagesPage() {
    const router = useRouter();
    const [showFilters, setShowFilters] = useState(false);

    // Filter state
    const [filters, setFilters] = useState<MessageFilters>({
        page: 1,
        page_size: 20,
    });

    // Temporary filter inputs
    const [tempFilters, setTempFilters] = useState({
        search: '',
        message_type: '' as any,
        status: '' as any,
        priority: '' as any,
        campaign_id: '',
        kol_id: '',
    });

    const { data, isLoading, error } = useMessages(filters);
    const { data: stats } = useMessageStats();

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            draft: "bg-gray-100 text-gray-800",
            queued: "bg-blue-100 text-blue-800",
            sending: "bg-yellow-100 text-yellow-800",
            sent: "bg-green-100 text-green-800",
            delivered: "bg-emerald-100 text-emerald-800",
            read: "bg-purple-100 text-purple-800",
            failed: "bg-red-100 text-red-800",
            bounced: "bg-orange-100 text-orange-800",
        };
        return colors[status] || "bg-gray-100 text-gray-800";
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'draft':
                return <MessageSquare className="h-4 w-4" />;
            case 'queued':
            case 'sending':
                return <Clock className="h-4 w-4" />;
            case 'sent':
            case 'delivered':
            case 'read':
                return <CheckCircle className="h-4 w-4" />;
            case 'failed':
            case 'bounced':
                return <XCircle className="h-4 w-4" />;
            default:
                return <MessageSquare className="h-4 w-4" />;
        }
    };

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'email':
                return <Mail className="h-4 w-4" />;
            case 'sms':
                return <MessageSquare className="h-4 w-4" />;
            default:
                return <MessageSquare className="h-4 w-4" />;
        }
    };

    const getPriorityColor = (priority: string) => {
        const colors: Record<string, string> = {
            low: "bg-gray-100 text-gray-600",
            normal: "bg-blue-100 text-blue-600",
            high: "bg-yellow-100 text-yellow-600",
            urgent: "bg-red-100 text-red-600",
        };
        return colors[priority] || "bg-blue-100 text-blue-600";
    };

    const applyFilters = () => {
        const newFilters: MessageFilters = {
            ...filters,
            page: 1,
            search: tempFilters.search || undefined,
            message_type: tempFilters.message_type || undefined,
            status: tempFilters.status || undefined,
            priority: tempFilters.priority || undefined,
            campaign_id: tempFilters.campaign_id ? parseInt(tempFilters.campaign_id) : undefined,
            kol_id: tempFilters.kol_id ? parseInt(tempFilters.kol_id) : undefined,
        };
        setFilters(newFilters);
        setShowFilters(false);
    };

    const clearFilters = () => {
        setTempFilters({
            search: '',
            message_type: '',
            status: '',
            priority: '',
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
        if (filters.message_type) count++;
        if (filters.status) count++;
        if (filters.priority) count++;
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
                        <h1 className="text-3xl font-bold">Messages</h1>
                        <p className="text-muted-foreground">
                            Manage communications with KOLs
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            onClick={() => router.push("/messages/templates")}
                        >
                            <MessageSquare className="h-4 w-4 mr-2" />
                            Templates
                        </Button>
                        <Button onClick={() => router.push("/messages/compose")}>
                            <Plus className="h-4 w-4 mr-2" />
                            Compose Message
                        </Button>
                    </div>
                </div>

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center">
                                    <MessageSquare className="h-8 w-8 text-blue-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-muted-foreground">Total Messages</p>
                                        <p className="text-2xl font-bold">{stats.total_messages}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center">
                                    <Send className="h-8 w-8 text-green-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-muted-foreground">Sent</p>
                                        <p className="text-2xl font-bold">{stats.by_status.sent || 0}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center">
                                    <CheckCircle className="h-8 w-8 text-emerald-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-muted-foreground">Delivery Rate</p>
                                        <p className="text-2xl font-bold">{stats.delivery_rate}%</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center">
                                    <AlertTriangle className="h-8 w-8 text-red-600" />
                                    <div className="ml-4">
                                        <p className="text-sm font-medium text-muted-foreground">Failed</p>
                                        <p className="text-2xl font-bold">{stats.by_status.failed || 0}</p>
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
                                        placeholder="Search messages by subject or content..."
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
                                    {filters.message_type && (
                                        <Badge variant="secondary" className="gap-1">
                                            Type: {filters.message_type}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => setFilters(prev => ({ ...prev, message_type: undefined }))}
                                            />
                                        </Badge>
                                    )}
                                    {filters.status && (
                                        <Badge variant="secondary" className="gap-1">
                                            Status: {filters.status}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => setFilters(prev => ({ ...prev, status: undefined }))}
                                            />
                                        </Badge>
                                    )}
                                    {filters.priority && (
                                        <Badge variant="secondary" className="gap-1">
                                            Priority: {filters.priority}
                                            <X
                                                className="h-3 w-3 cursor-pointer"
                                                onClick={() => setFilters(prev => ({ ...prev, priority: undefined }))}
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
                                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Type</label>
                                            <select
                                                value={tempFilters.message_type}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, message_type: e.target.value }))}
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                            >
                                                <option value="">All Types</option>
                                                <option value="email">Email</option>
                                                <option value="sms">SMS</option>
                                                <option value="line">Line</option>
                                                <option value="discord">Discord</option>
                                                <option value="whatsapp">WhatsApp</option>
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Status</label>
                                            <select
                                                value={tempFilters.status}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, status: e.target.value }))}
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                            >
                                                <option value="">All Statuses</option>
                                                <option value="draft">Draft</option>
                                                <option value="queued">Queued</option>
                                                <option value="sending">Sending</option>
                                                <option value="sent">Sent</option>
                                                <option value="delivered">Delivered</option>
                                                <option value="read">Read</option>
                                                <option value="failed">Failed</option>
                                                <option value="bounced">Bounced</option>
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Priority</label>
                                            <select
                                                value={tempFilters.priority}
                                                onChange={(e) => setTempFilters(prev => ({ ...prev, priority: e.target.value }))}
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                            >
                                                <option value="">All Priorities</option>
                                                <option value="low">Low</option>
                                                <option value="normal">Normal</option>
                                                <option value="high">High</option>
                                                <option value="urgent">Urgent</option>
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
                                Failed to load messages. Please try again.
                            </div>
                        ) : data?.messages?.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                {activeFilterCount > 0 ? 'No messages match your filters.' : 'No messages found. Compose your first message to get started.'}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {data?.messages?.map((message) => (
                                    <div
                                        key={message.id}
                                        onClick={() => router.push(`/messages/${message.id}`)}
                                        className="p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <div className="flex items-center gap-1">
                                                        {getTypeIcon(message.message_type)}
                                                        <span className="text-sm font-medium capitalize">{message.message_type}</span>
                                                    </div>
                                                    <div className="flex items-center gap-1">
                                                        {getStatusIcon(message.status)}
                                                        <Badge className={getStatusColor(message.status)}>
                                                            {message.status}
                                                        </Badge>
                                                    </div>
                                                    <Badge className={getPriorityColor(message.priority)}>
                                                        {message.priority}
                                                    </Badge>
                                                </div>
                                                <h3 className="font-semibold text-lg mb-1">
                                                    {message.subject || 'No Subject'}
                                                </h3>
                                                <div className="space-y-1 text-sm text-muted-foreground">
                                                    <p>📧 To: {message.recipient_email || message.kol_name || 'Unknown'}</p>
                                                    {message.campaign_name && <p>📋 Campaign: {message.campaign_name}</p>}
                                                    {message.brief_title && <p>📄 Brief: {message.brief_title}</p>}
                                                    {message.template_name && <p>📝 Template: {message.template_name}</p>}
                                                    <p>👨‍💼 Sent by: {message.sender_name}</p>
                                                </div>
                                                <div className="mt-3 text-sm text-muted-foreground">
                                                    <p className="line-clamp-2">{message.content.substring(0, 150)}...</p>
                                                </div>
                                                <div className="mt-2 text-xs text-muted-foreground">
                                                    Created: {new Date(message.created_at).toLocaleDateString()}
                                                    {message.sent_at && (
                                                        <span> • Sent: {new Date(message.sent_at).toLocaleDateString()}</span>
                                                    )}
                                                    {message.delivered_at && (
                                                        <span> • Delivered: {new Date(message.delivered_at).toLocaleDateString()}</span>
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
                                    {Math.min((filters.page || 1) * (filters.page_size || 20), data.total)} of {data.total} messages
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