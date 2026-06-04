import Link from 'next/link';

export default function ResetPasswordPage() {
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

          <form className="flex flex-col gap-6">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-text-primary" htmlFor="password">New Password</label>
              <input 
                id="password"
                type="password" 
                className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
                placeholder="Enter new password"
              />
            </div>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-text-primary" htmlFor="confirm-password">Confirm New Password</label>
              <input 
                id="confirm-password"
                type="password" 
                className="px-3 py-2 border border-border rounded-md text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
                placeholder="Confirm new password"
              />
            </div>

            <button type="submit" className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity mt-2">
              Reset Password
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-text-secondary">
          Enter your new password above to secure your account.
        </div>
      </div>
    </div>
  );
}
