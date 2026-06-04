import Link from 'next/link';

export default function RegisterPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 py-12 bg-background-primary">
      <div className="w-full max-w-[420px] bg-background-secondary border border-border rounded-lg shadow-sm flex flex-col pt-8">
        
        {/* Header */}
        <div className="flex flex-col gap-2 items-center text-center px-8 mb-6">
          <Link href="/" className="text-2xl font-bold text-brand mb-2">SiraFit</Link>
          <h1 className="text-xl font-semibold text-text-primary">Create an account</h1>
          <p className="text-sm text-text-secondary">Join SiraFit's high-density workspace</p>
        </div>

        {/* Form */}
        <div className="px-8 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary" htmlFor="name">Full Name</label>
            <input 
              id="name"
              type="text" 
              className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
              placeholder="Ex. Jane Doe"
            />
          </div>

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
            <label className="text-sm font-medium text-text-primary" htmlFor="password">Password</label>
            <input 
              id="password"
              type="password" 
              className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
              placeholder="Create a strong password"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary" htmlFor="confirm-password">Confirm Password</label>
            <input 
              id="confirm-password"
              type="password" 
              className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
              placeholder="Confirm your password"
            />
          </div>

          <div className="flex items-start gap-2 py-2">
            <input type="checkbox" id="terms" className="mt-1" />
            <label htmlFor="terms" className="text-xs text-text-secondary leading-tight">
              I agree to the Terms of Service and Privacy Policy.
            </label>
          </div>

          <button className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity mb-8">
            Create Account
          </button>
        </div>

        {/* Footer */}
        <div className="border-t border-border px-8 py-6 text-center text-sm text-text-secondary bg-background-secondary rounded-b-lg">
          Already have an account? 
          <Link href="/login" className="ml-1 text-brand font-medium hover:underline">Sign In</Link>
        </div>
      </div>
    </div>
  );
}
