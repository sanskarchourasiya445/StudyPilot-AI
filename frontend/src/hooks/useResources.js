import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourceApi } from '../services/resourceApi';
import { useToast } from '../components/ui/Toast';

export function useResources() {
  return useQuery({
    queryKey: ['resources'],
    queryFn: resourceApi.getResources,
  });
}

export function useResource(resourceId) {
  return useQuery({
    queryKey: ['resources', resourceId],
    queryFn: () => resourceApi.getResource(resourceId),
    enabled: !!resourceId,
    staleTime: 0,
    refetchOnMount: 'always',
  });
}

export function useUploadPdf() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (file) => resourceApi.uploadPdf(file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
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
      queryClient.invalidateQueries({ queryKey: ['resources'] });
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
      addToast('Resource deleted successfully.', 'info');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to delete resource.', 'error');
    },
  });
}
