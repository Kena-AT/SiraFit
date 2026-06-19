'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

const BrandLogo = () => (
  <Link href="/" className="flex items-center gap-2.5">
    <svg viewBox="0 0 18 18" width="22" height="22" fill="#3525cd"><path d="M10 6l0-6 8 0 0 6-8 0 0 0m-10 4l0-10 8 0 0 10-8 0 0 0m10 8l0-10 8 0 0 10-8 0 0 0m-10 0l0-6 8 0 0 6-8 0 0 0"/></svg>
    <span className="text-xl font-bold text-brand">SiraFit</span>
  </Link>
);

const DecoSvg = () => (
  <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.04]" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
    <defs><pattern id="rp-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#3525cd" strokeWidth="0.5"/></pattern></defs>
    <rect width="100%" height="100%" fill="url(#rp-grid)"/>
    <circle cx="200" cy="200" r="200" fill="#3525cd" opacity="0.05"/>
    <circle cx="80" cy="80" r="120" fill="#3525cd" opacity="0.04"/>
  </svg>
);

export default function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<'loading' | 'ready' | 'success' | 'error'>('loading');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!token) { setStatus('error'); setMessage('No reset token provided'); }
    else setStatus('ready');
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) { setMessage('Passwords do not match'); return; }
    if (password.length < 8) { setMessage('Password must be at least 8 characters'); return; }
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (response.ok) {
        setStatus('success');
        setMessage('Password reset successfully! Redirecting to login...');
        setTimeout(() => router.push('/login'), 3000);
      } else {
        const data = await response.json();
        setStatus('error');
        setMessage(data.detail || 'Failed to reset password');
      }
    } catch { setStatus('error'); setMessage('Network error. Please try again.'); }
    finally { setIsLoading(false); }
  };

  if (status === 'loading') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-4 relative overflow-hidden min-h-screen">
        <DecoSvg/>
        <div className="w-full max-w-[420px] flex flex-col items-center gap-8 relative z-10">
          <BrandLogo/>
          <div className="w-full bg-background-secondary border border-border rounded-lg shadow-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[3px] bg-brand"/>
            <div className="p-10 flex flex-col items-center gap-6">
              <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin"/>
              <p className="text-sm text-text-secondary">Validating token...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-4 relative overflow-hidden min-h-screen">
        <DecoSvg/>
        <div className="w-full max-w-[420px] flex flex-col items-center gap-8 relative z-10">
          <BrandLogo/>
          <div className="w-full bg-background-secondary border border-border rounded-lg shadow-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[3px] bg-brand"/>
            <div className="p-10 flex flex-col items-center gap-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-green-600">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/><path d="m16 19 2 2 4-4"/>
                </svg>
              </div>
              <div className="text-center">
                <h1 className="text-xl font-semibold text-text-primary mb-2">Password Reset!</h1>
                <p className="text-sm text-text-secondary">{message}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 py-12 relative overflow-hidden min-h-screen">
      <DecoSvg/>
      <div className="w-full max-w-[420px] flex flex-col items-center gap-8 relative z-10">
        <BrandLogo/>

        <div className="w-full bg-background-secondary border border-border rounded-lg shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-brand"/>
          <div className="p-8 pt-10 flex flex-col gap-6">
            <div className="flex flex-col gap-1.5 text-center">
              <h1 className="text-xl font-semibold text-text-primary">Reset your password</h1>
              <p className="text-sm text-text-secondary">Create a new, strong password below.</p>
            </div>

            {message && (
              <div className={`p-3 rounded-lg text-sm text-center border ${
                status === 'error' ? 'bg-red-50 text-red-600 border-red-200' : 'bg-green-50 text-green-600 border-green-200'
              }`}>{message}</div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="rp-password">New Password</label>
                <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  className="px-3.5 py-2.5 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary"
                  placeholder="Enter new password" required minLength={8}/>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="rp-confirm">Confirm New Password</label>
                <input id="confirm-password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                  className="px-3.5 py-2.5 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary"
                  placeholder="Confirm new password" required minLength={8}/>
              </div>

              <button type="submit" disabled={isLoading}
                className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
          </div>

          <div className="border-t border-border px-8 py-5 text-center text-sm text-text-secondary bg-background-primary/50">
            <Link href="/login" className="text-brand font-medium hover:underline">Back to Sign In</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
