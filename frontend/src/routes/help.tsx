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
        title: "Install the local agent",
        description: "Download the desktop agent and connect it to your account.",
        href: "/docs/agent-install",
      },
      {
        id: "gemini-key",
        title: "Connect your Gemini key",
        description: "Bring your own key. Stored locally only.",
        href: "/docs/gemini-key",
      },
      {
        id: "import-jobs",
        title: "Import your first jobs",
        description: "Paste a URL or watch the agent scrape Lever, Greenhouse, Ashby.",
        href: "/docs/import-jobs",
      },
      {
        id: "resume-profile",
        title: "Build a resume profile",
        description: "Structured JSON beats PDF editing every time.",
        href: "/docs/resume-profile",
      },
      {
        id: "match-scores",
        title: "Understand match scores",
        description: "Skill overlap, seniority alignment, domain relevance - explained.",
        href: "/docs/match-scores",
      },
      {
        id: "track-applications",
        title: "Track applications",
        description: "Move cards through Saved → Applied → Interview → Offer.",
        href: "/docs/track-applications",
      },
    ];

    return (
      <MarketingShell>
        <article className="mx-auto max-w-3xl px-6 py-16">
          <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Documentation
          </div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            Help &amp; docs
          </h1>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {articles.map((article) => (
              <Link
                key={article.id}
                to={article.href}
                className="group block rounded-lg bg-card p-4 ring-1 ring-border hover:shadow-md hover:ring-primary/30 transition"
              >
                <div className="text-sm font-semibold">{article.title}</div>
                <p className="mt-1 text-[12px] text-muted-foreground">
                  {article.description}
                </p>
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
