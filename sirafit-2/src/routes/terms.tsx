import { createFileRoute } from "@tanstack/react-router";
import { MarketingShell } from "@/components/sirafit/shell";

export const Route = createFileRoute("/terms")({
  head: () => ({ meta: [{ title: "Terms · SiraFit" }] }),
  component: () => (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-6 py-16">
        <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Last updated · 23 Jun 2026</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Terms of service</h1>
        <div className="mt-8 space-y-5 text-sm text-foreground/90">
          <p>By using SiraFit you agree not to automate application submissions, abuse rate limits, or use the platform for recruiter-side workflows.</p>
          <p>SiraFit is provided as-is. Job postings are sourced from third parties; accuracy is best-effort.</p>
        </div>
      </article>
    </MarketingShell>
  ),
});