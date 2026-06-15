'use client';

import Link from 'next/link';
import { Home, Search, FileText, BarChart3, Settings, Bell, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-screen bg-background-primary overflow-hidden">
      
      {/* SideNavBar */}
      <aside className="w-[240px] flex-shrink-0 border-r border-border bg-background-primary flex flex-col justify-between hidden md:flex">
        <div className="flex flex-col h-full">
          {/* Logo / Header */}
          <div className="h-16 flex items-center px-6 border-b border-border">
            <Link href="/" className="font-bold text-xl text-brand">SiraFit</Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-1">
            <Link href="/dashboard" className="flex items-center gap-3 px-4 py-3 rounded-md bg-brand-light border-l-2 border-brand text-brand font-medium">
              <Home className="w-5 h-5" />
              <span className="text-sm">Dashboard</span>
            </Link>
            
            <Link href="/dashboard/jobs" className="flex items-center gap-3 px-4 py-3 rounded-md text-text-secondary hover:bg-background-muted hover:text-text-primary transition-colors">
              <Search className="w-5 h-5" />
              <span className="text-sm">Job Pipeline</span>
            </Link>
            
            <Link href="/dashboard/resumes" className="flex items-center gap-3 px-4 py-3 rounded-md text-text-secondary hover:bg-background-muted hover:text-text-primary transition-colors">
              <FileText className="w-5 h-5" />
              <span className="text-sm">Resumes</span>
            </Link>

            <Link href="/dashboard/analytics" className="flex items-center gap-3 px-4 py-3 rounded-md text-text-secondary hover:bg-background-muted hover:text-text-primary transition-colors">
              <BarChart3 className="w-5 h-5" />
              <span className="text-sm">Analytics</span>
            </Link>
          </nav>

          {/* User / Settings (Footer of sidebar) */}
          <div className="p-4 border-t border-border space-y-1">
            <Link href="/dashboard/settings" className="flex items-center gap-3 px-4 py-3 rounded-md text-text-secondary hover:bg-background-muted hover:text-text-primary transition-colors">
              <Settings className="w-5 h-5" />
              <span className="text-sm">Settings</span>
            </Link>
            <div className="flex items-center gap-3 px-4 py-3 mt-2">
              <div className="w-8 h-8 rounded-full bg-border-light flex items-center justify-center text-text-secondary">
                <User className="w-4 h-4" />
              </div>
              <div className="flex flex-col truncate">
                <span className="text-sm font-medium text-text-primary leading-tight truncate">
                  {user?.full_name || 'User'}
                </span>
                <span className="text-xs text-text-muted truncate">
                  {user?.email || 'Loading...'}
                </span>
              </div>
            </div>
            <button 
              onClick={() => logout()} 
              className="block px-4 py-2 mt-2 text-xs font-medium text-text-secondary hover:text-brand hover:underline w-full text-left"
            >
              Log out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-background-primary relative">
        
        {/* TopNavBar */}
        <header className="h-16 w-full border-b border-border bg-background-primary flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-4 hidden md:flex">
            <h2 className="text-lg font-semibold text-text-primary">Dashboard</h2>
          </div>
          
          <div className="md:hidden flex items-center">
             <Link href="/" className="font-bold text-xl text-brand">SiraFit</Link>
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2 text-text-secondary hover:text-text-primary transition-colors rounded-full hover:bg-background-muted">
              <Bell className="w-5 h-5" />
            </button>
            <button className="bg-brand text-white px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 transition-opacity">
              + New Application
            </button>
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
