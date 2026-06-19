'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email.trim()) { setError('Email is required'); return; }
    if (!password) { setError('Password is required'); return; }
    setIsLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 relative overflow-hidden min-h-screen">
      {/* Decorative background SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.04]" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="login-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#3525cd" strokeWidth="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#login-grid)"/>
        <path d="M0 320C120 280 280 360 400 320L400 400L0 400Z" fill="#3525cd" opacity="0.08"/>
        <circle cx="80" cy="120" r="180" fill="#3525cd" opacity="0.05"/>
        <circle cx="340" cy="300" r="120" fill="#3525cd" opacity="0.04"/>
      </svg>
      <div className="w-full max-w-[420px] flex flex-col items-center gap-8 relative z-10">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5">
          <svg viewBox="0 0 18 18" width="22" height="22" fill="#3525cd">
            <path d="M10 6l0-6 8 0 0 6-8 0 0 0m-10 4l0-10 8 0 0 10-8 0 0 0m10 8l0-10 8 0 0 10-8 0 0 0m-10 0l0-6 8 0 0 6-8 0 0 0"/>
          </svg>
          <span className="text-xl font-bold text-brand">SiraFit</span>
        </Link>

        {/* Card */}
        <div className="w-full bg-background-secondary border border-border rounded-lg shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-brand"/>
          <div className="p-8 pt-10 flex flex-col gap-6">
            <div className="flex flex-col gap-1.5 text-center">
              <h1 className="text-xl font-semibold text-text-primary">Welcome back</h1>
              <p className="text-sm text-text-secondary">Log in to your high-density workspace</p>
            </div>

            {error && (
              <div className="p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-600 text-center">{error}</div>
            )}

            <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="login-email">Email</label>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setError(''); }}
                  className="px-3.5 py-2.5 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary"
                  placeholder="Ex. dev@example.com"
                  autoComplete="email"
                  disabled={isLoading}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-text-primary" htmlFor="login-password">Password</label>
                  <Link href="/forgot-password" className="text-xs text-brand hover:underline">Forgot password?</Link>
                </div>
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(''); }}
                  className="px-3.5 py-2.5 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary"
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  disabled={isLoading}
                />
              </div>

              <button type="submit" disabled={isLoading}
                className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          </div>

          <div className="border-t border-border px-8 py-5 text-center text-sm text-text-secondary bg-background-primary/50">
            Don't have an account?
            <Link href="/register" className="ml-1.5 text-brand font-medium hover:underline">Create an account</Link>
          </div>
        </div>

        <p className="text-xs text-text-muted">&copy; 2024 SiraFit. High-density automation.</p>
      </div>
    </div>
  );
}
