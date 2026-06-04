import Link from 'next/link';

export default function ForgotPasswordPage() {
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

          {/* Form Section */}
          <div className="p-8 pb-6">
            <form className="flex flex-col gap-6">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary" htmlFor="email">Email</label>
                <input 
                  id="email"
                  type="email" 
                  className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
                  placeholder="Ex. dev@example.com"
                />
              </div>

              <button type="submit" className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity">
                Send Reset Link
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
