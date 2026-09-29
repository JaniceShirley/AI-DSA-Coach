import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { interviewService } from '../services/interviewService';
import type { InterviewSessionListItem, Difficulty } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { getDifficultyBadgeClass } from '../utils/difficultyColors';
import { formatDate } from '../utils/formatting';
import {
  History,
  BrainCircuit,
  Plus,
  ArrowRight,
  AlertCircle
} from 'lucide-react';

export const InterviewHistoryPage: React.FC = () => {
  const [sessions, setSessions] = useState<InterviewSessionListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInterviews();
  }, []);

  const loadInterviews = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await interviewService.getInterviews();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load interview history:', err);
      setError('Failed to retrieve past interview sessions.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading interview history..." />;
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/40 rounded-xl text-indigo-400">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Mock Interview History
            </h1>
            <p className="text-xs text-slate-400">
              Review your past technical interview performances, scores, and evaluations.
            </p>
          </div>
        </div>

        <Link
          to="/interview"
          className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Mock Interview</span>
        </Link>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* History Table / List */}
      {sessions.length === 0 ? (
        <div className="p-12 bg-slate-900 border border-dashed border-slate-800 rounded-2xl text-center space-y-3">
          <BrainCircuit className="w-10 h-10 text-indigo-400 mx-auto opacity-70" />
          <h3 className="text-base font-bold text-white">No Mock Interviews Logged Yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Ready to test your technical communication and DSA problem-solving skills?
          </p>
          <Link
            to="/interview"
            className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-500 transition-colors"
          >
            <span>Start Your First Interview</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((sess) => (
            <div
              key={sess.id}
              className="bg-slate-900 border border-slate-800 hover:border-indigo-500/40 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all shadow-md"
            >
              <div className="space-y-1.5">
                <div className="flex items-center space-x-2.5">
                  <span className="text-xs font-mono text-slate-500">#{sess.id}</span>
                  <h3 className="text-sm font-bold text-white hover:text-indigo-300">
                    {sess.problem_title}
                  </h3>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${getDifficultyBadgeClass(sess.difficulty as Difficulty)}`}>
                    {sess.difficulty}
                  </span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${sess.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}`}>
                    {sess.status}
                  </span>
                </div>

                <div className="flex items-center space-x-4 text-xs text-slate-400">
                  <span>Stage: {sess.current_stage}</span>
                  <span>•</span>
                  <span>Date: {formatDate(sess.created_at)}</span>
                </div>
              </div>

              <div className="flex items-center space-x-4 shrink-0">
                {sess.overall_score !== null && (
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">Score</span>
                    <span className="text-lg font-extrabold text-indigo-400 font-mono">
                      {sess.overall_score} / 100
                    </span>
                  </div>
                )}

                <Link
                  to={`/interview/${sess.id}`}
                  className="px-4 py-2 bg-slate-950 hover:bg-indigo-600 text-slate-300 hover:text-white border border-slate-800 hover:border-indigo-500 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all"
                >
                  <span>{sess.status === 'COMPLETED' ? 'View Report' : 'Resume Session'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
