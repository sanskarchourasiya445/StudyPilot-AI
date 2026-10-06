import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studyApi } from '../services/studyApi';
import { useToast } from '../components/ui/Toast';

export function useSummary(resourceId, options = {}) {
  const { enabled = true } = options;
  return useQuery({
    queryKey: ['summary', resourceId],
    queryFn: () => studyApi.getSummary(resourceId),
    enabled: !!resourceId && enabled,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useGenerateSummary() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ resourceId, forceRegenerate = false }) =>
      studyApi.generateSummary(resourceId, forceRegenerate),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(['summary', variables.resourceId], data);
      queryClient.invalidateQueries({ queryKey: ['resources'] });
      queryClient.invalidateQueries({ queryKey: ['resources', variables.resourceId] });
      addToast('Summary generated successfully!', 'success');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to generate summary.', 'error');
    },
  });
}

export function useNotes(resourceId, style = 'bullet', options = {}) {
  const { enabled = true } = options;
  return useQuery({
    queryKey: ['notes', resourceId, style],
    queryFn: () => studyApi.getNotes(resourceId, style),
    enabled: !!resourceId && enabled,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useGenerateNotes() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ resourceId, style, forceRegenerate = false }) =>
      studyApi.generateNotes(resourceId, style, forceRegenerate),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(['notes', variables.resourceId, variables.style], data);
      queryClient.invalidateQueries({ queryKey: ['resources'] });
      queryClient.invalidateQueries({ queryKey: ['resources', variables.resourceId] });
      addToast('Study notes generated successfully!', 'success');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to generate notes.', 'error');
    },
  });
}

export function useQuizzes(resourceId, options = {}) {
  const { enabled = true } = options;
  return useQuery({
    queryKey: ['quizzes', resourceId],
    queryFn: () => studyApi.getQuizzes(resourceId),
    enabled: !!resourceId && enabled,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useGenerateQuiz() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ resourceId, questionCount, difficulty, forceRegenerate = false }) =>
      studyApi.generateQuiz(resourceId, questionCount, difficulty, forceRegenerate),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(['quizzes', variables.resourceId], (old = []) => {
        const list = Array.isArray(old) ? old : [];
        return [data, ...list.filter((q) => q.id !== data.id)];
      });
      queryClient.invalidateQueries({ queryKey: ['resources'] });
      queryClient.invalidateQueries({ queryKey: ['resources', variables.resourceId] });
      addToast('Practice quiz generated!', 'success');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to generate quiz.', 'error');
    },
  });
}

export function useDeleteSummary() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (resourceId) => studyApi.deleteSummary(resourceId),
    onSuccess: (_, resourceId) => {
      queryClient.setQueryData(['summary', resourceId], null);
      queryClient.invalidateQueries({ queryKey: ['summary', resourceId] });
      addToast('Summary deleted successfully.', 'info');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to delete summary.', 'error');
    },
  });
}

export function useDeleteNotes() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ resourceId, style }) => studyApi.deleteNotes(resourceId, style),
    onSuccess: (_, variables) => {
      queryClient.setQueryData(['notes', variables.resourceId, variables.style], null);
      queryClient.setQueryData(['notes', variables.resourceId], null);
      queryClient.invalidateQueries({ queryKey: ['notes', variables.resourceId] });
      addToast('Study notes deleted successfully.', 'info');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to delete notes.', 'error');
    },
  });
}

export function useDeleteQuizzes() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ resourceId, quizId }) => studyApi.deleteQuizzes(resourceId, quizId),
    onSuccess: (_, variables) => {
      queryClient.setQueryData(['quizzes', variables.resourceId], []);
      queryClient.invalidateQueries({ queryKey: ['quizzes', variables.resourceId] });
      addToast('Quizzes deleted successfully.', 'info');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to delete quizzes.', 'error');
    },
  });
}
