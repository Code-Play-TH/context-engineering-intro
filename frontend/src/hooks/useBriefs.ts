import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    briefsApi,
    BriefFilters,
    CreateBriefData,
    UpdateBriefData,
    BriefStatusUpdate,
    CreateBriefTemplateData,
    UpdateBriefTemplateData,
    GenerateBriefFromTemplate,
    BulkBriefCreate
} from '@/lib/api/briefs';

// Query keys
export const briefQueryKeys = {
    all: ['briefs'] as const,
    lists: () => [...briefQueryKeys.all, 'list'] as const,
    list: (filters: BriefFilters) => [...briefQueryKeys.lists(), filters] as const,
    details: () => [...briefQueryKeys.all, 'detail'] as const,
    detail: (id: number) => [...briefQueryKeys.details(), id] as const,
    stats: (campaignId?: number) => [...briefQueryKeys.all, 'stats', campaignId] as const,
    templates: () => [...briefQueryKeys.all, 'templates'] as const,
    templatesList: (filters: any) => [...briefQueryKeys.templates(), 'list', filters] as const,
    templateDetail: (id: number) => [...briefQueryKeys.templates(), 'detail', id] as const,
};

// Brief hooks
export function useBriefs(filters: BriefFilters = {}) {
    return useQuery({
        queryKey: briefQueryKeys.list(filters),
        queryFn: () => briefsApi.list(filters),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

export function useBrief(id: number) {
    return useQuery({
        queryKey: briefQueryKeys.detail(id),
        queryFn: () => briefsApi.get(id),
        enabled: !!id,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

export function useCreateBrief() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateBriefData) => briefsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.lists() });
        },
    });
}

export function useUpdateBrief() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: UpdateBriefData }) =>
            briefsApi.update(id, data),
        onSuccess: (updatedBrief) => {
            queryClient.setQueryData(
                briefQueryKeys.detail(updatedBrief.id),
                updatedBrief
            );
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.lists() });
        },
    });
}

export function useUpdateBriefStatus() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: BriefStatusUpdate }) =>
            briefsApi.updateStatus(id, data),
        onSuccess: (updatedBrief) => {
            queryClient.setQueryData(
                briefQueryKeys.detail(updatedBrief.id),
                updatedBrief
            );
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.lists() });
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.stats() });
        },
    });
}

export function useDeleteBrief() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: number) => briefsApi.delete(id),
        onSuccess: (_, deletedId) => {
            queryClient.removeQueries({ queryKey: briefQueryKeys.detail(deletedId) });
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.lists() });
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.stats() });
        },
    });
}

export function useGenerateBriefFromTemplate() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: GenerateBriefFromTemplate) => briefsApi.generateFromTemplate(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.lists() });
        },
    });
}

export function useCreateBulkBriefs() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: BulkBriefCreate) => briefsApi.createBulk(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.lists() });
        },
    });
}

export function useBriefStats(campaignId?: number) {
    return useQuery({
        queryKey: briefQueryKeys.stats(campaignId),
        queryFn: () => briefsApi.getStats(campaignId),
        staleTime: 2 * 60 * 1000, // 2 minutes
    });
}

// Brief Template hooks
export function useBriefTemplates(filters: {
    category?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
} = {}) {
    return useQuery({
        queryKey: briefQueryKeys.templatesList(filters),
        queryFn: () => briefsApi.listTemplates(filters),
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
}

export function useBriefTemplate(id: number) {
    return useQuery({
        queryKey: briefQueryKeys.templateDetail(id),
        queryFn: () => briefsApi.getTemplate(id),
        enabled: !!id,
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
}

export function useCreateBriefTemplate() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateBriefTemplateData) => briefsApi.createTemplate(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.templates() });
        },
    });
}

export function useUpdateBriefTemplate() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: UpdateBriefTemplateData }) =>
            briefsApi.updateTemplate(id, data),
        onSuccess: (updatedTemplate) => {
            queryClient.setQueryData(
                briefQueryKeys.templateDetail(updatedTemplate.id),
                updatedTemplate
            );
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.templates() });
        },
    });
}

export function useDeleteBriefTemplate() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: number) => briefsApi.deleteTemplate(id),
        onSuccess: (_, deletedId) => {
            queryClient.removeQueries({ queryKey: briefQueryKeys.templateDetail(deletedId) });
            queryClient.invalidateQueries({ queryKey: briefQueryKeys.templates() });
        },
    });
}