import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/import-jobs")({
  head: () => ({ meta: [{ title: "Import your first jobs · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">Documentation</Link>
        <ChevronRight className="h-3 w-3" />
        <span>Import your first jobs</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Import your first jobs</h1>
      <p className="mt-4 text-muted-foreground">
        Paste a URL or watch the agent scrape Lever, Greenhouse, and Ashby
        postings automatically.
      </p>
      <h2 className="mt-8 text-lg font-semibold">Ways to import</h2>
      <ul className="mt-4 list-disc list-inside space-y-2 text-sm">
        <li><strong>Paste a URL:</strong> From any ATS listing page, paste the job URL into the import dialog.</li>
        <li><strong>Watch the agent:</strong> Point the local agent at a listing page and it will auto-detect and import new roles.</li>
        <li><strong>Bulk import:</strong> Drag-and-drop a CSV or paste multiple URLs at once.</li>
      </ul>
      <p className="mt-6 text-sm text-muted-foreground">
        All imported jobs pass through the 3-stage dedupe pipeline before landing
        in your dashboard.
      </p>
    </article>
  ),
});