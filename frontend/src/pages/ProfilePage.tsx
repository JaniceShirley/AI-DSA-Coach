import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { progressService } from '../services/progressService';
import type { DashboardStats } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { formatDate } from '../utils/formatting';
import { User as UserIcon, Mail, Calendar, Trophy, Flame, CheckCircle2 } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadUserData = async () => {
      try {
        const data = await progressService.getDashboardStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load profile stats:', err);
      } finally {
        setLoading(false);
      }
    };

    loadUserData();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading user profile..." />;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* User Info Card */}
      <div className="bg-slate-900 border border-slate-800 p-6 sm:p-8 rounded-2xl flex flex-col sm:flex-row items-center sm:items-start space-y-4 sm:space-y-0 sm:space-x-6">
        <div className="w-20 h-20 rounded-full bg-indigo-600 text-white font-extrabold text-2xl flex items-center justify-center shrink-0 border-4 border-slate-800 shadow-xl">
          {user?.name?.[0]?.toUpperCase() || 'U'}
        </div>
        <div className="text-center sm:text-left space-y-2 flex-grow">
          <h1 className="text-2xl font-extrabold text-white tracking-tight">{user?.name}</h1>
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 text-xs text-slate-400">
            <span className="flex items-center space-x-1.5">
              <Mail className="w-4 h-4 text-slate-500" />
              <span>{user?.email}</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <Calendar className="w-4 h-4 text-slate-500" />
              <span>Joined {formatDate(user?.created_at)}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Progress Stats Summary */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl text-center space-y-2">
            <Trophy className="w-8 h-8 text-emerald-400 mx-auto" />
            <h3 className="text-3xl font-extrabold text-white">{stats.solved_count}</h3>
            <p className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Problems Solved</p>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl text-center space-y-2">
            <CheckCircle2 className="w-8 h-8 text-indigo-400 mx-auto" />
            <h3 className="text-3xl font-extrabold text-white">{stats.attempted_count}</h3>
            <p className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Problems Attempted</p>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl text-center space-y-2">
            <Flame className="w-8 h-8 text-amber-400 mx-auto" />
            <h3 className="text-3xl font-extrabold text-white">{stats.current_streak}</h3>
            <p className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Day Streak</p>
          </div>
        </div>
      )}

      {/* Account Info Details */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
        <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3 flex items-center space-x-2">
          <UserIcon className="w-5 h-5 text-indigo-400" />
          <span>Account Settings & Details</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-500 font-medium">User ID</span>
            <p className="text-slate-200 font-mono text-sm">{user?.id}</p>
          </div>
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-500 font-medium">Authentication Method</span>
            <p className="text-slate-200 font-semibold text-sm">Django REST JWT Bearer Token</p>
          </div>
        </div>
      </div>
    </div>
  );
};
