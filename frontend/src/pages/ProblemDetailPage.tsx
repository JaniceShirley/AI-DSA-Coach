import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { problemService } from '../services/problemService';
import { progressService } from '../services/progressService';
import { submissionService } from '../services/submissionService';
import type { ProblemDetail, UserProblemProgress, ProblemStatus, Submission, RunCodeResponse } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { CodeEditor } from '../components/CodeEditor';
import { AICoachPanel } from '../components/AICoachPanel';
import { getDifficultyBadgeClass, getStatusBadgeClass } from '../utils/difficultyColors';
import { formatDate } from '../utils/formatting';
import {
  ArrowLeft,
  CheckCircle2,
  Code2,
  AlertCircle,
  Play,
  Send,
  RotateCcw,
  History,
  XCircle
} from 'lucide-react';

export const ProblemDetailPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();

  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [progress, setProgress] = useState<UserProblemProgress | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Editor & Execution State
  const [code, setCode] = useState<string>('');
  const [language, setLanguage] = useState<string>('python');
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [execResult, setExecResult] = useState<RunCodeResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'statement' | 'history'>('statement');
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null);

  useEffect(() => {
    const loadProblemData = async () => {
      if (!slug) return;
      try {
        setLoading(true);
        setError(null);
        const probData = await problemService.getProblemBySlug(slug);
        setProblem(probData);

        // Set starter code
        const initialCode = probData.starter_code?.python || '# Write your solution here\n';
        setCode(initialCode);

        // Fetch user problem progress & submission history
        try {
          const [progData, subHistory] = await Promise.all([
            progressService.getProblemProgress(probData.id),
            submissionService.getSubmissions(probData.id),
          ]);
          setProgress(progData);
          setSubmissions(subHistory);
        } catch {
          // Progress fetch silent fallback
        }
      } catch (err) {
        console.error('Failed to load problem:', err);
        setError(`Problem '${slug}' not found or failed to load.`);
      } finally {
        setLoading(false);
      }
    };

    loadProblemData();
  }, [slug]);

  const handleResetCode = () => {
    if (problem?.starter_code?.python) {
      setCode(problem.starter_code.python);
    }
  };

  const handleRunCode = async () => {
    if (!problem) return;
    try {
      setIsExecuting(true);
      setExecResult(null);
      const res = await submissionService.runCode(problem.id, code, language);
      setExecResult(res);
    } catch (err: unknown) {
      console.error('Run code error:', err);
      setExecResult({
        status: 'INTERNAL_ERROR',
        test_cases_passed: 0,
        total_test_cases: 0,
        runtime: 0,
        memory: 0,
        error_message: 'Execution error while contacting server.',
        results: [],
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSubmitSolution = async () => {
    if (!problem) return;
    try {
      setIsExecuting(true);
      setExecResult(null);
      const submission = await submissionService.submitCode(problem.id, code, language);

      // Refresh progress & submission history after submit
      const [updatedProg, updatedHistory] = await Promise.all([
        progressService.getProblemProgress(problem.id),
        submissionService.getSubmissions(problem.id),
      ]);

      setProgress(updatedProg);
      setSubmissions(updatedHistory);
      setProblem((prev) => (prev ? { ...prev, user_status: updatedProg.status as ProblemStatus } : null));

      // Display run result format from submission
      setExecResult({
        status: submission.status,
        test_cases_passed: submission.test_cases_passed,
        total_test_cases: submission.total_test_cases,
        runtime: submission.runtime,
        memory: submission.memory,
        error_message: submission.error_message,
        results: [],
      });
    } catch (err) {
      console.error('Submit code error:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading Monaco Editor & Problem details..." />;
  }

  if (error || !problem) {
    return (
      <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">Problem Not Found</h3>
        <p className="text-slate-400 text-sm">{error || 'Requested problem does not exist.'}</p>
        <Link
          to="/problems"
          className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Problems</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Back Button & Problem Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-3">
          <Link
            to="/problems"
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                {problem.id}. {problem.title}
              </h1>
              <span className={`text-xs px-2.5 py-0.5 rounded font-semibold ${getDifficultyBadgeClass(problem.difficulty)}`}>
                {problem.difficulty}
              </span>
              <span className={`text-xs px-2.5 py-0.5 rounded font-semibold ${getStatusBadgeClass(problem.user_status)}`}>
                {problem.user_status}
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation (Statement vs Submission History) */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 p-1 rounded-lg text-xs">
          <button
            onClick={() => setActiveTab('statement')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              activeTab === 'statement' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Description & Examples
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors flex items-center space-x-1.5 ${
              activeTab === 'history' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Submissions ({submissions.length})</span>
          </button>
        </div>
      </div>

      {/* Main Two-Panel Coding Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[600px]">
        {/* LEFT PANEL: Problem Description / Submission History */}
        <div className="lg:col-span-6 space-y-4 max-h-[750px] overflow-y-auto pr-1">
          {activeTab === 'statement' ? (
            <>
              {/* Description */}
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
                <h3 className="text-base font-bold text-white border-b border-slate-800 pb-2">
                  Problem Description
                </h3>
                <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-line font-sans">
                  {problem.description}
                </div>

                <div className="pt-2 flex flex-wrap gap-2">
                  {problem.topics.map((t) => (
                    <span key={t} className="text-xs px-2.5 py-1 bg-slate-800 text-indigo-300 rounded border border-slate-700">
                      Topic: {t}
                    </span>
                  ))}
                  {problem.patterns.map((p) => (
                    <span key={p} className="text-xs px-2.5 py-1 bg-indigo-950/60 text-indigo-400 rounded border border-indigo-800/50">
                      Pattern: {p}
                    </span>
                  ))}
                </div>
              </div>

              {/* Examples */}
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
                <h3 className="text-base font-bold text-white border-b border-slate-800 pb-2">
                  Examples
                </h3>
                <div className="space-y-4">
                  {problem.examples.map((ex, index) => (
                    <div key={index} className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2 text-xs font-mono">
                      <p className="text-slate-400 font-bold">Example {index + 1}:</p>
                      <p><span className="text-slate-500">Input:</span> <span className="text-slate-200">{ex.input}</span></p>
                      <p><span className="text-slate-500">Output:</span> <span className="text-emerald-400 font-bold">{ex.output}</span></p>
                      {ex.explanation && (
                        <p><span className="text-slate-500 font-sans">Explanation:</span> <span className="text-slate-300 font-sans">{ex.explanation}</span></p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Constraints */}
              {problem.constraints && problem.constraints.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-3">
                  <h3 className="text-base font-bold text-white border-b border-slate-800 pb-2">
                    Constraints
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-xs text-slate-300 font-mono">
                    {problem.constraints.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Integrated AI DSA Coach Panel */}
              <AICoachPanel
                problemId={problem.id}
                studentCode={code}
                latestSubmissionId={submissions.length > 0 ? submissions[0].id : undefined}
              />

              {/* Progress Stats Summary */}
              {progress && (
                <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-2">
                    Your Problem Progress
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-500 block">Total Attempts:</span>
                      <span className="font-semibold text-slate-200">{progress.attempts}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Status:</span>
                      <span className={`font-semibold ${progress.status === 'SOLVED' ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {progress.status}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* SUBMISSION HISTORY TAB */
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
              <h3 className="text-base font-bold text-white border-b border-slate-800 pb-2 flex items-center space-x-2">
                <History className="w-5 h-5 text-indigo-400" />
                <span>Your Submissions</span>
              </h3>

              {submissions.length === 0 ? (
                <div className="py-12 text-center text-slate-500 text-xs">
                  No submissions logged for this problem yet. Submit your code to see history!
                </div>
              ) : (
                <div className="space-y-3">
                  {submissions.map((sub) => (
                    <div
                      key={sub.id}
                      onClick={() => {
                        setSelectedSubmission(sub);
                        setCode(sub.code);
                      }}
                      className={`p-4 rounded-xl border text-xs cursor-pointer transition-all ${
                        selectedSubmission?.id === sub.id
                          ? 'bg-indigo-950/40 border-indigo-500/50 shadow-md'
                          : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className={`px-2.5 py-0.5 rounded font-bold ${getStatusBadgeClass(sub.status)}`}>
                            {sub.status}
                          </span>
                          <span className="text-slate-400 font-mono">#{sub.id}</span>
                        </div>
                        <span className="text-slate-500">{formatDate(sub.created_at)}</span>
                      </div>

                      <div className="mt-2.5 flex items-center justify-between text-slate-400 font-mono text-[11px]">
                        <span>Passed: {sub.test_cases_passed} / {sub.total_test_cases}</span>
                        <span>Runtime: {sub.runtime} ms</span>
                        <span className="text-indigo-400 hover:underline font-sans font-medium">Load Code →</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT PANEL: Monaco Code Editor & Execution Panel */}
        <div className="lg:col-span-6 flex flex-col space-y-4">
          {/* Action Header */}
          <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1.5 text-xs text-slate-300">
                <Code2 className="w-4 h-4 text-indigo-400" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-white focus:outline-none"
                >
                  <option value="python">Python 3</option>
                </select>
              </div>

              <button
                onClick={handleResetCode}
                title="Reset to starter code"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors text-xs flex items-center space-x-1"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Reset</span>
              </button>
            </div>

            {/* Run & Submit Action Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleRunCode}
                disabled={isExecuting}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors"
              >
                <Play className="w-3.5 h-3.5 text-emerald-400" />
                <span>{isExecuting ? 'Running...' : 'Run'}</span>
              </button>

              <button
                onClick={handleSubmitSolution}
                disabled={isExecuting}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors shadow-md shadow-indigo-600/20"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{isExecuting ? 'Submitting...' : 'Submit'}</span>
              </button>
            </div>
          </div>

          {/* Monaco Editor Container */}
          <div className="flex-grow min-h-[380px] rounded-xl overflow-hidden">
            <CodeEditor code={code} onChange={setCode} language={language} />
          </div>

          {/* Execution & Test Case Output Panel */}
          {execResult && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2.5 py-1 rounded font-bold ${getStatusBadgeClass(execResult.status)}`}>
                    {execResult.status}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Passed: {execResult.test_cases_passed} / {execResult.total_test_cases}
                  </span>
                </div>
                <span className="text-xs text-slate-400 font-mono">{execResult.runtime} ms</span>
              </div>

              {execResult.error_message && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-300 font-mono text-xs whitespace-pre-wrap">
                  {execResult.error_message}
                </div>
              )}

              {/* Detailed Test Case Output List */}
              {execResult.results && execResult.results.length > 0 && (
                <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                  {execResult.results.map((res, idx) => (
                    <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1 font-mono">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-400">Test Case {idx + 1}:</span>
                        {res.passed ? (
                          <span className="text-emerald-400 flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Passed</span>
                          </span>
                        ) : (
                          <span className="text-rose-400 flex items-center space-x-1">
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Failed</span>
                          </span>
                        )}
                      </div>
                      <p><span className="text-slate-500">Input:</span> {res.input}</p>
                      <p><span className="text-slate-500">Expected:</span> <span className="text-emerald-400">{res.expected_output}</span></p>
                      <p><span className="text-slate-500">Actual:</span> <span className={res.passed ? 'text-emerald-400' : 'text-rose-400'}>{res.actual_output}</span></p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
