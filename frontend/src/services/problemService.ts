import api from './api';
import type { ProblemListItem, ProblemDetail } from '../types';

export interface ProblemFilterParams {
  search?: string;
  difficulty?: string;
  topic?: string;
  status_filter?: string;
}

export const problemService = {
  async getProblems(params?: ProblemFilterParams): Promise<ProblemListItem[]> {
    const response = await api.get<ProblemListItem[]>('/problems/', { params });
    return response.data;
  },

  async getProblemBySlug(slug: string): Promise<ProblemDetail> {
    const response = await api.get<ProblemDetail>(`/problems/${slug}/`);
    return response.data;
  },
};
