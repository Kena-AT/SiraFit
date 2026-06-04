import Link from 'next/link';

export default function LogoutPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 pt-48 bg-background-primary min-h-screen">
      <div className="w-full max-w-[400px] flex flex-col gap-6">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center justify-center gap-1 opacity-70">
          <Link href="/" className="text-xl font-bold text-brand">SiraFit</Link>
        </div>

        {/* Logout Card */}
        <div className="relative bg-background-primary border border-border rounded-lg shadow-sm p-8 flex flex-col items-center text-center overflow-hidden">
          {/* Decorative Top Accent Line */}
          <div className="absolute top-0 left-0 w-full h-[3px] bg-brand"></div>

          <div className="w-12 h-12 rounded-full bg-border-light flex items-center justify-center text-text-secondary mb-4 mt-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinelinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </div>

          <h1 className="text-lg font-semibold text-text-primary mb-1">You have been logged out</h1>
          <p className="text-sm text-text-secondary mb-8">Thank you for using SiraFit. Have a great day.</p>

          <div className="w-full flex flex-col gap-3">
            <Link href="/login" className="w-full bg-brand text-white py-2.5 rounded-md text-sm font-medium hover:opacity-90 transition-opacity inline-flex justify-center">
              Log back in
            </Link>
            <Link href="/" className="w-full text-text-secondary hover:text-text-primary py-2 text-sm font-medium transition-colors">
              Return to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
