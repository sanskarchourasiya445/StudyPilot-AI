import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { masteryApi } from '../services/masteryApi';

export function useMastery() {
  return useQuery({
    queryKey: ['mastery'],
    queryFn: masteryApi.getMastery,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

export function useKnowledgeGaps() {
  return useQuery({
    queryKey: ['knowledge_gaps'],
    queryFn: masteryApi.getKnowledgeGaps,
    staleTime: 1000 * 60 * 2,
  });
}

export function useRecommendedDifficulty(topic) {
  return useQuery({
    queryKey: ['mastery_difficulty', topic],
    queryFn: () => masteryApi.getRecommendedDifficulty(topic),
    enabled: Boolean(topic),
    staleTime: 1000 * 30, // 30 seconds
  });
}

export function useSubmitQuizResult() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ quizId, score, totalQuestions, topic }) =>
      masteryApi.submitQuizResult(quizId, score, totalQuestions, topic),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mastery'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge_gaps'] });
    },
  });
}
