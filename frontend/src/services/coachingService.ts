import api from './api';
import type {
  HintResponse,
  ChallengeResponse,
  AlternativeResponse,
  FeedbackResponse,
  CoachingInteraction
} from '../types';

export const coachingService = {
  async getHint(
    problemId: number,
    studentCode: string,
    submissionId?: number,
    requestedLevel?: number
  ): Promise<HintResponse> {
    const response = await api.post<HintResponse>('/coaching/hint/', {
      problem_id: problemId,
      student_code: studentCode,
      submission_id: submissionId || null,
      requested_level: requestedLevel || null,
    });
    return response.data;
  },

  async challengeUnderstanding(
    problemId: number,
    studentCode: string,
    userAnswer?: string
  ): Promise<ChallengeResponse> {
    const response = await api.post<ChallengeResponse>('/coaching/challenge/', {
      problem_id: problemId,
      student_code: studentCode,
      user_answer: userAnswer || '',
    });
    return response.data;
  },

  async getAlternativeApproach(
    problemId: number,
    studentCode: string
  ): Promise<AlternativeResponse> {
    const response = await api.post<AlternativeResponse>('/coaching/alternative/', {
      problem_id: problemId,
      student_code: studentCode,
    });
    return response.data;
  },

  async getFeedback(
    problemId: number,
    studentCode: string,
    submissionId?: number
  ): Promise<FeedbackResponse> {
    const response = await api.post<FeedbackResponse>('/coaching/feedback/', {
      problem_id: problemId,
      student_code: studentCode,
      submission_id: submissionId || null,
    });
    return response.data;
  },

  async getCoachingHistory(problemId: number): Promise<CoachingInteraction[]> {
    const response = await api.get<CoachingInteraction[]>(`/coaching/history/${problemId}/`);
    return response.data;
  }
};
