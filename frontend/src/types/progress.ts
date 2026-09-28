import type { ProblemListItem, ProblemStatus } from './problem';

export interface UserProblemProgress {
  id: number;
  user: number;
  problem: number;
  status: ProblemStatus;
  attempts: number;
  solved_at?: string | null;
  time_spent: number;
  hints_used: number;
  hint_level: number;
  challenge_score?: number | null;
  interview_score?: number | null;
  submission_history: Array<{
    code: string;
    status: string;
    timestamp: string;
  }>;
}

export interface TopicProgressItem {
  topic: string;
  solved: number;
  total: number;
  percentage: number;
}

export interface DashboardStats {
  total_problems: number;
  solved_count: number;
  attempted_count: number;
  current_streak: number;
  topic_progress: TopicProgressItem[];
  recent_problems: ProblemListItem[];
  recommended_problem: ProblemListItem | null;
}
