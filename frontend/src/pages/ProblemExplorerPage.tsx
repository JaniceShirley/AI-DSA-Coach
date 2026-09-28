import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { problemService } from '../services/problemService';
import type { ProblemListItem } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { getDifficultyBadgeClass, getStatusBadgeClass } from '../utils/difficultyColors';
import { Search, Filter, BookOpen, CheckCircle2, Circle, AlertCircle } from 'lucide-react';

const TOPIC_OPTIONS = [
  'All',
  'Array',
  'Hash Table',
  'Two Pointers',
  'Sliding Window',
  'String',
  'Binary Search',
  'Stack',
  'Linked List',
  'Tree',
  'Graphs',
  'Dynamic Programming',
  'Recursion',
];

export const ProblemExplorerPage: React.FC = () => {
  const [problems, setProblems] = useState<ProblemListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState<string>('');
  const [difficulty, setDifficulty] = useState<string>('All');
  const [topic, setTopic] = useState<string>('All');
  const [statusFilter, setStatusFilter] = useState<string>('All');

  const fetchProblems = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await problemService.getProblems({
        search: search || undefined,
        difficulty: difficulty !== 'All' ? difficulty : undefined,
        topic: topic !== 'All' ? topic : undefined,
        status_filter: statusFilter !== 'All' ? statusFilter : undefined,
      });
      setProblems(data);
    } catch (err) {
      console.error('Failed to fetch problems:', err);
      setError('Unable to load problems from the server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProblems();
  }, [search, difficulty, topic, statusFilter]);

  const totalProblems = problems.length;
  const solvedCount = problems.filter((p) => p.user_status === 'SOLVED').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center space-x-3">
            <BookOpen className="w-8 h-8 text-indigo-400" />
            <span>DSA Problem Explorer</span>
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Browse and solve 30 curated Data Structures & Algorithms interview questions.
          </p>
        </div>

        {/* Quick stats pill */}
        <div className="flex items-center space-x-3 bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl text-xs">
          <span className="text-slate-400">Showing: <strong className="text-white">{totalProblems}</strong> problems</span>
          <span className="text-slate-700">•</span>
          <span className="text-emerald-400 font-semibold">{solvedCount} Solved</span>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3 sm:space-y-0 sm:flex sm:items-center sm:space-x-4">
        {/* Search */}
        <div className="relative flex-grow">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search problems by title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Difficulty Filter */}
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400 shrink-0 hidden sm:block" />
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="w-full sm:w-auto px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="All">All Difficulties</option>
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
        </div>

        {/* Topic Filter */}
        <div>
          <select
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full sm:w-auto px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            {TOPIC_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {t === 'All' ? 'All Topics' : t}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full sm:w-auto px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="All">All Statuses</option>
            <option value="SOLVED">Solved</option>
            <option value="ATTEMPTED">Attempted</option>
            <option value="UNSOLVED">Unsolved</option>
          </select>
        </div>
      </div>

      {/* Main Problems View */}
      {loading ? (
        <LoadingSpinner message="Fetching problem catalog..." />
      ) : error ? (
        <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl text-center">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
          <p className="text-slate-300 font-medium">{error}</p>
          <button
            onClick={fetchProblems}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500"
          >
            Retry
          </button>
        </div>
      ) : problems.length === 0 ? (
        <div className="p-12 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-400">
          <p className="text-base font-semibold text-slate-300 mb-1">No problems found</p>
          <p className="text-xs">Try clearing your filters or search terms.</p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-950/70 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5 w-16 text-center">#</th>
                  <th className="px-5 py-3.5">Title</th>
                  <th className="px-5 py-3.5">Difficulty</th>
                  <th className="px-5 py-3.5">Topics & Patterns</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {problems.map((problem) => (
                  <tr
                    key={problem.id}
                    className="hover:bg-slate-800/40 transition-colors group"
                  >
                    <td className="px-5 py-4 text-center font-mono text-xs text-slate-500 font-bold">
                      {problem.id}
                    </td>
                    <td className="px-5 py-4 font-semibold text-white">
                      <Link
                        to={`/problems/${problem.slug}`}
                        className="hover:text-indigo-400 transition-colors flex items-center space-x-2"
                      >
                        <span>{problem.title}</span>
                      </Link>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`text-xs px-2.5 py-1 rounded font-semibold ${getDifficultyBadgeClass(problem.difficulty)}`}>
                        {problem.difficulty}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-1.5 max-w-xs">
                        {problem.topics.map((t) => (
                          <span
                            key={t}
                            className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center space-x-1.5">
                        {problem.user_status === 'SOLVED' ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        ) : problem.user_status === 'ATTEMPTED' ? (
                          <Circle className="w-4 h-4 text-amber-400 fill-amber-400/20 shrink-0" />
                        ) : (
                          <Circle className="w-4 h-4 text-slate-600 shrink-0" />
                        )}
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${getStatusBadgeClass(problem.user_status)}`}>
                          {problem.user_status}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        to={`/problems/${problem.slug}`}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-600 hover:text-white transition-all"
                      >
                        <span>Solve</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
