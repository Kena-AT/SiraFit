import { createFileRoute } from "@tanstack/react-router";
import { MarketingShell } from "@/components/sirafit/shell";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/help")({
  head: () => ({ meta: [{ title: "Help & docs · SiraFit" }] }),
  component: () => {
    const articles = [
      {
        id: "install-agent",
        title: "Browser extension & local agent",
        description:
          "Capture postings directly on ATS sites with Plasmo or pair the desktop agent.",
        href: "/docs/agent-install",
      },
      {
        id: "gemini-key",
        title: "Connect your AI keys",
        description: "Bring your own key: Gemini, Claude, GPT-4o, Groq, Mistral, or local Ollama.",
        href: "/docs/gemini-key",
      },
      {
        id: "import-jobs",
        title: "Import & capture jobs",
        description: "Scrape via URL, browser extension, saved-jobs session, or batch CSV.",
        href: "/docs/import-jobs",
      },
      {
        id: "resume-profile",
        title: "Master profile & resume variants",
        description:
          "Structured JSON profiles, variant versioning, diff-revert, and PDF/Word export.",
        href: "/docs/resume-profile",
      },
      {
        id: "match-scores",
        title: "Hybrid match scoring",
        description:
          "Deterministic skill overlap, seniority alignment, and pgvector semantic similarity.",
        href: "/docs/match-scores",
      },
      {
        id: "track-applications",
        title: "Application tracking & analytics",
        description:
          "Full lifecycle pipeline, follow-ups, salary benchmarks, and interview preparation.",
        href: "/docs/track-applications",
      },
    ];

    return (
      <MarketingShell>
        <article className="mx-auto max-w-3xl px-6 py-16">
          <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Documentation
          </div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Help &amp; docs</h1>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {articles.map((article) => (
              <Link
                key={article.id}
                to={article.href}
                className="group block rounded-lg bg-card p-4 ring-1 ring-border hover:shadow-md hover:ring-primary/30 transition"
              >
                <div className="text-sm font-semibold">{article.title}</div>
                <p className="mt-1 text-[12px] text-muted-foreground">{article.description}</p>
                <div className="mt-3 inline-flex items-center text-xs font-medium text-primary">
                  Read more
                  <ChevronRight className="ml-1 h-3 w-3" />
                </div>
              </Link>
            ))}
          </div>
        </article>
      </MarketingShell>
    );
  },
});
