'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

type AuditLogItem = {
  id: string;
  action: string;
  entity_type: string;
  created_at: string;
  details: any;
};

type DashboardStats = {
  active_applications: number;
  resumes_generated: number;
  jobs_scored: number;
  recent_activity: AuditLogItem[];
};

const StatCard = ({ label, value, accent = false }: { label: string; value: number; accent?: boolean }) => (
  <div className="bg-background-secondary border border-border rounded-lg overflow-hidden relative">
    <div className="absolute top-0 left-0 w-1 h-full bg-brand"/>
    <div className="p-6 pl-7">
      <p className="text-sm text-text-secondary font-medium mb-1.5">{label}</p>
      <p className={`text-3xl font-bold ${accent ? 'text-brand' : 'text-text-primary'}`}>{value}</p>
    </div>
  </div>
);

const ActivityRow = ({ activity }: { activity: AuditLogItem }) => (
  <div className="flex items-center gap-4 px-4 py-3 bg-background-muted rounded-md border border-border-light hover:border-border transition-colors">
    <div className="w-4 h-4 rounded bg-brand shrink-0 flex items-center justify-center">
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <path d="M2.85 6.0125l-2.85-2.85 0.7125-0.7125 2.1375 2.1375 4.5875-4.5875 0.7125 0.7125-5.3 5.3z" fill="white"/>
      </svg>
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm text-text-primary font-medium capitalize truncate">{activity.action.replace(/_/g, ' ')}</p>
      <p className="text-xs text-text-muted mt-0.5">{new Date(activity.created_at).toLocaleString()}</p>
    </div>
    {activity.details && (
      <div className="hidden sm:block text-xs text-text-secondary bg-background-primary px-2 py-1 rounded truncate max-w-[200px]">
        {JSON.stringify(activity.details).substring(0, 40)}...
      </div>
    )}
  </div>
);

export default function DashboardPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/v1/dashboard/stats');
        if (response.ok) { const data = await response.json(); setStats(data); }
      } catch (error) { console.error('Failed to fetch stats:', error); }
      finally { setIsLoading(false); }
    };
    fetchStats();
  }, [isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center h-64">
        <div className="w-10 h-10 border-4 border-brand border-t-transparent rounded-full animate-spin"/>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto pb-8">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Welcome back, {user?.full_name?.split(' ')[0] || 'User'}</h1>
        <p className="text-sm text-text-secondary mt-1">Here's your pipeline overview for today</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <StatCard label="Active Applications" value={stats?.active_applications || 0} accent/>
        <StatCard label="Resumes Generated" value={stats?.resumes_generated || 0}/>
        <StatCard label="Jobs Scored" value={stats?.jobs_scored || 0}/>
      </div>

      {/* Pipeline Activity */}
      <div className="bg-background-secondary border border-border rounded-lg overflow-hidden">
        <div className="px-6 py-5 border-b border-border flex items-center justify-between">
          <h2 className="text-base font-semibold text-text-primary">Pipeline Activity</h2>
          <span className="text-xs text-text-muted bg-background-muted px-2.5 py-1 rounded-full">
            {stats?.recent_activity?.length || 0} events
          </span>
        </div>
        <div className="p-5">
          {stats?.recent_activity && stats.recent_activity.length > 0 ? (
            <div className="space-y-2.5">
              {stats.recent_activity.map((activity) => (
                <ActivityRow key={activity.id} activity={activity}/>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 border-2 border-dashed border-border-light rounded-lg">
              <div className="text-center">
                <svg className="mx-auto mb-3 text-text-muted" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
                <p className="text-text-muted text-sm">No recent activity found.</p>
                <p className="text-text-muted text-xs mt-1">Sync your local agent to start scoring jobs.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
