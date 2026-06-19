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
    <defs><pattern id="ve-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#3525cd" strokeWidth="0.5"/></pattern></defs>
    <rect width="100%" height="100%" fill="url(#ve-grid)"/>
    <circle cx="100" cy="120" r="200" fill="#3525cd" opacity="0.05"/>
    <circle cx="340" cy="300" r="100" fill="#3525cd" opacity="0.04"/>
  </svg>
);

const StatusCard = ({ icon, title, message, action }: { icon: React.ReactNode; title: string; message: string; action?: React.ReactNode }) => (
  <div className="w-full bg-background-secondary border border-border rounded-lg shadow-sm relative overflow-hidden">
    <div className="absolute top-0 left-0 right-0 h-[3px] bg-brand"/>
    <div className="p-10 flex flex-col items-center gap-6">
      <div className="w-16 h-16 rounded-full flex items-center justify-center">{icon}</div>
      <div className="text-center">
        <h1 className="text-xl font-semibold text-text-primary mb-2">{title}</h1>
        <p className="text-sm text-text-secondary">{message}</p>
      </div>
      {action}
    </div>
  </div>
);

export default function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<'verifying' | 'success' | 'error' | 'no-token'>('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) { setStatus('no-token'); setMessage('Please check your email for the verification link'); return; }
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/verify-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });
        if (response.ok) {
          setStatus('success');
          setMessage('Email verified successfully! Redirecting to login...');
          setTimeout(() => router.push('/login'), 3000);
        } else {
          const data = await response.json();
          setStatus('error');
          setMessage(data.detail || 'Failed to verify email');
        }
      } catch { setStatus('error'); setMessage('Network error. Please try again.'); }
    };
    verifyEmail();
  }, [token, router]);

  const renderContent = () => {
    switch (status) {
      case 'no-token':
        return (
          <StatusCard
            icon={<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#3525cd" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>}
            title="Check Your Email"
            message={message}
            action={<Link href="/login" className="mt-2 w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity text-center inline-block">Back to Sign In</Link>}
          />
        );
      case 'verifying':
        return (
          <StatusCard
            icon={<div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin"/>}
            title="Verifying your email"
            message="Please wait while we verify your email address."
          />
        );
      case 'success':
        return (
          <StatusCard
            icon={<div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-green-600"><svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/><path d="m16 19 2 2 4-4"/></svg></div>}
            title="Email Verified!"
            message={message}
            action={<Link href="/login" className="mt-2 w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity text-center inline-block">Go to Login</Link>}
          />
        );
      default:
        return (
          <StatusCard
            icon={<div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-red-600"><svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></div>}
            title="Verification Failed"
            message={message}
            action={<Link href="/register" className="mt-2 w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity text-center inline-block">Register Again</Link>}
          />
        );
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-background-primary relative overflow-hidden">
      <DecoSvg/>
      <header className="fixed top-0 w-full h-14 bg-background-primary border-b border-border flex items-center px-4 z-50">
        <BrandLogo/>
      </header>
      <main className="flex-1 flex items-center justify-center p-4 relative z-10">
        <div className="w-full max-w-[480px] flex flex-col items-center gap-8">
          {renderContent()}
        </div>
      </main>
      <footer className="w-full bg-background-primary border-t border-border py-6 px-4 flex justify-center relative z-10">
        <p className="text-xs text-text-muted">&copy; 2024 SiraFit Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}
