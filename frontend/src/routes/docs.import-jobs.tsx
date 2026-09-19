import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/import-jobs")({
  head: () => ({ meta: [{ title: "Import & capture jobs · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">
          Documentation
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span>Import &amp; capture jobs</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Import &amp; capture jobs</h1>
      <p className="mt-4 text-muted-foreground">
        SiraFit features an enterprise-grade multi-engine ingestion pipeline powered by Scrapling,
        Playwright, and our Plasmo browser extension. Postings are automatically normalized,
        deduplicated, and embedded into PostgreSQL with pgvector.
      </p>
      <h2 className="mt-8 text-lg font-semibold">Ways to import</h2>
      <ul className="mt-4 list-disc list-inside space-y-2.5 text-sm">
        <li>
          <strong>Browser Extension (Plasmo):</strong> 1-click capture from LinkedIn, Indeed,
          Greenhouse, Lever, Ashby, or Workday while browsing job boards.
        </li>
        <li>
          <strong>Direct URL Import:</strong> Paste any job listing link into the import view. Our
          multi-engine scraper automatically selects between HTTP, Camoufox, and Playwright based on
          bot-detection challenges.
        </li>
        <li>
          <strong>Raw Description:</strong> Paste text or job descriptions directly to normalize,
          extract skill taxonomies, and calculate match scores.
        </li>
        <li>
          <strong>Authenticated Session Import:</strong> Provide your LinkedIn or Indeed session
          cookie to discover and import your saved jobs queue asynchronously via Celery.
        </li>
        <li>
          <strong>Batch CSV Import:</strong> Upload a CSV of up to 500 job URLs or IDs for bulk
          processing in the background.
        </li>
      </ul>
      <p className="mt-6 text-sm text-muted-foreground">
        All imported jobs undergo a 3-stage deterministic + fuzzy deduplication check, followed by
        automatic semantic embedding generation via pgvector.
      </p>
    </article>
  ),
});
