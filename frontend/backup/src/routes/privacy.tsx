import { createFileRoute } from "@tanstack/react-router";
import { MarketingShell } from "@/components/sirafit/shell";

export const Route = createFileRoute("/privacy")({
  head: () => ({ meta: [{ title: "Privacy · SiraFit" }] }),
  component: () => (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-6 py-16">
        <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Last updated · 23 Jun 2026</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Privacy policy</h1>
        <div className="mt-8 space-y-5 text-sm text-foreground/90">
          <p>SiraFit is built local-first. Sensitive operations like scraping, AI execution, and resume rendering happen on your machine.</p>
          <h2 className="text-lg font-semibold">What we store in the cloud</h2>
          <p>Normalized job projections, application metadata, and resume JSON necessary to power your dashboard. No raw HTML is stored beyond a 30–90 day window.</p>
          <h2 className="text-lg font-semibold">API keys</h2>
          <p>Your Gemini API key is stored locally only. It is never transmitted to SiraFit servers.</p>
          <h2 className="text-lg font-semibold">Your rights</h2>
          <p>Export or delete your data at any time from Settings · Data &amp; Privacy.</p>
        </div>
      </article>
    </MarketingShell>
  ),
});