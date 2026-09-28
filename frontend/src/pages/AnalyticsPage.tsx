import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { analyticsService } from '../services/analyticsService';
import type { AnalyticsData } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { getDifficultyBadgeClass, getStatusBadgeClass } from '../utils/difficultyColors';
import { formatDate } from '../utils/formatting';
import {
  BarChart3,
  Trophy,
  Percent,
  Clock,
  Sparkles,
  ArrowRight,
  AlertCircle,
  FileCode2,
  PieChart as PieChartIcon
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie
} from 'recharts';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const result = await analyticsService.getAnalytics();
        setData(result);
      } catch (err) {
        console.error('Failed to load analytics:', err);
        setError('Failed to load progress analytics.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Calculating database analytics & progress metrics..." />;
  }

  if (error || !data) {
    return (
      <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">Analytics Unavailable</h3>
        <p className="text-slate-400 text-sm">{error || 'Data could not be retrieved.'}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500"
        >
          Retry
        </button>
      </div>
    );
  }

  const difficultyPieData = Object.entries(data.solved_by_difficulty).map(([diff, val]) => ({
    name: diff,
    value: val.solved,
    total: val.total,
  }));

  const COLORS = ['#10b981', '#f59e0b', '#f43f5e'];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center space-x-3">
            <BarChart3 className="w-8 h-8 text-indigo-400" />
            <span>Progress Analytics & Performance</span>
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Real-time performance analytics calculated directly from PostgreSQL submission records.
          </p>
        </div>
      </div>

      {/* Progress Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
            <Trophy className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Solved</p>
            <h3 className="text-2xl font-bold text-white mt-0.5">{data.solved_count} <span className="text-xs font-normal text-slate-500">/ {data.total_problems}</span></h3>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <FileCode2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Submissions</p>
            <h3 className="text-2xl font-bold text-white mt-0.5">{data.total_submissions}</h3>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400">
            <Percent className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Success Rate</p>
            <h3 className="text-2xl font-bold text-white mt-0.5">{data.success_rate}%</h3>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center space-x-4">
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Avg Attempts / Solved</p>
            <h3 className="text-2xl font-bold text-white mt-0.5">{data.average_attempts_per_solved}</h3>
          </div>
        </div>
      </div>

      {/* Weakest Topic Rule-Based Recommendation Card */}
      {data.recommended_problem && (
        <div className="bg-slate-900 border border-indigo-500/30 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/50 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl shrink-0 mt-1">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                  Targeted Weakest Topic Recommendation
                </span>
                <span className={`text-xs px-2.5 py-0.5 rounded font-semibold ${getDifficultyBadgeClass(data.recommended_problem.difficulty)}`}>
                  {data.recommended_problem.difficulty}
                </span>
              </div>
              <h3 className="text-xl font-bold text-white">{data.recommended_problem.title}</h3>
              <p className="text-xs text-slate-400">
                Recommended based on your topic completion rates and recent problem attempts.
              </p>
            </div>
          </div>

          <Link
            to={`/problems/${data.recommended_problem.slug}`}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold flex items-center justify-center space-x-2 transition-colors shrink-0 shadow-lg shadow-indigo-600/30"
          >
            <span>Solve Recommended Problem</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Topic Breakdown Bar Chart */}
        <div className="lg:col-span-8 bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <BarChart3 className="w-5 h-5 text-indigo-400" />
              <span>Solved Problems by Topic</span>
            </h3>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.solved_by_topic} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <XAxis dataKey="topic" stroke="#64748b" fontSize={10} tickLine={false} interval={0} angle={-30} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                <Bar dataKey="solved" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Difficulty Breakdown Pie Chart */}
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <PieChartIcon className="w-5 h-5 text-emerald-400" />
              <span>By Difficulty</span>
            </h3>
          </div>

          <div className="h-48 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={difficultyPieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={5}
                >
                  {difficultyPieData.map((_, index) => (
                    <Cell key={`pie-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-800 text-xs">
            {difficultyPieData.map((item, idx) => (
              <div key={item.name} className="flex justify-between items-center">
                <span className="flex items-center space-x-2 text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx] }}></span>
                  <span>{item.name}</span>
                </span>
                <span className="font-mono text-slate-400">{item.value} / {item.total}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Submissions Audit Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-bold text-white">Recent Submissions Log</h3>
          <span className="text-xs text-slate-400">Total: {data.total_submissions}</span>
        </div>

        {data.recent_submissions.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No code submissions logged yet. Solve a problem to record submissions!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/70 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Submission ID</th>
                  <th className="px-5 py-3.5">Problem</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5">Tests Passed</th>
                  <th className="px-5 py-3.5">Runtime</th>
                  <th className="px-5 py-3.5">Submitted At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data.recent_submissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-4 font-mono text-xs text-slate-400">#{sub.id}</td>
                    <td className="px-5 py-4 font-semibold text-white">
                      <Link to={`/problems/${sub.problem.slug}`} className="hover:text-indigo-400">
                        {sub.problem.title}
                      </Link>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`text-xs px-2.5 py-1 rounded font-semibold ${getStatusBadgeClass(sub.status)}`}>
                        {sub.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 font-mono text-xs">
                      {sub.test_cases_passed} / {sub.total_test_cases}
                    </td>
                    <td className="px-5 py-4 font-mono text-xs text-slate-400">
                      {sub.runtime} ms
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-400">
                      {formatDate(sub.created_at)}
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
