'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) { setError('Email is required'); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError('Invalid email format'); return; }
    setError('');
    setIsLoading(true);
    setMessage(null);
    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });
      if (response.ok) {
        setMessage({ type: 'success', text: 'If the email exists, a reset link has been sent' });
        setEmail('');
        setTimeout(() => router.push('/login'), 3000);
      } else {
        const errorData = await response.json();
        setMessage({ type: 'error', text: errorData.detail || 'Failed to send reset link' });
      }
    } catch { setMessage({ type: 'error', text: 'Network error. Please try again.' }); }
    finally { setIsLoading(false); }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 relative overflow-hidden min-h-screen">
      {/* Decorative background SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.04]" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
        <defs><pattern id="fp-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#3525cd" strokeWidth="0.5"/></pattern></defs>
        <rect width="100%" height="100%" fill="url(#fp-grid)"/>
        <circle cx="320" cy="120" r="200" fill="#3525cd" opacity="0.05"/>
        <circle cx="80" cy="320" r="140" fill="#3525cd" opacity="0.04"/>
      </svg>
      <div className="w-full max-w-[420px] flex flex-col items-center gap-8 relative z-10">
        <Link href="/" className="flex items-center gap-2.5">
          <svg viewBox="0 0 18 18" width="22" height="22" fill="#3525cd">
            <path d="M10 6l0-6 8 0 0 6-8 0 0 0m-10 4l0-10 8 0 0 10-8 0 0 0m10 8l0-10 8 0 0 10-8 0 0 0m-10 0l0-6 8 0 0 6-8 0 0 0"/>
          </svg>
          <span className="text-xl font-bold text-brand">SiraFit</span>
        </Link>

        <div className="w-full bg-background-secondary border border-border rounded-lg shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-brand"/>
          <div className="p-8 pt-10 flex flex-col gap-6">
            <div className="flex flex-col gap-1.5 text-center">
              <h1 className="text-xl font-semibold text-text-primary">Forgot Password</h1>
              <p className="text-sm text-text-secondary">Enter your email and we'll send you a reset link.</p>
            </div>

            {message && (
              <div className={`p-3 rounded-lg text-sm text-center border ${
                message.type === 'success' ? 'bg-green-50 text-green-600 border-green-200' : 'bg-red-50 text-red-600 border-red-200'
              }`}>{message.text}</div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="fp-email">Email</label>
                <input id="fp-email" type="email" value={email}
                  onChange={(e) => { setEmail(e.target.value); if (error) setError(''); }}
                  className={`px-3.5 py-2.5 border ${error ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary`}
                  placeholder="Ex. dev@example.com"/>
                {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
              </div>
              <button type="submit" disabled={isLoading}
                className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
          </div>

          <div className="border-t border-border px-8 py-5 text-center text-sm text-text-secondary bg-background-primary/50">
            Remember your password?
            <Link href="/login" className="ml-1.5 text-brand font-medium hover:underline">Sign In</Link>
          </div>
        </div>

        <p className="text-xs text-text-muted">Confidential & Proprietary. &copy; 2024 SiraFit Inc.</p>
      </div>
    </div>
  );
}
