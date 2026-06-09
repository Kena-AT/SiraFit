import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function DashboardPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
    setIsLoading(false);
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
          <p className="text-3xl font-bold text-brand">12</p>
        </div>
        
        <div className="bg-background-secondary border border-border p-6 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-text-secondary mb-2">Resumes Generated</h3>
          <p className="text-3xl font-bold text-text-primary">24</p>
        </div>

        <div className="bg-background-secondary border border-border p-6 rounded-lg shadow-sm">
          <h3 className="text-sm font-medium text-text-secondary mb-2">Jobs Scored</h3>
          <p className="text-3xl font-bold text-text-primary">156</p>
        </div>
      </div>

      <div className="bg-background-secondary border border-border rounded-lg shadow-sm p-6 min-h-[400px]">
        <h2 className="text-lg font-semibold text-text-primary mb-4">Pipeline Activity</h2>
        {/* Placeholder for timeline/activity feed */}
        <div className="flex items-center justify-center h-48 border-2 border-dashed border-border-light rounded-md">
          <p className="text-text-muted text-sm">No recent activity found. Sync your local agent to start scoring jobs.</p>
        </div>
      </div>
    </div>
  );
}