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
    
    // Simple email validation
    if (!email.trim()) {
      setError('Email is required');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Invalid email format');
      return;
    }

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
        
        // Clear form
        setEmail('');
        
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      } else {
        const errorData = await response.json();
        setMessage({ type: 'error', text: errorData.detail || 'Failed to send reset link' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 bg-background-muted min-h-screen">
      <div className="w-full max-w-[400px] flex flex-col gap-6">
        
        {/* Auth Card */}
        <div className="bg-background-secondary border border-border rounded-lg shadow-sm flex flex-col overflow-hidden">
          
          {/* Header Section */}
          <div className="border-b border-border p-8 pb-6 flex flex-col gap-2 text-center">
            <Link href="/" className="text-2xl font-bold text-brand mb-2">SiraFit</Link>
            <h1 className="text-lg font-semibold text-text-primary">Forgot Password</h1>
            <p className="text-sm text-text-secondary">Enter your email and we'll send you a reset link.</p>
          </div>

          {/* Message Notification */}
          {message && (
            <div className={`mx-4 mb-4 p-4 rounded-lg text-sm text-center ${
              message.type === 'success' 
                ? 'bg-green-50 text-green-600 border border-green-200' 
                : 'bg-red-50 text-red-600 border border-red-200'
            }`}>
              {message.text}
            </div>
          )}

          {/* Form Section */}
          <div className="p-8 pb-6">
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="email">Email</label>
                <input 
                  id="email"
                  type="email" 
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError('');
                  }}
                  className={`px-3 py-2 border ${error ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand`}
                  placeholder="Ex. dev@example.com"
                />
                {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
              </div>

              <button 
                type="submit" 
                disabled={isLoading}
                className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
          </div>
          
          {/* Footer Navigation */}
          <div className="px-8 pb-8 text-center text-sm text-text-secondary">
            Remember your password? 
            <Link href="/login" className="ml-1 text-brand font-medium hover:underline">Sign In</Link>
          </div>
        </div>

        {/* External Footer */}
        <div className="text-center text-xs text-text-secondary">
          Confidential & Proprietary. © 2024 SiraFit Inc.
        </div>
      </div>
    </div>
  );
}