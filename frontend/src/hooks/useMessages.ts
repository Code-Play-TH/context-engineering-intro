import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    messagesApi,
    MessageFilters,
    CreateMessageData,
    UpdateMessageData,
    MessageStatusUpdate,
    CreateMessageTemplateData,
    UpdateMessageTemplateData,
    GenerateMessageFromTemplate,
    BulkMessageCreate,
    EmailSendRequest,
    BulkEmailRequest
} from '@/lib/api/messages';

// Query keys
export const messageQueryKeys = {
    all: ['messages'] as const,
    lists: () => [...messageQueryKeys.all, 'list'] as const,
    list: (filters: MessageFilters) => [...messageQueryKeys.lists(), filters] as const,
    details: () => [...messageQueryKeys.all, 'detail'] as const,
    detail: (id: number) => [...messageQueryKeys.details(), id] as const,
    stats: (campaignId?: number) => [...messageQueryKeys.all, 'stats', campaignId] as const,
    templates: () => [...messageQueryKeys.all, 'templates'] as const,
    templatesList: (filters: any) => [...messageQueryKeys.templates(), 'list', filters] as const,
    templateDetail: (id: number) => [...messageQueryKeys.templates(), 'detail', id] as const,
};

// Message hooks
export function useMessages(filters: MessageFilters = {}) {
    return useQuery({
        queryKey: messageQueryKeys.list(filters),
        queryFn: () => messagesApi.list(filters),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

export function useMessage(id: number) {
    return useQuery({
        queryKey: messageQueryKeys.detail(id),
        queryFn: () => messagesApi.get(id),
        enabled: !!id,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

export function useCreateMessage() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateMessageData) => messagesApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.lists() });
        },
    });
}

export function useUpdateMessage() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: UpdateMessageData }) =>
            messagesApi.update(id, data),
        onSuccess: (updatedMessage) => {
            queryClient.setQueryData(
                messageQueryKeys.detail(updatedMessage.id),
                updatedMessage
            );
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.lists() });
        },
    });
}

export function useUpdateMessageStatus() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: MessageStatusUpdate }) =>
            messagesApi.updateStatus(id, data),
        onSuccess: (updatedMessage) => {
            queryClient.setQueryData(
                messageQueryKeys.detail(updatedMessage.id),
                updatedMessage
            );
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.lists() });
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.stats() });
        },
    });
}

export function useDeleteMessage() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: number) => messagesApi.delete(id),
        onSuccess: (_, deletedId) => {
            queryClient.removeQueries({ queryKey: messageQueryKeys.detail(deletedId) });
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.lists() });
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.stats() });
        },
    });
}

export function useSendMessage() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, forceSend }: { id: number; forceSend?: boolean }) =>
            messagesApi.send(id, forceSend),
        onSuccess: (updatedMessage) => {
            queryClient.setQueryData(
                messageQueryKeys.detail(updatedMessage.id),
                updatedMessage
            );
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.lists() });
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.stats() });
        },
    });
}

export function useGenerateMessageFromTemplate() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: GenerateMessageFromTemplate) => messagesApi.generateFromTemplate(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.lists() });
        },
    });
}

export function useCreateBulkMessages() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: BulkMessageCreate) => messagesApi.createBulk(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.lists() });
        },
    });
}

export function useMessageStats(campaignId?: number) {
    return useQuery({
        queryKey: messageQueryKeys.stats(campaignId),
        queryFn: () => messagesApi.getStats(campaignId),
        staleTime: 2 * 60 * 1000, // 2 minutes
    });
}

// Message Template hooks
export function useMessageTemplates(filters: {
    message_type?: string;
    category?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
} = {}) {
    return useQuery({
        queryKey: messageQueryKeys.templatesList(filters),
        queryFn: () => messagesApi.listTemplates(filters),
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
}

export function useMessageTemplate(id: number) {
    return useQuery({
        queryKey: messageQueryKeys.templateDetail(id),
        queryFn: () => messagesApi.getTemplate(id),
        enabled: !!id,
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
}

export function useCreateMessageTemplate() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateMessageTemplateData) => messagesApi.createTemplate(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.templates() });
        },
    });
}

export function useUpdateMessageTemplate() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: UpdateMessageTemplateData }) =>
            messagesApi.updateTemplate(id, data),
        onSuccess: (updatedTemplate) => {
            queryClient.setQueryData(
                messageQueryKeys.templateDetail(updatedTemplate.id),
                updatedTemplate
            );
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.templates() });
        },
    });
}

export function useDeleteMessageTemplate() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: number) => messagesApi.deleteTemplate(id),
        onSuccess: (_, deletedId) => {
            queryClient.removeQueries({ queryKey: messageQueryKeys.templateDetail(deletedId) });
            queryClient.invalidateQueries({ queryKey: messageQueryKeys.templates() });
        },
    });
}

// Email service hooks
export function useTestEmailConfig() {
    return useMutation({
        mutationFn: (testEmail: string) => messagesApi.testEmailConfig(testEmail),
    });
}

export function useSendEmail() {
    return useMutation({
        mutationFn: (data: EmailSendRequest) => messagesApi.sendEmail(data),
    });
}

export function useSendBulkEmails() {
    return useMutation({
        mutationFn: (data: BulkEmailRequest) => messagesApi.sendBulkEmails(data),
    });
}

export function useTestEmailConnection() {
    return useQuery({
        queryKey: ['email', 'test-connection'],
        queryFn: () => messagesApi.testEmailConnection(),
        enabled: false, // Only run when manually triggered
        retry: false,
    });
}