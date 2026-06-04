import Link from 'next/link';

export default function VerifyEmailPage() {
  return (
    <div className="flex-1 flex flex-col min-h-screen bg-background-primary justify-between">
      {/* Transactional Top NavBar */}
      <header className="w-full h-14 bg-background-primary border-b border-border flex items-center px-4">
        <Link href="/" className="font-bold text-xl text-brand">SiraFit</Link>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-[480px] bg-background-secondary border border-border rounded-lg shadow-sm p-8 flex flex-col items-center gap-6">
          
          <div className="w-16 h-16 bg-brand-light rounded-full flex items-center justify-center text-brand mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinelinejoin="round">
              <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"></path>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
              <path d="m16 19 2 2 4-4"></path>
            </svg>
          </div>

          <div className="text-center flex flex-col gap-2">
            <h1 className="text-2xl font-bold text-text-primary">Verify your email</h1>
            <p className="text-sm text-text-secondary">
              We've sent a verification link to your email address. Please click the link to activate your account.
            </p>
          </div>

          <div className="w-full h-[1px] bg-border-light my-2"></div>

          <div className="w-full flex flex-col gap-3">
            <button className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity">
              Resend verification email
            </button>
            <Link href="/login" className="w-full text-center text-text-secondary hover:text-text-primary py-2.5 text-sm font-medium transition-colors">
              Back to Sign In
            </Link>
          </div>
        </div>
      </main>

      {/* Transactional Footer */}
      <footer className="w-full bg-background-primary border-t border-border py-8 px-4 flex justify-center">
        <p className="text-xs text-text-muted">© 2024 SiraFit Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}
