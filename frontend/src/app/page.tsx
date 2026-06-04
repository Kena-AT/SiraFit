import Link from 'next/link';

export default function LandingPage() {
  return (
    <main className="flex-1 flex flex-col pt-14">
      {/* TopNavBar */}
      <header className="fixed top-0 w-full h-14 bg-background-primary border-b border-border flex items-center justify-between px-4 z-50">
        <div className="font-bold text-xl text-brand">SiraFit</div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-text-secondary hover:text-text-primary text-sm font-medium">Log in</Link>
          <Link href="/register" className="bg-brand text-white px-4 py-2 rounded-md text-sm font-medium hover:opacity-90">Sign up</Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="flex flex-col items-center text-center px-4 py-20 gap-8">
        <h1 className="text-4xl md:text-5xl font-bold max-w-3xl leading-tight">
          Automate your job search with deterministic precision
        </h1>
        <p className="text-text-secondary text-lg max-w-2xl">
          SiraFit is your local-first career operations automated layer. Score jobs, generate tailored resumes, and track your applications.
        </p>
        <Link href="/register" className="bg-brand text-white px-6 py-3 rounded-md text-base font-medium hover:opacity-90">
          Get Started for Free
        </Link>
      </section>
    </main>
  );
}
