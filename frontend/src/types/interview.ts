import type { ProblemDetail } from './problem';
import type { Submission } from './submission';

export type InterviewStage =
  | 'PROBLEM_INTRO'
  | 'APPROACH'
  | 'COMPLEXITY'
  | 'EDGE_CASES'
  | 'OPTIMIZATION'
  | 'CODING'
  | 'FINAL_EVALUATION';

export type InterviewStatus = 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED';

export interface InterviewMessage {
  id: number;
  role: 'AI_INTERVIEWER' | 'STUDENT';
  message: string;
  stage: string;
  created_at: string;
}

export interface RubricEvaluationItem {
  rating: string;
  notes: string;
}

export interface InterviewEvaluation {
  id: number;
  overall_score: number;
  problem_understanding: RubricEvaluationItem;
  approach_quality: RubricEvaluationItem;
  technical_reasoning: RubricEvaluationItem;
  complexity_analysis: RubricEvaluationItem;
  edge_case_awareness: RubricEvaluationItem;
  optimization: RubricEvaluationItem;
  communication: RubricEvaluationItem;
  coding_correctness: RubricEvaluationItem;
  strengths: string[];
  areas_for_improvement: string[];
  final_feedback: string;
  recommended_topics: string[];
  recommended_problems: Array<{ id: number; title: string; slug: string; difficulty: string }>;
  created_at: string;
}

export interface InterviewSessionListItem {
  id: number;
  problem: number;
  problem_title: string;
  problem_slug: string;
  status: InterviewStatus;
  difficulty: string;
  current_stage: InterviewStage;
  overall_score: number | null;
  started_at: string;
  completed_at: string | null;
  created_at: string;
}

export interface InterviewSessionDetail {
  id: number;
  problem: ProblemDetail;
  status: InterviewStatus;
  difficulty: string;
  current_stage: InterviewStage;
  final_feedback: string;
  submission: Submission | null;
  messages: InterviewMessage[];
  evaluation: InterviewEvaluation | null;
  started_at: string;
  completed_at: string | null;
  created_at: string;
}

export interface StartInterviewResponse {
  session_id: number;
  problem: ProblemDetail;
  stage: InterviewStage;
  status: InterviewStatus;
  message: string;
  created_at: string;
}

export interface InterviewRespondResponse {
  session_id: number;
  stage: InterviewStage;
  status: InterviewStatus;
  message: string;
  should_end?: boolean;
}
