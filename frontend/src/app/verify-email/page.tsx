'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');
  
  const [status, setStatus] = useState<'verifying' | 'success' | 'error' | 'no-token'>('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus('no-token');
        setMessage('Please check your email for the verification link');
        return;
      }

      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/verify-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });

        if (response.ok) {
          setStatus('success');
          setMessage('Email verified successfully! Redirecting to login...');
          
          setTimeout(() => {
            router.push('/login');
          }, 3000);
        } else {
          const data = await response.json();
          setStatus('error');
          setMessage(data.detail || 'Failed to verify email');
        }
      } catch (error) {
        setStatus('error');
        setMessage('Network error. Please try again.');
      }
    };

    verifyEmail();
  }, [token, router]);

  if (status === 'no-token') {
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-background-primary justify-between">
        <header className="w-full h-14 bg-background-primary border-b border-border flex items-center px-4">
          <Link href="/" className="font-bold text-xl text-brand">SiraFit</Link>
        </header>
        <main className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-[480px] bg-background-secondary border border-border rounded-lg shadow-sm p-8 flex flex-col items-center gap-6">
            <div className="w-16 h-16 bg-brand-light rounded-full flex items-center justify-center text-brand">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"></path>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                <path d="m16 19 2 2 4-4"></path>
              </svg>
            </div>
            <div className="text-center flex flex-col gap-2">
              <h1 className="text-2xl font-bold text-text-primary">Check Your Email</h1>
              <p className="text-sm text-text-secondary mb-4">
                We've sent a verification link to your email address. Please click the link to activate your account.
              </p>
            </div>
            <div className="w-full h-[1px] bg-border-light my-2"></div>
            <div className="w-full flex flex-col gap-3">
              <Link href="/login" className="w-full text-center bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity">
                Back to Sign In
              </Link>
            </div>
          </div>
        </main>
        <footer className="w-full bg-background-primary border-t border-border py-8 px-4 flex justify-center">
          <p className="text-xs text-text-muted">© 2024 SiraFit Inc. All rights reserved.</p>
        </footer>
      </div>
    );
  }

  if (status === 'verifying') {
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-background-primary justify-between">
        <header className="w-full h-14 bg-background-primary border-b border-border flex items-center px-4">
          <Link href="/" className="font-bold text-xl text-brand">SiraFit</Link>
        </header>
        <main className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-[480px] bg-background-secondary border border-border rounded-lg shadow-sm p-8 flex flex-col items-center gap-6">
            <div className="w-16 h-16 bg-brand-light rounded-full flex items-center justify-center text-brand animate-pulse">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"></path>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                <path d="m16 19 2 2 4-4"></path>
              </svg>
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-bold text-text-primary mb-2">Verifying your email</h1>
              <p className="text-sm text-text-secondary">Please wait while we verify your email address.</p>
            </div>
          </div>
        </main>
        <footer className="w-full bg-background-primary border-t border-border py-8 px-4 flex justify-center">
          <p className="text-xs text-text-muted">© 2024 SiraFit Inc. All rights reserved.</p>
        </footer>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-background-primary justify-between">
        <header className="w-full h-14 bg-background-primary border-b border-border flex items-center px-4">
          <Link href="/" className="font-bold text-xl text-brand">SiraFit</Link>
        </header>
        <main className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-[480px] bg-background-secondary border border-border rounded-lg shadow-sm p-8 flex flex-col items-center gap-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-green-600">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"></path>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                <path d="m16 19 2 2 4-4"></path>
              </svg>
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-bold text-text-primary mb-2">Email Verified!</h1>
              <p className="text-sm text-text-secondary">{message}</p>
            </div>
            <Link href="/login" className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity text-center">
              Go to Login
            </Link>
          </div>
        </main>
        <footer className="w-full bg-background-primary border-t border-border py-8 px-4 flex justify-center">
          <p className="text-xs text-text-muted">© 2024 SiraFit Inc. All rights reserved.</p>
        </footer>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-background-primary justify-between">
      <header className="w-full h-14 bg-background-primary border-b border-border flex items-center px-4">
        <Link href="/" className="font-bold text-xl text-brand">SiraFit</Link>
      </header>
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-[480px] bg-background-secondary border border-border rounded-lg shadow-sm p-8 flex flex-col items-center gap-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-red-600">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
          </div>
          <div className="text-center flex flex-col gap-4">
            <h1 className="text-2xl font-bold text-text-primary">Verification Failed</h1>
            <p className="text-sm text-text-secondary">{message}</p>
            <Link href="/register" className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity text-center inline-block">
              Register Again
            </Link>
          </div>
        </div>
      </main>
      <footer className="w-full bg-background-primary border-t border-border py-8 px-4 flex justify-center">
        <p className="text-xs text-text-muted">© 2024 SiraFit Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}