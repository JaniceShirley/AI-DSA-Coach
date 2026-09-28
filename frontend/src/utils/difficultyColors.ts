import type { Difficulty, ProblemStatus, SubmissionStatus } from '../types';

export const getDifficultyBadgeClass = (difficulty: Difficulty): string => {
  switch (difficulty) {
    case 'Easy':
      return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    case 'Medium':
      return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
    case 'Hard':
      return 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
    default:
      return 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
  }
};

export const getStatusBadgeClass = (status: ProblemStatus | SubmissionStatus | string): string => {
  switch (status) {
    case 'SOLVED':
    case 'ACCEPTED':
      return 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30';
    case 'ATTEMPTED':
    case 'WRONG_ANSWER':
      return 'bg-amber-500/15 text-amber-400 border border-amber-500/30';
    case 'RUNTIME_ERROR':
    case 'SYNTAX_ERROR':
    case 'TIME_LIMIT_EXCEEDED':
    case 'INTERNAL_ERROR':
      return 'bg-rose-500/15 text-rose-400 border border-rose-500/30';
    case 'UNSOLVED':
    default:
      return 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
  }
};
