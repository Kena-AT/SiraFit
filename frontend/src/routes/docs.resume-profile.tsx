import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/resume-profile")({
  head: () => ({ meta: [{ title: "Master profile & variants · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">
          Documentation
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span>Master profile &amp; variants</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">
        Master profile &amp; resume variants
      </h1>
      <p className="mt-4 text-muted-foreground">
        Structured JSON beats manual PDF editing every time. Your master profile defines your
        skills, work experience, projects, and education. Every change is tracked with immutable
        version snapshots and rollback support.
      </p>
      <h2 className="mt-8 text-lg font-semibold">Profile architecture</h2>
      <ul className="mt-4 list-disc list-inside space-y-1.5 text-sm">
        <li>
          <strong>Canonical Skill Taxonomy:</strong> Standardized skill identification with
          auto-suggestions and alias normalization.
        </li>
        <li>
          <strong>Work Experience &amp; Projects:</strong> Measurable bullet points, tech stack
          tags, and quantifiable accomplishments.
        </li>
        <li>
          <strong>Version History:</strong> Every profile edit creates a snapshot so you can revert
          to any historical state with a single click.
        </li>
      </ul>
      <h2 className="mt-8 text-lg font-semibold">Job-specific resume variants &amp; visual diff</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Generate tailored variants for specific job postings. Use our side-by-side visual diff
        viewer to compare tailored bullet points against your master profile, accept or reject AI
        modifications, and export cleanly formatted documents to either ATS-ready PDF or Microsoft
        Word (.docx).
      </p>
    </article>
  ),
});
