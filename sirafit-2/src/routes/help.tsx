import { createFileRoute } from "@tanstack/react-router";
import { MarketingShell } from "@/components/sirafit/shell";

export const Route = createFileRoute("/help")({
  head: () => ({ meta: [{ title: "Help & docs · SiraFit" }] }),
  component: () => (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-6 py-16">
        <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Documentation</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Help &amp; docs</h1>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {[["Install the local agent","Download the desktop agent and connect it to your account."],["Connect your Gemini key","Bring your own key. Stored locally only."],["Import your first jobs","Paste a URL or watch the agent scrape Lever, Greenhouse, Ashby."],["Build a resume profile","Structured JSON beats PDF editing every time."],["Understand match scores","Skill overlap, seniority alignment, domain relevance — explained."],["Track applications","Move cards through Saved → Applied → Interview → Offer."]].map(([t,d]) => (
            <div key={t} className="rounded-lg bg-card p-4 ring-1 ring-border">
              <div className="text-sm font-semibold">{t}</div>
              <p className="mt-1 text-[12px] text-muted-foreground">{d}</p>
            </div>
          ))}
        </div>
      </article>
    </MarketingShell>
  ),
});