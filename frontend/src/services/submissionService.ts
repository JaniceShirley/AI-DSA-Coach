import api from './api';
import type { Submission, RunCodeResponse } from '../types';

export const submissionService = {
  async runCode(problemId: number, code: string, language: string = 'python'): Promise<RunCodeResponse> {
    const response = await api.post<RunCodeResponse>('/submissions/run/', {
      problem_id: problemId,
      code,
      language,
    });
    return response.data;
  },

  async submitCode(problemId: number, code: string, language: string = 'python'): Promise<Submission> {
    const response = await api.post<Submission>('/submissions/submit/', {
      problem_id: problemId,
      code,
      language,
    });
    return response.data;
  },

  async getSubmissions(problemId?: number): Promise<Submission[]> {
    const params = problemId ? { problem_id: problemId } : undefined;
    const response = await api.get<Submission[]>('/submissions/', { params });
    return response.data;
  },

  async getSubmissionById(id: number): Promise<Submission> {
    const response = await api.get<Submission>(`/submissions/${id}/`);
    return response.data;
  },
};
