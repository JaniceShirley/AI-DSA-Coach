import api from './api';
import type { DashboardStats, UserProblemProgress, ProblemStatus } from '../types';

export const progressService = {
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>('/progress/');
    return response.data;
  },

  async getProblemProgress(problemId: number): Promise<UserProblemProgress> {
    const response = await api.get<UserProblemProgress>(`/progress/${problemId}/`);
    return response.data;
  },

  async recordAttempt(
    problemId: number,
    status: ProblemStatus,
    timeSpent: number = 0,
    code: string = ''
  ): Promise<UserProblemProgress> {
    const response = await api.post<UserProblemProgress>(`/progress/${problemId}/`, {
      status,
      time_spent: timeSpent,
      code,
    });
    return response.data;
  },
};
