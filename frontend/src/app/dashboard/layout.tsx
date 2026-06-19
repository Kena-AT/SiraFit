'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

const SvgIcon = ({ path, size = 20, className = '' }: { path: string; size?: number; className?: string }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} fill="currentColor" className={className} xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d={path} />
  </svg>
);

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: 'M10 6l0-6 8 0 0 6-8 0 0 0m-10 4l0-10 8 0 0 10-8 0 0 0m10 8l0-10 8 0 0 10-8 0 0 0m-10 0l0-6 8 0 0 6-8 0 0 0' },
  { href: '/dashboard/jobs', label: 'Job Pipeline', icon: 'M2 19c-0.55 0-1.02083-0.19583-1.4125-0.5875-0.39167-0.39167-0.5875-0.8625-0.5875-1.4125l0-11c0-0.55 0.19583-1.02083 0.5875-1.4125 0.39167-0.39167 0.8625-0.5875 1.4125-0.5875l4 0 0-2c0-0.55 0.19583-1.02083 0.5875-1.4125 0.39167-0.39167 0.8625-0.5875 1.4125-0.5875l4 0c0.55 0 1.02083 0.19583 1.4125 0.5875 0.39167 0.39167 0.5875 0.8625 0.5875 1.4125l0 2 4 0c0.55 0 1.02083 0.19583 1.4125 0.5875 0.39167 0.39167 0.5875 0.8625 0.5875 1.4125l0 11c0 0.55-0.19583 1.02083-0.5875 1.4125-0.39167 0.39167-0.8625 0.5875-1.4125 0.5875l-16 0 0 0m0-2l16 0 0 0 0 0 0-11 0 0 0 0-16 0 0 0 0 0 0 11 0 0 0 0 0 0' },
  { href: '/dashboard/resumes', label: 'Resumes', icon: 'M2 20c-0.55 0-1.02083-0.19583-1.4125-0.5875-0.39167-0.39167-0.5875-0.8625-0.5875-1.4125l0-11c0-0.55 0.19583-1.02083 0.5875-1.4125 0.39167-0.39167 0.8625-0.5875 1.4125-0.5875l5 0 0-3c0-0.55 0.19583-1.02083 0.5875-1.4125 0.39167-0.39167 0.8625-0.5875 1.4125-0.5875l2 0c0.55 0 1.02083 0.19583 1.4125 0.5875 0.39167 0.39167 0.5875 0.8625 0.5875 1.4125l0 3 5 0c0.55 0 1.02083 0.19583 1.4125 0.5875 0.39167 0.39167 0.5875 0.8625 0.5875 1.4125l0 11c0 0.55-0.19583 1.02083-0.5875 1.4125-0.39167 0.39167-0.8625 0.5875-1.4125 0.5875l-16 0 0 0m0-2l16 0 0 0 0 0 0-11 0 0 0 0-5 0 0 0c0 0.55-0.19583 1.02083-0.5875 1.4125-0.39167 0.39167-0.8625 0.5875-1.4125 0.5875l-2 0c-0.55 0-1.02083-0.19583-1.4125-0.5875-0.39167-0.39167-0.5875-0.8625-0.5875-1.4125l0 0-5 0 0 0 0 0 0 11 0 0 0 0 0 0' },
  { href: '/dashboard/analytics', label: 'Analytics', icon: 'M4 14l2 0 0-5-2 0 0 5 0 0m8 0l2 0 0-10-2 0 0 10 0 0m-4 0l2 0 0-3-2 0 0 3 0 0m0-5l2 0 0-2-2 0 0 2 0 0m-6 9c-0.55 0-1.02083-0.19583-1.4125-0.5875-0.39167-0.39167-0.5875-0.8625-0.5875-1.4125l0-14c0-0.55 0.19583-1.02083 0.5875-1.4125 0.39167-0.39167 0.8625-0.5875 1.4125-0.5875l14 0c0.55 0 1.02083 0.19583 1.4125 0.5875 0.39167 0.39167 0.5875 0.8625 0.5875 1.4125l0 14c0 0.55-0.19583 1.02083-0.5875 1.4125-0.39167 0.39167-0.8625 0.5875-1.4125 0.5875l-14 0 0 0m0-2l14 0 0 0 0 0 0-14 0 0 0 0-14 0 0 0 0 0 0 14 0 0 0 0 0 0' },
  { href: '/dashboard/settings', label: 'Settings', icon: 'M7.3 20l-0.4-3.2c-0.21667-0.08333-0.42083-0.18333-0.6125-0.3-0.19167-0.11667-0.37917-0.24167-0.5625-0.375l-2.975 1.25-2.75-4.75 2.575-1.95c-0.01667-0.11667-0.025-0.22917-0.025-0.3375 0-0.10833 0-0.22083 0-0.3375 0-0.11667 0-0.22917 0-0.3375 0-0.10833 0.00833-0.22083 0.025-0.3375l-2.575-1.95 2.75-4.75 2.975 1.25c0.18333-0.13333 0.375-0.25833 0.575-0.375 0.2-0.11667 0.4-0.21667 0.6-0.3l0.4-3.2 5.5 0 0.4 3.2c0.21667 0.08333 0.42083 0.18333 0.6125 0.3 0.19167 0.11667 0.37917 0.24167 0.5625 0.375l2.975-1.25 2.75 4.75-2.575 1.95c0.01667 0.11667 0.025 0.22917 0.025 0.3375 0 0.10833 0 0.22083 0 0.3375 0 0.11667 0 0.22917 0 0.3375 0 0.10833-0.01667 0.22083-0.05 0.3375l2.575 1.95-2.75 4.75-2.95-1.25c-0.18333 0.13333-0.375 0.25833-0.575 0.375-0.2 0.11667-0.4 0.21666-0.6 0.3l-0.4 3.2-5.5 0 0 0', bottom: true },
];

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/dashboard/jobs': 'Job Pipeline',
  '/dashboard/resumes': 'Resumes',
  '/dashboard/analytics': 'Analytics',
  '/dashboard/profile': 'Profile',
  '/dashboard/settings': 'Settings',
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const firstName = user?.full_name?.charAt(0) || 'U';

  return (
    <div className="flex h-screen bg-background-primary overflow-hidden">
      {/* SideNavBar */}
      <aside className="w-[240px] flex-shrink-0 border-r border-border bg-background-primary flex flex-col justify-between hidden md:flex">
        <div className="flex flex-col h-full">
          {/* Logo / Header */}
          <div className="px-4 pt-4 pb-3 border-b border-border">
            <div className="flex items-center gap-3 px-2">
              <div className="w-8 h-8 rounded bg-brand flex items-center justify-center">
                <span className="text-xs font-bold text-white">{firstName}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-text-primary leading-tight">Control Center</span>
                <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">Automation Active</span>
              </div>
            </div>
            <div className="mt-3">
              <Link href="/dashboard/jobs"
                className="flex items-center gap-2 w-full bg-brand text-white px-4 py-2 rounded-md text-xs font-medium hover:opacity-90 transition-opacity"
              >
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path d="M4.17 5.83H0V4.17h4.17V0h1.66v4.17H10v1.66H5.83V10H4.17V5.83z" fill="white"/>
                </svg>
                New Automation
              </Link>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
            {navItems.filter(n => !n.bottom).map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.href} href={item.href}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-brand-light border-l-2 border-brand text-brand font-medium'
                      : 'text-text-secondary hover:bg-background-muted hover:text-text-primary'
                  }`}
                >
                  <SvgIcon path={item.icon} size={20} className="w-5 h-5 shrink-0"/>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* User / Settings footer */}
          <div className="px-2 py-3 border-t border-border space-y-0.5">
            {navItems.filter(n => n.bottom).map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.href} href={item.href}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-brand-light border-l-2 border-brand text-brand font-medium'
                      : 'text-text-secondary hover:bg-background-muted hover:text-text-primary'
                  }`}
                >
                  <SvgIcon path={item.icon} size={20} className="w-5 h-5 shrink-0"/>
                  <span>{item.label}</span>
                </Link>
              );
            })}
            <div className="flex items-center gap-3 px-4 py-3 mt-1">
              <div className="w-8 h-8 rounded-full bg-brand-light flex items-center justify-center text-brand text-xs font-bold">
                {firstName}
              </div>
              <div className="flex flex-col truncate min-w-0">
                <span className="text-sm font-medium text-text-primary leading-tight truncate">{user?.full_name || 'User'}</span>
                <span className="text-xs text-text-muted truncate">{user?.email || 'Loading...'}</span>
              </div>
            </div>
            <button onClick={() => logout()}
              className="flex items-center gap-3 px-4 py-2.5 rounded-md text-sm text-text-secondary hover:text-red-500 hover:bg-red-50 w-full transition-colors"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              <span>Log out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-background-primary relative">
        {/* TopNavBar */}
        <header className="h-16 w-full border-b border-border bg-background-primary flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-4 hidden md:flex">
            <h2 className="text-lg font-semibold text-text-primary">{pageTitles[pathname] || 'Dashboard'}</h2>
          </div>
          <div className="md:hidden flex items-center">
            <Link href="/" className="flex items-center gap-2">
              <svg viewBox="0 0 18 18" width="20" height="20" fill="#3525cd">
                <path d="M10 6l0-6 8 0 0 6-8 0 0 0m-10 4l0-10 8 0 0 10-8 0 0 0m10 8l0-10 8 0 0 10-8 0 0 0m-10 0l0-6 8 0 0 6-8 0 0 0"/>
              </svg>
              <span className="font-bold text-xl text-brand">SiraFit</span>
            </Link>
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 text-text-secondary hover:text-text-primary transition-colors rounded-full hover:bg-background-muted">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
            </button>
            <Link href="/dashboard/jobs"
              className="bg-brand text-white px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 transition-opacity"
            >
              + New Application
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
