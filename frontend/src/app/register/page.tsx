'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({ full_name: '', email: '', password: '', confirmPassword: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setFormData(prev => ({ ...prev, [id]: value }));
    if (errors[id]) {
      setErrors(prev => { const n = { ...prev }; delete n[id]; return n; });
    }
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!formData.full_name.trim()) errs.full_name = 'Full name is required';
    if (!formData.email.trim()) errs.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) errs.email = 'Invalid email format';
    if (!formData.password) errs.password = 'Password is required';
    else if (formData.password.length < 8) errs.password = 'Password must be at least 8 characters';
    if (formData.password !== formData.confirmPassword) errs.confirmPassword = 'Passwords do not match';
    return errs;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) { setErrors(validationErrors); return; }
    setIsLoading(true); setMessage(null);
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: formData.full_name.trim(), email: formData.email.trim().toLowerCase(), password: formData.password }),
      });
      if (response.ok) {
        setMessage({ type: 'success', text: 'Registration successful! Please verify your email.' });
        setFormData({ full_name: '', email: '', password: '', confirmPassword: '' });
        setTimeout(() => router.push('/verify-email'), 2000);
      } else {
        const errorData = await response.json();
        setMessage({ type: 'error', text: errorData.detail || 'Registration failed' });
      }
    } catch { setMessage({ type: 'error', text: 'Network error. Please try again.' }); }
    finally { setIsLoading(false); }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 py-12 relative overflow-hidden min-h-screen">
      {/* Decorative background SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.04]" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
        <defs><pattern id="reg-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#3525cd" strokeWidth="0.5"/></pattern></defs>
        <rect width="100%" height="100%" fill="url(#reg-grid)"/>
        <path d="M0 340C160 290 240 370 400 330L400 400L0 400Z" fill="#3525cd" opacity="0.08"/>
        <circle cx="360" cy="80" r="160" fill="#3525cd" opacity="0.04"/>
        <circle cx="60" cy="340" r="100" fill="#3525cd" opacity="0.05"/>
      </svg>
      <div className="w-full max-w-[420px] flex flex-col items-center gap-8 relative z-10">
        {/* Brand */}
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
              <h1 className="text-xl font-semibold text-text-primary">Create an account</h1>
              <p className="text-sm text-text-secondary">Join SiraFit's high-density workspace</p>
            </div>

            {message && (
              <div className={`p-3 rounded-lg text-sm text-center border ${
                message.type === 'success' ? 'bg-green-50 text-green-600 border-green-200' : 'bg-red-50 text-red-600 border-red-200'
              }`}>
                {message.text}
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="full_name">Full Name</label>
                <input id="full_name" type="text" value={formData.full_name} onChange={handleChange}
                  className={`px-3.5 py-2.5 border ${errors.full_name ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary`}
                  placeholder="Ex. Jane Doe"/>
                {errors.full_name && <p className="text-xs text-red-600 mt-1">{errors.full_name}</p>}
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="reg-email">Email</label>
                <input id="email" type="email" value={formData.email} onChange={handleChange}
                  className={`px-3.5 py-2.5 border ${errors.email ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary`}
                  placeholder="Ex. dev@example.com"/>
                {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email}</p>}
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="reg-password">Password</label>
                <input id="password" type="password" value={formData.password} onChange={handleChange}
                  className={`px-3.5 py-2.5 border ${errors.password ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary`}
                  placeholder="Create a strong password"/>
                {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password}</p>}
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="confirmPassword">Confirm Password</label>
                <input id="confirmPassword" type="password" value={formData.confirmPassword} onChange={handleChange}
                  className={`px-3.5 py-2.5 border ${errors.confirmPassword ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors bg-background-primary`}
                  placeholder="Confirm your password"/>
                {errors.confirmPassword && <p className="text-xs text-red-600 mt-1">{errors.confirmPassword}</p>}
              </div>

              <div className="flex items-start gap-2.5 pt-1">
                <input type="checkbox" id="terms" className="mt-0.5 accent-brand" />
                <label htmlFor="terms" className="text-xs text-text-secondary leading-relaxed">
                  I agree to the Terms of Service and Privacy Policy.
                </label>
              </div>

              <button type="submit" disabled={isLoading}
                className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Creating Account...' : 'Create Account'}
              </button>
            </form>
          </div>

          <div className="border-t border-border px-8 py-5 text-center text-sm text-text-secondary bg-background-primary/50">
            Already have an account?
            <Link href="/login" className="ml-1.5 text-brand font-medium hover:underline">Sign In</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
