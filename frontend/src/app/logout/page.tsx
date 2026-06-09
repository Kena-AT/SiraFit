'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function LogoutPage() {
  const { logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const performLogout = async () => {
      try {
        await logout();
      } catch (error) {
        console.error('Logout error:', error);
      } finally {
        router.push('/login');
      }
    };

    performLogout();
  }, [logout, router]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 pt-48 bg-background-primary min-h-screen">
      <div className="w-full max-w-[400px] flex flex-col gap-6">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center justify-center gap-1 opacity-70">
          <a href="/" className="text-xl font-bold text-brand">SiraFit</a>
        </div>

        {/* Logout Card */}
        <div className="relative bg-background-primary border border-border rounded-lg shadow-sm p-8 flex flex-col items-center text-center overflow-hidden">
          {/* Decorative Top Accent Line */}
          <div className="absolute top-0 left-0 w-full h-[3px] bg-brand"></div>

          <div className="w-12 h-12 rounded-full bg-border-light flex items-center justify-center text-text-secondary mb-4 mt-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </div>

          <h1 className="text-lg font-semibold text-text-primary mb-1">Logging out...</h1>
          <p className="text-sm text-text-secondary">Please wait while we sign you out securely.</p>
        </div>
      </div>
    </div>
  );
}