export type InteractionType = 'hint' | 'challenge' | 'alternative' | 'feedback';

export interface CoachingInteraction {
  id: number;
  session_id: string;
  problem: number;
  problem_title?: string;
  student_code: string;
  hint_level?: number | null;
  user_question?: string | null;
  ai_response: string;
  submission?: number | null;
  interaction_type: InteractionType;
  evaluation_metadata?: Record<string, unknown>;
  created_at: string;
}

export interface HintResponse {
  status: string;
  interaction_id: number;
  session_id: string;
  hint: string;
  hint_level: number;
  hints_used: number;
}

export interface ChallengeResponse {
  status: string;
  interaction_id: number;
  session_id: string;
  challenge: string;
}

export interface AlternativeResponse {
  status: string;
  interaction_id: number;
  session_id: string;
  alternative_approach: string;
}

export interface AIFeedbackData {
  approach: string;
  correctness: string;
  time_complexity: string;
  space_complexity: string;
  edge_cases: string;
  optimization: string;
}

export interface FeedbackResponse {
  status: string;
  interaction_id: number;
  session_id: string;
  feedback: AIFeedbackData;
}
