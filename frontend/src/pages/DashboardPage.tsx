import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { progressService } from '../services/progressService';
import type { DashboardStats } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { getDifficultyBadgeClass, getStatusBadgeClass } from '../utils/difficultyColors';
import {
  Trophy,
  Flame,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
  BarChart3,
  AlertCircle
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await progressService.getDashboardStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load dashboard stats:', err);
        setError('Failed to load progress data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading dashboard progress..." />;
  }

  if (error || !stats) {
    return (
      <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl text-center">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white mb-2">Error Loading Dashboard</h3>
        <p className="text-slate-400 text-sm mb-4">{error || 'Data unavailable'}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  const chartData = stats.topic_progress.map((tp) => ({
    name: tp.topic,
    solved: tp.solved,
    total: tp.total,
    percentage: tp.percentage,
  }));

  return (
    <div className="space-y-8">
      {/* Greeting Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between bg-gradient-to-r from-indigo-900/30 via-slate-900 to-slate-900 p-6 rounded-2xl border border-indigo-500/20">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Welcome back, {user?.name || 'Developer'} 👋
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Track your Data Structures & Algorithms progress and interview readiness.
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center space-x-3">
          <Link
            to="/problems"
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold flex items-center space-x-2 transition-colors shadow-lg shadow-indigo-600/20"
          >
            <span>Browse Problems</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Progress Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Solved Card */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
            <Trophy className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Problems Solved
            </p>
            <h3 className="text-2xl font-bold text-white mt-0.5">
              {stats.solved_count} <span className="text-sm font-normal text-slate-500">/ {stats.total_problems}</span>
            </h3>
          </div>
        </div>

        {/* Streak Card */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400">
            <Flame className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Current Streak
            </p>
            <h3 className="text-2xl font-bold text-white mt-0.5">
              {stats.current_streak} <span className="text-sm font-normal text-slate-500">days</span>
            </h3>
          </div>
        </div>

        {/* Attempted Card */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Attempted
            </p>
            <h3 className="text-2xl font-bold text-white mt-0.5">
              {stats.attempted_count}
            </h3>
          </div>
        </div>

        {/* Completion Rate */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Completion Rate
            </p>
            <h3 className="text-2xl font-bold text-white mt-0.5">
              {stats.total_problems > 0
                ? Math.round((stats.solved_count / stats.total_problems) * 100)
                : 0}
              %
            </h3>
          </div>
        </div>
      </div>

      {/* Recommended Problem Section */}
      {stats.recommended_problem && (
        <div className="bg-slate-900 border border-indigo-500/30 p-5 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40">
          <div className="flex items-start space-x-3.5">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-lg shrink-0 mt-1">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                  Recommended Problem
                </span>
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${getDifficultyBadgeClass(stats.recommended_problem.difficulty)}`}>
                  {stats.recommended_problem.difficulty}
                </span>
              </div>
              <h4 className="text-lg font-bold text-white mt-1">
                {stats.recommended_problem.title}
              </h4>
              <p className="text-xs text-slate-400 mt-0.5">
                Topics: {stats.recommended_problem.topics.join(' • ')}
              </p>
            </div>
          </div>

          <Link
            to={`/problems/${stats.recommended_problem.slug}`}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center justify-center space-x-2 transition-colors shrink-0"
          >
            <span>Solve Now</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Topic Performance Charts & Progress Bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recharts Bar Graph */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white">Topic Performance</h3>
            </div>
            <span className="text-xs text-slate-400">Solved per topic</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} interval={0} angle={-25} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="solved" radius={[4, 4, 0, 0]}>
                  {chartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#6366f1' : '#38bdf8'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Detailed Topic Progress Bars */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h3 className="text-base font-bold text-white mb-4">Topic Progress Breakdown</h3>
          <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
            {stats.topic_progress.map((item) => (
              <div key={item.topic} className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-300">{item.topic}</span>
                  <span className="text-slate-400 font-mono">
                    {item.solved} / {item.total} ({item.percentage}%)
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                    style={{ width: `${item.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Problems Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-bold text-white">Recent Activity</h3>
          <Link to="/problems" className="text-xs font-semibold text-indigo-400 hover:text-indigo-300">
            View all 30 problems →
          </Link>
        </div>

        {stats.recent_problems.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No recent activity yet. Start by exploring and solving problems!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/50 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3.5">Title</th>
                  <th className="px-6 py-3.5">Difficulty</th>
                  <th className="px-6 py-3.5">Topics</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {stats.recent_problems.map((prob) => (
                  <tr key={prob.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4 font-semibold text-white">
                      <Link to={`/problems/${prob.slug}`} className="hover:text-indigo-400">
                        {prob.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-xs px-2.5 py-1 rounded font-semibold ${getDifficultyBadgeClass(prob.difficulty)}`}>
                        {prob.difficulty}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {prob.topics.join(', ')}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-xs px-2.5 py-1 rounded font-semibold ${getStatusBadgeClass(prob.user_status)}`}>
                        {prob.user_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/problems/${prob.slug}`}
                        className="text-xs font-medium text-indigo-400 hover:text-indigo-300"
                      >
                        Open →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
