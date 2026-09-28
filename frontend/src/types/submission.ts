import type { ProblemListItem } from './problem';

export type SubmissionStatus =
  | 'ACCEPTED'
  | 'WRONG_ANSWER'
  | 'RUNTIME_ERROR'
  | 'SYNTAX_ERROR'
  | 'TIME_LIMIT_EXCEEDED'
  | 'INTERNAL_ERROR';

export interface TestCaseResult {
  test_case_id: number;
  input: string;
  expected_output: string;
  actual_output: string;
  passed: boolean;
  error: string | null;
  is_public: boolean;
}

export interface RunCodeResponse {
  status: SubmissionStatus;
  test_cases_passed: number;
  total_test_cases: number;
  runtime: number;
  memory: number;
  error_message: string | null;
  results: TestCaseResult[];
}

export interface Submission {
  id: number;
  user: number;
  problem: ProblemListItem;
  code: string;
  language: string;
  status: SubmissionStatus;
  runtime: number;
  memory: number;
  error_message: string | null;
  test_cases_passed: number;
  total_test_cases: number;
  created_at: string;
}

export interface DifficultyBreakdown {
  solved: number;
  total: number;
}

export interface AnalyticsData {
  total_problems: number;
  solved_count: number;
  attempted_count: number;
  total_submissions: number;
  success_rate: number;
  average_attempts_per_solved: number;
  average_solving_time_minutes: number;
  solved_by_difficulty: Record<string, DifficultyBreakdown>;
  solved_by_topic: Array<{
    topic: string;
    solved: number;
    total: number;
    percentage: number;
  }>;
  recommended_problem: ProblemListItem | null;
  recent_submissions: Submission[];
}
