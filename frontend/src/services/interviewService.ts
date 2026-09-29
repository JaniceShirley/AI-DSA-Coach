import api from './api';
import type {
  StartInterviewResponse,
  InterviewSessionListItem,
  InterviewSessionDetail,
  InterviewRespondResponse,
  InterviewEvaluation
} from '../types';

export const interviewService = {
  async startInterview(params: {
    difficulty?: string;
    topic?: string;
    problem_id?: number;
  }): Promise<StartInterviewResponse> {
    const response = await api.post<StartInterviewResponse>('/interviews/start/', params);
    return response.data;
  },

  async getInterviews(): Promise<InterviewSessionListItem[]> {
    const response = await api.get<InterviewSessionListItem[]>('/interviews/');
    return response.data;
  },

  async getInterviewById(sessionId: number): Promise<InterviewSessionDetail> {
    const response = await api.get<InterviewSessionDetail>(`/interviews/${sessionId}/`);
    return response.data;
  },

  async respond(sessionId: number, message: string): Promise<InterviewRespondResponse> {
    const response = await api.post<InterviewRespondResponse>(`/interviews/${sessionId}/respond/`, {
      message
    });
    return response.data;
  },

  async associateCode(sessionId: number, submissionId: number): Promise<{ session_id: number; submission_status: string; message: string; stage: string }> {
    const response = await api.post(`/interviews/${sessionId}/code/`, {
      submission_id: submissionId
    });
    return response.data;
  },

  async endInterview(sessionId: number): Promise<InterviewEvaluation> {
    const response = await api.post<InterviewEvaluation>(`/interviews/${sessionId}/end/`);
    return response.data;
  },

  async getFeedback(sessionId: number): Promise<InterviewEvaluation> {
    const response = await api.get<InterviewEvaluation>(`/interviews/${sessionId}/feedback/`);
    return response.data;
  }
};
