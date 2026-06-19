'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function LogoutPage() {
  const { logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const performLogout = async () => {
      try { await logout(); }
      catch (error) { console.error('Logout error:', error); }
      finally { router.push('/login'); }
    };
    performLogout();
  }, [logout, router]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 relative overflow-hidden min-h-screen">
      {/* Decorative background SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.04]" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
        <defs><pattern id="lo-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#3525cd" strokeWidth="0.5"/></pattern></defs>
        <rect width="100%" height="100%" fill="url(#lo-grid)"/>
        <path d="M0 260Q200 200 400 280L400 400L0 400Z" fill="#3525cd" opacity="0.06"/>
        <circle cx="340" cy="100" r="140" fill="#3525cd" opacity="0.04"/>
      </svg>
      <div className="w-full max-w-[420px] flex flex-col items-center gap-8 relative z-10">
        {/* Brand */}
        <div className="flex items-center gap-2.5 opacity-70">
          <svg viewBox="0 0 18 18" width="22" height="22" fill="#3525cd">
            <path d="M10 6l0-6 8 0 0 6-8 0 0 0m-10 4l0-10 8 0 0 10-8 0 0 0m10 8l0-10 8 0 0 10-8 0 0 0m-10 0l0-6 8 0 0 6-8 0 0 0"/>
          </svg>
          <span className="text-xl font-bold text-brand">SiraFit</span>
        </div>

        <div className="w-full bg-background-secondary border border-border rounded-lg shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-brand"/>
          <div className="p-10 flex flex-col items-center text-center gap-6">
            <div className="w-12 h-12 rounded-full bg-border-light flex items-center justify-center text-text-secondary">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-text-primary mb-1">Logging out...</h1>
              <p className="text-sm text-text-secondary">Please wait while we sign you out securely.</p>
            </div>
            <div className="w-8 h-8 border-4 border-brand border-t-transparent rounded-full animate-spin"/>
          </div>
        </div>
      </div>
    </div>
  );
}
