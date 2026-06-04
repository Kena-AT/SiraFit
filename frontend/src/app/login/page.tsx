import Link from 'next/link';

export default function LoginPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 bg-background-primary">
      <div className="w-full max-w-[448px] flex flex-col gap-8">
        
        {/* Brand Header */}
        <div className="flex flex-col gap-1 items-center text-center">
          <Link href="/" className="text-2xl font-bold text-brand mb-2">SiraFit</Link>
          <h1 className="text-xl font-semibold text-text-primary">Welcome back</h1>
          <p className="text-sm text-text-secondary">Log in to your high-density workspace</p>
        </div>

        {/* Auth Card */}
        <div className="bg-background-secondary border border-border-light rounded-lg p-8 shadow-sm flex flex-col gap-6">
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
            
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-text-primary" htmlFor="password">Password</label>
                <Link href="/forgot-password" className="text-xs text-brand hover:underline">Forgot password?</Link>
              </div>
              <input 
                id="password"
                type="password" 
                className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
                placeholder="Enter your password"
              />
            </div>

            <button type="submit" className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity">
              Sign In
            </button>
          </form>
          
          <div className="flex justify-center text-sm text-text-secondary mt-2">
            <span>Don't have an account? </span>
            <Link href="/register" className="ml-1 text-brand font-medium hover:underline">Create an account</Link>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-text-muted">
          © 2024 SiraFit. High-density automation.
        </div>
      </div>
    </div>
  );
}
