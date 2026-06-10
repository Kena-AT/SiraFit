'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');
  
  const [status, setStatus] = useState<'loading' | 'ready' | 'success' | 'error'>('loading');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Validate token on mount
    if (!token) {
      setStatus('error');
      setMessage('No reset token provided');
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setMessage('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setMessage('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          token,
          new_password: password 
        }),
      });

      if (response.ok) {
        setStatus('success');
        setMessage('Password reset successfully! Redirecting to login...');
        
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      } else {
        const data = await response.json();
        setStatus('error');
        setMessage(data.detail || 'Failed to reset password');
      }
    } catch (error) {
      setStatus('error');
      setMessage('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (status === 'loading') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-4 py-20 bg-background-primary min-h-screen">
        <div className="w-full max-w-[448px] flex flex-col gap-6">
          <div className="flex justify-center mb-2">
            <Link href="/" className="text-2xl font-bold text-brand">SiraFit</Link>
          </div>
          <div className="bg-background-secondary border border-border rounded-lg shadow-sm p-10 flex flex-col gap-6 items-center">
            <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-text-secondary">Validating token...</p>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-4 py-20 bg-background-primary min-h-screen">
        <div className="w-full max-w-[448px] flex flex-col gap-6">
          <div className="flex justify-center mb-2">
            <Link href="/" className="text-2xl font-bold text-brand">SiraFit</Link>
          </div>
          <div className="bg-background-secondary border border-border rounded-lg shadow-sm p-10 flex flex-col gap-6 items-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-green-600">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"></path>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                <path d="m16 19 2 2 4-4"></path>
              </svg>
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-bold text-text-primary mb-2">Password Reset!</h1>
              <p className="text-sm text-text-secondary">{message}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 py-20 bg-background-primary min-h-screen">
      <div className="w-full max-w-[448px] flex flex-col gap-6">
        
        {/* Brand Logo */}
        <div className="flex justify-center mb-2">
          <Link href="/" className="text-2xl font-bold text-brand">SiraFit</Link>
        </div>

        {/* Auth Card */}
        <div className="bg-background-secondary border border-border rounded-lg shadow-sm p-10 flex flex-col gap-6">
          <div className="flex flex-col gap-2 text-center">
            <h1 className="text-xl font-semibold text-text-primary">Reset your password</h1>
            <p className="text-sm text-text-secondary">Create a new, strong password below.</p>
          </div>

          {message && (
            <div className={`p-4 rounded-lg text-sm text-center ${
              status === 'error' 
                ? 'bg-red-50 text-red-600 border border-red-200' 
                : 'bg-green-50 text-green-600 border border-green-200'
            }`}>
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-text-primary" htmlFor="password">New Password</label>
              <input 
                id="password"
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
                placeholder="Enter new password"
                required
                minLength={8}
              />
            </div>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-text-primary" htmlFor="confirm-password">Confirm New Password</label>
              <input 
                id="confirm-password"
                type="password" 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
                placeholder="Confirm new password"
                required
                minLength={8}
              />
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>

          <div className="text-center text-sm text-text-secondary">
            <Link href="/login" className="hover:text-brand hover:underline">
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}