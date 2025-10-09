/**
 * React Query hooks for campaigns
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { campaignApi, Campaign, CampaignCreate, CampaignUpdate } from '@/lib/api/campaigns';

export function useCampaigns(params?: {
    page?: number;
    page_size?: number;
    status?: string;
}) {
    return useQuery({
        queryKey: ['campaigns', params],
        queryFn: () => campaignApi.list(params),
    });
}

export function useCampaign(id: number) {
    return useQuery({
        queryKey: ['campaigns', id],
        queryFn: () => campaignApi.get(id),
        enabled: !!id,
    });
}

export function useCreateCampaign() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CampaignCreate) => campaignApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['campaigns'] });
        },
    });
}

export function useUpdateCampaign() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: CampaignUpdate }) =>
            campaignApi.update(id, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['campaigns'] });
            queryClient.invalidateQueries({ queryKey: ['campaigns', variables.id] });
        },
    });
}

export function useDeleteCampaign() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: number) => campaignApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['campaigns'] });
        },
    });
}

export function useChangeStatus() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, status }: { id: number; status: string }) =>
            campaignApi.changeStatus(id, status),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['campaigns'] });
            queryClient.invalidateQueries({ queryKey: ['campaigns', variables.id] });
        },
    });
}

export function useDuplicateCampaign() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: number) => campaignApi.duplicate(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['campaigns'] });
        },
    });
}
