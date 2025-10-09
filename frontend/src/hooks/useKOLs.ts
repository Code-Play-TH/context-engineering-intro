import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { kolsApi, KOLFilters, CreateKOLData, UpdateKOLData } from '@/lib/api/kols';

// Query keys
export const kolQueryKeys = {
    all: ['kols'] as const,
    lists: () => [...kolQueryKeys.all, 'list'] as const,
    list: (filters: KOLFilters) => [...kolQueryKeys.lists(), filters] as const,
    details: () => [...kolQueryKeys.all, 'detail'] as const,
    detail: (id: number) => [...kolQueryKeys.details(), id] as const,
    duplicates: (id: number) => [...kolQueryKeys.all, 'duplicates', id] as const,
    imports: () => [...kolQueryKeys.all, 'imports'] as const,
    import: (jobId: number) => [...kolQueryKeys.imports(), jobId] as const,
};

// List KOLs with filters
export function useKOLs(filters: KOLFilters = {}) {
    return useQuery({
        queryKey: kolQueryKeys.list(filters),
        queryFn: () => kolsApi.list(filters),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

// Get single KOL
export function useKOL(id: number) {
    return useQuery({
        queryKey: kolQueryKeys.detail(id),
        queryFn: () => kolsApi.get(id),
        enabled: !!id,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

// Create KOL mutation
export function useCreateKOL() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateKOLData) => kolsApi.create(data),
        onSuccess: () => {
            // Invalidate and refetch KOL lists
            queryClient.invalidateQueries({ queryKey: kolQueryKeys.lists() });
        },
    });
}

// Update KOL mutation
export function useUpdateKOL() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: UpdateKOLData }) =>
            kolsApi.update(id, data),
        onSuccess: (updatedKOL) => {
            // Update the specific KOL in cache
            queryClient.setQueryData(
                kolQueryKeys.detail(updatedKOL.id),
                updatedKOL
            );
            // Invalidate lists to reflect changes
            queryClient.invalidateQueries({ queryKey: kolQueryKeys.lists() });
        },
    });
}

// Delete KOL mutation
export function useDeleteKOL() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: number) => kolsApi.delete(id),
        onSuccess: (_, deletedId) => {
            // Remove from cache
            queryClient.removeQueries({ queryKey: kolQueryKeys.detail(deletedId) });
            // Invalidate lists
            queryClient.invalidateQueries({ queryKey: kolQueryKeys.lists() });
        },
    });
}

// Add tag mutation
export function useAddKOLTag() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, tag }: { id: number; tag: string }) =>
            kolsApi.addTag(id, tag),
        onSuccess: (_, { id }) => {
            // Invalidate the specific KOL and lists
            queryClient.invalidateQueries({ queryKey: kolQueryKeys.detail(id) });
            queryClient.invalidateQueries({ queryKey: kolQueryKeys.lists() });
        },
    });
}

// Remove tag mutation
export function useRemoveKOLTag() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, tag }: { id: number; tag: string }) =>
            kolsApi.removeTag(id, tag),
        onSuccess: (_, { id }) => {
            // Invalidate the specific KOL and lists
            queryClient.invalidateQueries({ queryKey: kolQueryKeys.detail(id) });
            queryClient.invalidateQueries({ queryKey: kolQueryKeys.lists() });
        },
    });
}

// Find duplicates
export function useKOLDuplicates(id: number) {
    return useQuery({
        queryKey: kolQueryKeys.duplicates(id),
        queryFn: () => kolsApi.findDuplicates(id),
        enabled: !!id,
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
}

// CSV Import mutations
export function useUploadKOLImport() {
    return useMutation({
        mutationFn: (file: File) => kolsApi.uploadImport(file),
    });
}

export function useValidateKOLImport() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (jobId: number) => kolsApi.validateImport(jobId),
        onSuccess: (job) => {
            // Update the import job in cache
            queryClient.setQueryData(kolQueryKeys.import(job.id), job);
        },
    });
}

export function useProcessKOLImport() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (jobId: number) => kolsApi.processImport(jobId),
        onSuccess: (job) => {
            // Update the import job in cache
            queryClient.setQueryData(kolQueryKeys.import(job.id), job);
            // Invalidate KOL lists to show new imports
            queryClient.invalidateQueries({ queryKey: kolQueryKeys.lists() });
        },
    });
}

// Get import job status
export function useKOLImportStatus(jobId: number | null) {
    return useQuery({
        queryKey: kolQueryKeys.import(jobId!),
        queryFn: () => kolsApi.getImportStatus(jobId!),
        enabled: !!jobId,
        refetchInterval: (data) => {
            // Poll every 2 seconds if job is still processing
            if (data?.status === 'pending' || data?.status === 'validating' || data?.status === 'processing') {
                return 2000;
            }
            return false;
        },
    });
}