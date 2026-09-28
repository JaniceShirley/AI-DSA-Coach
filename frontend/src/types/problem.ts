export type Difficulty = 'Easy' | 'Medium' | 'Hard';
export type ProblemStatus = 'UNSOLVED' | 'ATTEMPTED' | 'SOLVED';

export interface Example {
  input: string;
  output: string;
  explanation?: string;
}

export interface ProblemListItem {
  id: number;
  title: string;
  slug: string;
  difficulty: Difficulty;
  topics: string[];
  patterns: string[];
  user_status: ProblemStatus;
}

export interface ProblemDetail extends ProblemListItem {
  description: string;
  constraints: string[];
  examples: Example[];
  starter_code: Record<string, string>;
  created_at: string;
}
