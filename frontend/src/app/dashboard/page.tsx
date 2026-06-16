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

export default function DashboardPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    const fetchStats = async () => {
      try {
        const response = await fetch('/api/v1/dashboard/stats');
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center">
        <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-text-primary">Welcome to your high-density workspace</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-background-secondary border border-border p-6 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-text-secondary mb-2">Active Applications</h3>
          <p className="text-3xl font-bold text-brand">{stats?.active_applications || 0}</p>
        </div>
        
        <div className="bg-background-secondary border border-border p-6 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-text-secondary mb-2">Resumes Generated</h3>
          <p className="text-3xl font-bold text-text-primary">{stats?.resumes_generated || 0}</p>
        </div>

        <div className="bg-background-secondary border border-border p-6 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-text-secondary mb-2">Jobs Scored</h3>
          <p className="text-3xl font-bold text-text-primary">{stats?.jobs_scored || 0}</p>
        </div>
      </div>

      <div className="bg-background-secondary border border-border rounded-lg shadow-sm p-6 min-h-[400px]">
        <h2 className="text-lg font-semibold text-text-primary mb-4">Pipeline Activity</h2>
        
        {stats?.recent_activity && stats.recent_activity.length > 0 ? (
          <div className="space-y-4">
            {stats.recent_activity.map((activity) => (
              <div key={activity.id} className="flex items-start gap-4 p-4 border border-border-light rounded-md">
                <div className="w-2 h-2 mt-2 rounded-full bg-brand shrink-0" />
                <div>
                  <p className="text-sm font-medium text-text-primary capitalize">
                    {activity.action.replace('_', ' ')}
                  </p>
                  <p className="text-xs text-text-muted mt-1">
                    {new Date(activity.created_at).toLocaleString()}
                  </p>
                  {activity.details && (
                    <div className="text-xs text-text-secondary mt-2 bg-background-muted p-2 rounded">
                      {JSON.stringify(activity.details)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-48 border-2 border-dashed border-border-light rounded-md">
            <p className="text-text-muted text-sm">No recent activity found. Sync your local agent to start scoring jobs.</p>
          </div>
        )}
      </div>
    </div>
  );
}