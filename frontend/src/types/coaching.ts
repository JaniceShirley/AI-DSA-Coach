export type InteractionType = 'chat' | 'hint' | 'challenge' | 'alternative' | 'feedback';

export type LearningStage =
  | 'UNDERSTANDING_PROBLEM'
  | 'APPROACH_DISCOVERY'
  | 'GUIDED_IMPLEMENTATION'
  | 'DEBUGGING'
  | 'CORRECTNESS_VERIFICATION'
  | 'COMPLEXITY_ANALYSIS'
  | 'OPTIMIZATION_DISCOVERY'
  | 'OPTIMIZED_IMPLEMENTATION'
  | 'APPROACH_COMPARISON'
  | 'COMPLETED';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ExploredApproach {
  name: string;
  type: string;
  is_valid: boolean;
  is_optimal: boolean;
  status?: string;
  time_complexity?: string;
  space_complexity?: string;
  tradeoffs?: string;
  description?: string;
}

export interface CoachingSessionState {
  session_id: number;
  problem_id: number;
  stage: LearningStage;
  current_approach: Partial<ExploredApproach>;
  explored_approaches: ExploredApproach[];
  solution_status: string;
  complexity_state: Record<string, string>;
  hints_provided: string[];
  misconceptions: string[];
  last_student_code?: string;
  last_execution_result?: Record<string, unknown>;
  messages: ChatMessage[];
  updated_at: string;
}

export interface ChatResponse {
  status: string;
  message: string;
  stage: LearningStage;
  current_approach: Partial<ExploredApproach>;
  explored_approaches: ExploredApproach[];
  solution_status: string;
  complexity_state: Record<string, string>;
  execution_result?: Record<string, unknown>;
  interaction_id: number;
  session_id: number;
}

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
