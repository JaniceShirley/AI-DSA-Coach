import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Code2 } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Code2 className="w-8 h-8" />
          </div>
        </Link>
        <h2 className="mt-4 text-3xl font-extrabold text-white tracking-tight">
          AI DSA Coach
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Master Data Structures & Algorithms with Progressive AI Mentorship
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900 border border-slate-800 py-8 px-4 shadow-xl rounded-2xl sm:px-10">
          <Outlet />
        </div>
      </div>
    </div>
  );
};
