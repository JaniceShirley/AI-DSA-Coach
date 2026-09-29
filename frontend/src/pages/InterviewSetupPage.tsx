import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { interviewService } from '../services/interviewService';
import { problemService } from '../services/problemService';
import type { ProblemListItem } from '../types';
import {
  Brain,
  Sparkles,
  History,
  Play,
  Layers,
  CheckCircle2,
  ArrowRight,
  Loader2,
  AlertCircle
} from 'lucide-react';

export const InterviewSetupPage: React.FC = () => {
  const navigate = useNavigate();
  const [difficulty, setDifficulty] = useState<string>('Any');
  const [selectedTopic, setSelectedTopic] = useState<string>('Any');
  const [selectedProblemId, setSelectedProblemId] = useState<number | null>(null);
  const [problems, setProblems] = useState<ProblemListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProblems();
  }, []);

  const loadProblems = async () => {
    try {
      const data = await problemService.getProblems();
      setProblems(data);
    } catch (err) {
      console.error('Failed to load problems for interview:', err);
    }
  };

  const topics = [
    'Any',
    'Array',
    'Hash Table',
    'Two Pointers',
    'Sliding Window',
    'Stack',
    'Binary Search',
    'Linked List',
    'Tree',
    'Graph',
    'Dynamic Programming',
  ];

  const handleStartInterview = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await interviewService.startInterview({
        difficulty: difficulty !== 'Any' ? difficulty : undefined,
        topic: selectedTopic !== 'Any' ? selectedTopic : undefined,
        problem_id: selectedProblemId || undefined,
      });
      navigate(`/interview/${res.session_id}`);
    } catch (err: unknown) {
      console.error('Failed to start interview:', err);
      setError('Failed to start mock interview session. Please verify backend service and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950 via-slate-900 to-slate-950 border border-indigo-500/20 p-8 shadow-2xl">
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Phase 5: Interactive Technical Mock Interview</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            AI Technical Mock Interview
          </h1>
          <p className="text-slate-300 text-sm max-w-2xl leading-relaxed">
            Simulate a high-stakes technical coding interview with an AI interviewer.
            Practice explaining your algorithmic intuition, deriving time/space complexities, evaluating edge cases, and implementing code in real-time.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link
              to="/interview/history"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-colors"
            >
              <History className="w-4 h-4 text-indigo-400" />
              <span>View Past Interview History</span>
            </Link>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-rose-200">Session Error</p>
            <p className="mt-0.5 text-xs">{error}</p>
          </div>
        </div>
      )}

      {/* Main Setup Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Configuration Form */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-lg">
          <h3 className="text-lg font-bold text-white border-b border-slate-800 pb-3 flex items-center space-x-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            <span>Interview Setup</span>
          </h3>

          {/* Difficulty Selection */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
              Target Difficulty
            </label>
            <div className="grid grid-cols-4 gap-2">
              {['Any', 'Easy', 'Medium', 'Hard'].map((diff) => (
                <button
                  key={diff}
                  type="button"
                  onClick={() => setDifficulty(diff)}
                  className={`py-2 px-3 rounded-xl border text-xs font-semibold transition-all ${
                    difficulty === diff
                      ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-white'
                  }`}
                >
                  {diff}
                </button>
              ))}
            </div>
          </div>

          {/* Topic Selection */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
              Topic Focus
            </label>
            <div className="flex flex-wrap gap-2">
              {topics.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setSelectedTopic(t)}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                    selectedTopic === t
                      ? 'bg-indigo-950 text-indigo-300 border-indigo-500'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Specific Problem Select (Optional) */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
              Specific Problem (Optional)
            </label>
            <select
              value={selectedProblemId || ''}
              onChange={(e) => setSelectedProblemId(e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">-- Random Problem from Selection --</option>
              {problems.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.id}. {p.title} ({p.difficulty})
                </option>
              ))}
            </select>
          </div>

          {/* Start Button */}
          <button
            onClick={handleStartInterview}
            disabled={loading}
            className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-sm font-bold flex items-center justify-center space-x-2 transition-all shadow-lg shadow-indigo-600/30"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Initializing AI Interviewer...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Start Technical Mock Interview</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Right: How It Works & Rubric Overview */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-lg">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Brain className="w-5 h-5 text-indigo-400" />
              <span>Interview Structure</span>
            </h3>

            <ul className="space-y-3 text-xs text-slate-300">
              <li className="flex items-start space-x-2.5">
                <span className="w-5 h-5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800 flex items-center justify-center shrink-0 font-bold text-[10px]">
                  1
                </span>
                <div>
                  <strong className="text-white block">Problem Clarification & Approach:</strong>
                  Explain requirements and your high-level algorithmic plan.
                </div>
              </li>
              <li className="flex items-start space-x-2.5">
                <span className="w-5 h-5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800 flex items-center justify-center shrink-0 font-bold text-[10px]">
                  2
                </span>
                <div>
                  <strong className="text-white block">Complexity & Edge Cases:</strong>
                  Derive Big-O bounds and test edge-case robustness.
                </div>
              </li>
              <li className="flex items-start space-x-2.5">
                <span className="w-5 h-5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800 flex items-center justify-center shrink-0 font-bold text-[10px]">
                  3
                </span>
                <div>
                  <strong className="text-white block">Coding & Verification:</strong>
                  Implement in the Monaco editor and verify against test cases.
                </div>
              </li>
              <li className="flex items-start space-x-2.5">
                <span className="w-5 h-5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800 flex items-center justify-center shrink-0 font-bold text-[10px]">
                  4
                </span>
                <div>
                  <strong className="text-white block">Evaluation Report:</strong>
                  Receive a structured performance report with strengths, rubric scores, and recommendations.
                </div>
              </li>
            </ul>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-2 text-xs text-slate-400">
            <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>Evaluation Rubric Criteria</span>
            </div>
            <p>
              Problem Understanding • Approach Quality • Complexity Analysis • Edge Cases • Optimization • Communication • Code Execution.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
