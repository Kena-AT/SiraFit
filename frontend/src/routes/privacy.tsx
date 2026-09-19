import { createFileRoute } from "@tanstack/react-router";
import { MarketingShell } from "@/components/sirafit/shell";

export const Route = createFileRoute("/privacy")({
  head: () => ({ meta: [{ title: "Privacy · SiraFit" }] }),
  component: () => (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-6 py-16">
        <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Last updated · September 2026
        </div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Privacy policy</h1>
        <div className="mt-8 space-y-5 text-sm text-foreground/90">
          <p>
            SiraFit is built local-first and privacy-conscious. Sensitive operations like job
            scraping, AI-assisted tailoring, and resume rendering run securely on your machine or
            private deployment.
          </p>
          <h2 className="text-lg font-semibold">What we store</h2>
          <p>
            Normalized job projections, application pipeline metadata, and structured resume
            variants necessary to power your dashboard. Raw scraped HTML is not stored beyond a
            30–90 day deduplication window.
          </p>
          <h2 className="text-lg font-semibold">API keys &amp; AI providers</h2>
          <p>
            Your AI API keys (Google Gemini, Anthropic Claude, OpenAI, Groq, Mistral, OpenRouter)
            are encrypted at rest with AES-GCM or stored strictly in your local environment. They
            are never transmitted to third parties or used to train models.
          </p>
          <h2 className="text-lg font-semibold">Your rights</h2>
          <p>Export or delete your data at any time from Settings · Data &amp; Privacy.</p>
        </div>
      </article>
    </MarketingShell>
  ),
});
