import { apiClient } from './apiClient';

export const studyApi = {
  async getSummary(resourceId) {
    try {
      const response = await apiClient.get(`/resources/${resourceId}/summary`);
      return response.data;
    } catch (error) {
      if (error?.status === 404 || error?.response?.status === 404) return null;
      throw error;
    }
  },

  async generateSummary(resourceId, forceRegenerate = false) {
    const response = await apiClient.post(`/resources/${resourceId}/summary`, {
      force_regenerate: forceRegenerate,
    });
    return response.data;
  },

  async getNotes(resourceId, style = 'bullet') {
    try {
      const response = await apiClient.get(`/resources/${resourceId}/notes`, {
        params: { style },
      });
      return response.data;
    } catch (error) {
      if (error?.status === 404 || error?.response?.status === 404) return null;
      throw error;
    }
  },

  async generateNotes(resourceId, style = 'bullet', forceRegenerate = false) {
    const response = await apiClient.post(`/resources/${resourceId}/notes`, {
      style,
      force_regenerate: forceRegenerate,
    });
    return response.data;
  },

  async getQuizzes(resourceId) {
    try {
      const response = await apiClient.get(`/resources/${resourceId}/quizzes`);
      return response.data;
    } catch (error) {
      if (error?.status === 404 || error?.response?.status === 404) return [];
      throw error;
    }
  },

  async generateQuiz(resourceId, questionCount = 5, difficulty = 'medium', forceRegenerate = false) {
    const response = await apiClient.post(`/resources/${resourceId}/quiz`, {
      question_count: questionCount,
      difficulty,
      force_regenerate: forceRegenerate,
    });
    return response.data;
  },

  async deleteSummary(resourceId) {
    const response = await apiClient.delete(`/resources/${resourceId}/summary`);
    return response.data;
  },

  async deleteNotes(resourceId, style = null) {
    const response = await apiClient.delete(`/resources/${resourceId}/notes`, {
      params: style ? { style } : {},
    });
    return response.data;
  },

  async deleteQuizzes(resourceId, quizId = null) {
    const response = await apiClient.delete(`/resources/${resourceId}/quizzes`, {
      params: quizId ? { quiz_id: quizId } : {},
    });
    return response.data;
  },
};
