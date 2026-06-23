import Link from 'next/link';

export default function LandingPage() {
  return (
    <main className="flex-1 flex flex-col">
      {/* TopNavBar */}
      <header className="fixed top-0 w-full h-14 bg-background-primary border-b border-border flex items-center justify-between px-4 md:px-8 z-50">
        <div className="flex items-center gap-2.5">
          <svg viewBox="0 0 18 18" width="20" height="20" fill="#3525cd">
            <path d="M10 6l0-6 8 0 0 6-8 0 0 0m-10 4l0-10 8 0 0 10-8 0 0 0m10 8l0-10 8 0 0 10-8 0 0 0m-10 0l0-6 8 0 0 6-8 0 0 0"/>
          </svg>
          <span className="font-bold text-xl text-brand">SiraFit</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-text-secondary hover:text-text-primary text-sm font-medium transition-colors">Log in</Link>
          <Link href="/register" className="bg-brand text-white px-5 py-2 rounded-md text-sm font-medium hover:opacity-90 transition-opacity">Sign up</Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="flex flex-col md:flex-row items-center gap-12 px-4 md:px-12 pt-28 pb-20 max-w-7xl mx-auto w-full relative">
        {/* Decorative background */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.03]" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
          <defs><pattern id="hero-grid" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M 50 0 L 0 0 0 50" fill="none" stroke="#3525cd" strokeWidth="0.5"/></pattern></defs>
          <rect width="100%" height="100%" fill="url(#hero-grid)"/>
          <circle cx="80" cy="100" r="180" fill="#3525cd" opacity="0.06"/>
          <circle cx="350" cy="300" r="140" fill="#3525cd" opacity="0.04"/>
        </svg>

        {/* Left Column - Text */}
        <div className="flex-1 flex flex-col gap-6 relative z-10">
          {/* System Online Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-sm bg-background-muted border border-border w-fit">
            <div className="w-2 h-2 rounded-full bg-brand"/>
            <span className="text-xs font-semibold text-brand uppercase tracking-wider">System Online v</span>
          </div>

          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text-primary leading-[1.1] tracking-tight">
            Your Job Search,<br/>
            <span className="text-brand">Automated.</span>
          </h1>

          <p className="text-text-secondary text-base md:text-lg max-w-lg leading-relaxed">
            The operational command center for high-volume job management and AI-powered resume tailoring. Built for high-throughput candidates.
          </p>

          <div className="flex items-center gap-4 pt-2">
            <Link href="/register"
              className="inline-flex items-center gap-2 bg-brand text-white px-6 py-3 rounded-md text-sm font-medium hover:opacity-90 transition-opacity"
            >
              Get Started
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M4.65 8.65L4 8l2.48-2.48H0v-.92h6.48L4 2.12l.65-.65L8.5 5.12 4.65 8.65z" fill="white"/>
              </svg>
            </Link>
            <Link href="/login"
              className="inline-flex items-center gap-2 bg-background-primary text-text-primary px-6 py-3 rounded-md text-sm font-medium border border-border hover:bg-background-muted transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 2.5l8 4.5-8 4.5v-9z" fill="#1b1b24"/>
              </svg>
              View Demo
            </Link>
          </div>
        </div>

        {/* Right Column - Abstract Dashboard Visualization */}
        <div className="flex-1 w-full max-w-lg relative z-10">
          <div className="bg-background-secondary border border-border rounded-lg shadow-sm p-5 relative overflow-hidden">
            {/* Faux App Header */}
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-border-light"/>
                <div className="w-3 h-3 rounded-full bg-border-light"/>
                <div className="w-3 h-3 rounded-full bg-border-light"/>
              </div>
              <div className="px-3 py-1 rounded bg-background-muted">
                <span className="text-xs font-mono text-text-secondary">sira-fit-terminal ~ zsh</span>
              </div>
            </div>

            {/* Faux Data Rows */}
            <div className="space-y-2">
              <div className="h-8 flex items-center px-3 bg-background-muted/60 rounded border border-border/40 gap-3">
                <div className="w-4 h-4 rounded bg-brand/5"/>
                <div className="h-2 w-[140px] rounded bg-text-secondary/5"/>
                <div className="h-2 w-[80px] rounded bg-text-secondary/5 ml-auto"/>
              </div>
              <div className="h-8 flex items-center px-3 bg-background-muted/60 rounded border border-brand/10 gap-3 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-brand"/>
                <div className="w-4 h-4 rounded bg-brand flex items-center justify-center">
                  <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                    <path d="M2.85 6.0125l-2.85-2.85 0.7125-0.7125 2.1375 2.1375 4.5875-4.5875 0.7125 0.7125-5.3 5.3z" fill="white"/>
                  </svg>
                </div>
                <div className="h-2 w-[180px] rounded bg-text-primary/15"/>
                <div className="h-2 w-[100px] rounded bg-brand/15 ml-auto"/>
              </div>
              <div className="h-8 flex items-center px-3 bg-background-muted/40 rounded border border-border/40 gap-3 opacity-60">
                <div className="w-4 h-4 rounded bg-brand/5"/>
                <div className="h-2 w-[110px] rounded bg-text-secondary/5"/>
                <div className="h-2 w-[60px] rounded bg-text-secondary/5 ml-auto"/>
              </div>
              <div className="h-8 flex items-center px-3 bg-background-muted/30 rounded border border-border/40 gap-3 opacity-40">
                <div className="w-4 h-4 rounded bg-brand/5"/>
                <div className="h-2 w-[220px] rounded bg-text-secondary/5"/>
                <div className="h-2 w-[50px] rounded bg-text-secondary/5 ml-auto"/>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Wave */}
      <div className="relative">
        <svg viewBox="0 0 1440 120" className="w-full h-24 -mb-1" preserveAspectRatio="none">
          <path fill="#fcf8ff" d="M0,64L60,74.7C120,85,240,107,360,106.7C480,107,600,85,720,80C840,75,960,85,1080,90.7C1200,96,1320,96,1380,96L1440,96L1440,120L1380,120C1320,120,1200,120,1080,120C960,120,840,120,720,120C600,120,480,120,360,120C240,120,120,120,60,120L0,120Z"/>
        </svg>
      </div>

      {/* Footer */}
      <footer className="w-full bg-background-primary border-t border-border py-8 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <svg viewBox="0 0 18 18" width="18" height="18" fill="#1b1b24">
              <path d="M10 6l0-6 8 0 0 6-8 0 0 0m-10 4l0-10 8 0 0 10-8 0 0 0m10 8l0-10 8 0 0 10-8 0 0 0m-10 0l0-6 8 0 0 6-8 0 0 0"/>
            </svg>
            <span className="text-sm font-bold text-text-primary">SiraFit</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-text-secondary">
            <Link href="#" className="hover:text-text-primary transition-colors">Legal</Link>
            <Link href="#" className="hover:text-text-primary transition-colors">Privacy</Link>
            <Link href="#" className="hover:text-text-primary transition-colors">Product</Link>
            <Link href="#" className="hover:text-text-primary transition-colors">Twitter</Link>
            <Link href="#" className="hover:text-text-primary transition-colors">GitHub</Link>
          </div>
          <p className="text-xs text-text-muted">&copy; 2024 SiraFit. High-density automation.</p>
        </div>
      </footer>
    </main>
  );
}
