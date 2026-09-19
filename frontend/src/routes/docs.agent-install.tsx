import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/agent-install")({
  head: () => ({ meta: [{ title: "Extension & Local Agent · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">
          Documentation
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span>Extension &amp; local agent</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Extension &amp; local agent</h1>
      <p className="mt-4 text-muted-foreground">
        SiraFit gives you two ways to capture job postings directly from the web: our official
        Plasmo-powered browser extension for Chrome and Edge, and a standalone local desktop agent
        with background worker support.
      </p>

      <h2 className="mt-8 text-lg font-semibold">1. Plasmo browser extension (Recommended)</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        The browser extension runs directly on any job portal (LinkedIn, Indeed, Greenhouse, Lever,
        Ashby, Workday) and allows 1-click capture into your SiraFit pipeline.
      </p>
      <ol className="mt-4 list-decimal list-inside space-y-2 text-sm">
        <li>
          Install the extension from the Chrome Web Store or load unpacked from{" "}
          <code>frontend/extension</code>.
        </li>
        <li>Click the SiraFit extension icon in your browser toolbar to authenticate.</li>
        <li>
          Browse to any job listing and click <strong>Capture Job</strong>.
        </li>
        <li>The job posting is normalized, scored, and immediately available on your dashboard.</li>
      </ol>

      <h2 className="mt-8 text-lg font-semibold">2. Standalone desktop agent</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        For scheduled background polling, authenticated session scraping, and local LLM execution
        with zero network egress.
      </p>
      <ol className="mt-4 list-decimal list-inside space-y-2 text-sm">
        <li>
          Navigate to <strong>Settings → AI &amp; Agent</strong> in the web app.
        </li>
        <li>Download the SiraFit agent package for your platform (macOS, Windows, Linux).</li>
        <li>Launch the agent and copy the secure pairing token into your dashboard.</li>
        <li>Once paired, the agent handles Playwright and Scrapling scraping locally.</li>
      </ol>
    </article>
  ),
});
