import { createFileRoute, Link } from "@tanstack/react-router";
import { MarketingShell } from "@/components/sirafit/shell";
import { AgentDot, ScorePill, StatusPill, Tag } from "@/components/sirafit/bits";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "SiraFit — Deterministic career operations for engineers" },
      { name: "description", content: "SiraFit ingests jobs from ATS sources, scores them deterministically, and tailors structured resumes — locally, with your own AI key." },
      { property: "og:title", content: "SiraFit — Deterministic career operations for engineers" },
      { property: "og:description", content: "Local-first ATS scraping, deterministic match scoring, and structured resume tailoring." },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <MarketingShell>
      <section className="border-b border-border">
        <div className="mx-auto max-w-5xl px-6 py-20 text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-card px-3 py-1 text-[11px] font-medium text-muted-foreground ring-1 ring-border">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--brand)]" />
            v0.8.2 · Local agent in private beta
          </div>
          <h1 className="mt-6 text-balance text-4xl font-semibold tracking-tight md:text-5xl">
            Career operations for engineers who actually&nbsp;ship.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-pretty text-base text-muted-foreground md:text-lg">
            SiraFit ingests jobs from Lever, Greenhouse, and Ashby, scores them deterministically, and tailors structured resumes — all from a local agent you control, with your own Gemini key.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link to="/dashboard" className="rounded-md bg-foreground px-4 py-2.5 text-sm font-medium text-background ring-1 ring-foreground transition-colors hover:bg-foreground/90">Launch the dashboard</Link>
            <Link to="/register" className="rounded-md bg-card px-4 py-2.5 text-sm font-medium text-foreground ring-1 ring-border transition-colors hover:bg-muted">Create an account</Link>
          </div>
          <div className="mt-10 grid grid-cols-2 gap-3 md:grid-cols-4">
            {[["842","Jobs ingested / day"],["12","ATS sources polled"],["~3.6%","Sector interview rate"],["8.4%","SiraFit user median"]].map(([v,l]) => (
              <div key={l} className="rounded-md bg-card p-4 ring-1 ring-border">
                <div className="font-mono text-xl font-semibold tabular-nums">{v}</div>
                <div className="text-[11px] text-muted-foreground">{l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="pipeline" className="border-b border-border bg-muted/20">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="mb-10 max-w-2xl">
            <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">The pipeline</div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight md:text-3xl">Scrape · Normalize · Score · Tailor · Track.</h2>
            <p className="mt-2 text-sm text-muted-foreground">Every job that enters SiraFit follows the same deterministic pipeline. AI generates content. AI does not decide outcomes.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-5">
            {[{t:"Scrape",d:"Playwright pulls postings from Lever, Greenhouse, Ashby."},{t:"Normalize",d:"Unified schema across ATS sources."},{t:"Dedupe",d:"3-stage deterministic + fuzzy matching."},{t:"Score",d:"Rule-based skill + seniority + domain match."},{t:"Tailor",d:"Structured resume JSON → ATS-ready PDF."}].map((c,i) => (
              <div key={c.t} className="rounded-lg bg-card p-5 ring-1 ring-border">
                <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Step {String(i+1).padStart(2,"0")}</div>
                <div className="mt-2 text-sm font-semibold">{c.t}</div>
                <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">{c.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="intelligence" className="border-b border-border">
        <div className="mx-auto grid max-w-7xl gap-8 px-6 py-16 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Glanceable intelligence</div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight md:text-3xl">Every job, scored. Every application, tracked.</h2>
            <p className="mt-2 text-sm text-muted-foreground">No more guessing whether to apply. Deterministic match scores cite which skills overlapped and which gaps cost you points. Your call — better informed.</p>
            <div className="mt-6 flex flex-wrap gap-2">{["Greenhouse","Lever","Ashby","Workday","Gemini","Local-first"].map((t) => (<Tag key={t}>{t}</Tag>))}</div>
          </div>
          <div className="overflow-hidden rounded-lg bg-card ring-1 ring-border lg:col-span-3">
            <div className="border-b border-border bg-muted/30 px-4 py-2 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Top match queue</div>
            <table className="w-full text-left text-sm">
              <tbody className="divide-y divide-border">
                {[["Stripe","Software Engineer, Infrastructure",94,"new"],["Linear","Junior Fullstack Developer",89,"new"],["Anthropic","Backend Systems Engineer",91,"saved"],["Vercel","Frontend Engineer",72,"seen"]].map(([c,r,m,s]) => (
                  <tr key={c as string} className="hover:bg-muted/40">
                    <td className="px-4 py-2.5 font-medium">{c}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{r}</td>
                    <td className="px-4 py-2.5"><ScorePill value={m as number} /></td>
                    <td className="px-4 py-2.5 text-right"><StatusPill status={s as string} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="border-b border-border bg-muted/20">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-12">
          <div>
            <div className="text-lg font-semibold tracking-tight">Ready to operate?</div>
            <p className="text-sm text-muted-foreground">The dashboard is a click away. Set up the local agent when you're ready.</p>
          </div>
          <div className="flex items-center gap-3">
            <AgentDot />
            <Link to="/dashboard" className="rounded-md bg-foreground px-4 py-2.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">Open dashboard</Link>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}