import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourceApi } from '../services/resourceApi';
import { useToast } from '../components/ui/Toast';

export function useResources() {
  return useQuery({
    queryKey: ['resources'],
    queryFn: resourceApi.getResources,
    refetchInterval: (query) => {
      const data = query.state.data;
      const isProcessing =
        Array.isArray(data) &&
        data.some((r) => r.status === 'processing' || r.status === 'pending');
      return isProcessing ? 2000 : false;
    },
  });
}

export function useResource(resourceId) {
  return useQuery({
    queryKey: ['resources', resourceId],
    queryFn: () => resourceApi.getResource(resourceId),
    enabled: Boolean(resourceId),
    staleTime: 1000 * 60,
    retry: (failureCount, error) => {
      // Never retry on 404 Not Found
      if (error?.response?.status === 404 || error?.status === 404) return false;
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'processing' || status === 'pending' ? 1500 : false;
    },
  });
}

export function useUploadPdf() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (file) => resourceApi.uploadPdf(file),
    onSuccess: (data) => {
      const resId = data.resource_id || data.id;
      if (resId) {
        queryClient.setQueryData(['resources', resId], data);
      }
      queryClient.setQueryData(['resources'], (old = []) => {
        const list = Array.isArray(old) ? old : [];
        return [data, ...list.filter((r) => (r.resource_id || r.id) !== resId)];
      });
      queryClient.invalidateQueries({ queryKey: ['resources'], exact: true });
      addToast(`PDF "${data.title || data.source}" uploaded successfully!`, 'success');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to upload PDF.', 'error');
    },
  });
}

export function useAddYoutube() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (url) => resourceApi.addYoutube(url),
    onSuccess: (data) => {
      const resId = data.resource_id || data.id;
      if (resId) {
        queryClient.setQueryData(['resources', resId], data);
      }
      queryClient.setQueryData(['resources'], (old = []) => {
        const list = Array.isArray(old) ? old : [];
        return [data, ...list.filter((r) => (r.resource_id || r.id) !== resId)];
      });
      queryClient.invalidateQueries({ queryKey: ['resources'], exact: true });
      addToast(`YouTube video "${data.title || data.source}" added successfully!`, 'success');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to ingest YouTube URL.', 'error');
    },
  });
}

export function useDeleteResource() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (resourceId) => resourceApi.deleteResource(resourceId),
    onSuccess: (_, resourceId) => {
      // 1. Cancel and completely remove individual resource query from cache
      queryClient.cancelQueries({ queryKey: ['resources', resourceId] });
      queryClient.removeQueries({ queryKey: ['resources', resourceId], exact: true });

      // 2. Remove any cached study tool queries for this resource
      queryClient.removeQueries({ queryKey: ['summary', resourceId] });
      queryClient.removeQueries({ queryKey: ['notes', resourceId] });
      queryClient.removeQueries({ queryKey: ['quizzes', resourceId] });

      // 3. Update the resources list cache optimistically
      queryClient.setQueryData(['resources'], (old = []) => {
        const list = Array.isArray(old) ? old : [];
        return list.filter((r) => (r.resource_id || r.id) !== resourceId);
      });

      // 4. Invalidate ONLY the list query (exact: true) so it doesn't refetch the deleted resource
      queryClient.invalidateQueries({ queryKey: ['resources'], exact: true });
      addToast('Resource deleted successfully.', 'info');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to delete resource.', 'error');
    },
  });
}
