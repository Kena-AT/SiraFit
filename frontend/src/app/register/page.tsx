'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setFormData(prev => ({ ...prev, [id]: value }));
    // Clear error when user types
    if (errors[id]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[id];
        return newErrors;
      });
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Full name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    return newErrors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: formData.full_name.trim(),
          email: formData.email.trim().toLowerCase(),
          password: formData.password,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Registration successful! Please verify your email.' });
        
        // Clear form
        setFormData({
          full_name: '',
          email: '',
          password: '',
          confirmPassword: '',
        });
        
        setTimeout(() => {
          router.push('/verify-email');
        }, 2000);
      } else {
        const errorData = await response.json();
        setMessage({ type: 'error', text: errorData.detail || 'Registration failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 py-12 bg-background-primary">
      <div className="w-full max-w-[420px] bg-background-secondary border border-border rounded-lg shadow-sm flex flex-col pt-8">
        
        {/* Header */}
        <div className="flex flex-col gap-2 items-center text-center px-8 mb-6">
          <Link href="/" className="text-2xl font-bold text-brand mb-2">SiraFit</Link>
          <h1 className="text-xl font-semibold text-text-primary">Create an account</h1>
          <p className="text-sm text-text-secondary">Join SiraFit's high-density workspace</p>
        </div>

        {/* Error/Success Message */}
        {message && (
          <div className={`mx-8 mb-6 p-4 rounded-lg text-sm text-center ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-600 border border-green-200' 
              : 'bg-red-50 text-red-600 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-8 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary" htmlFor="full_name">Full Name</label>
            <input 
              id="full_name"
              type="text" 
              value={formData.full_name}
              onChange={handleChange}
              className={`px-3 py-2 border ${errors.full_name ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand`}
              placeholder="Ex. Jane Doe"
            />
            {errors.full_name && <p className="text-xs text-red-600 mt-1">{errors.full_name}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary" htmlFor="email">Email</label>
            <input 
              id="email"
              type="email" 
              value={formData.email}
              onChange={handleChange}
              className={`px-3 py-2 border ${errors.email ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand`}
              placeholder="Ex. dev@example.com"
            />
            {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email}</p>}
          </div>
          
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary" htmlFor="password">Password</label>
            <input 
              id="password"
              type="password" 
              value={formData.password}
              onChange={handleChange}
              className={`px-3 py-2 border ${errors.password ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand`}
              placeholder="Create a strong password"
            />
            {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password}</p>}
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary" htmlFor="confirmPassword">Confirm Password</label>
            <input 
              id="confirmPassword"
              type="password" 
              value={formData.confirmPassword}
              onChange={handleChange}
              className={`px-3 py-2 border ${errors.confirmPassword ? 'border-red-500' : 'border-border'} rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand`}
              placeholder="Confirm your password"
            />
            {errors.confirmPassword && <p className="text-xs text-red-600 mt-1">{errors.confirmPassword}</p>}
          </div>

          <div className="flex items-start gap-2 py-2">
            <input type="checkbox" id="terms" className="mt-1" />
            <label htmlFor="terms" className="text-xs text-text-secondary leading-tight">
              I agree to the Terms of Service and Privacy Policy.
            </label>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity mb-8 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        {/* Footer */}
        <div className="border-t border-border px-8 py-6 text-center text-sm text-text-secondary bg-background-secondary rounded-b-lg">
          Already have an account? 
          <Link href="/login" className="ml-1 text-brand font-medium hover:underline">Sign In</Link>
        </div>
      </div>
    </div>
  );
}