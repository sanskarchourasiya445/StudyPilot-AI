import { apiClient } from './apiClient';

export const masteryApi = {
  getMastery: async () => {
    const response = await apiClient.get('/mastery');
    return response.data;
  },

  getKnowledgeGaps: async () => {
    const response = await apiClient.get('/mastery/gaps');
    return response.data;
  },

  getRecommendedDifficulty: async (topic) => {
    const response = await apiClient.get('/mastery/difficulty', {
      params: { topic },
    });
    return response.data;
  },

  submitQuizResult: async (quizId, score, totalQuestions, topic) => {
    const response = await apiClient.post(
      `/resources/quizzes/${quizId}/submit`,
      null,
      { params: { score, total_questions: totalQuestions, topic_override: topic } }
    );
    return response.data;
  },
};
