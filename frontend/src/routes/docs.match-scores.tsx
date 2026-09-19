import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/match-scores")({
  head: () => ({ meta: [{ title: "Hybrid match scores · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">
          Documentation
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span>Hybrid match scores</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Hybrid match scoring</h1>
      <p className="mt-4 text-muted-foreground">
        SiraFit pairs deterministic rule-based evaluation with high-dimensional vector embeddings
        via PostgreSQL pgvector. This ensures transparent, verifiable scoring with deep contextual
        understanding.
      </p>
      <h2 className="mt-8 text-lg font-semibold">The scoring architecture</h2>
      <ul className="mt-4 list-disc list-inside space-y-2 text-sm">
        <li>
          <strong>Skills Overlap (50%):</strong> Hard &amp; soft skill taxonomy mapping against your
          master profile. Distinguishes between required vs. preferred competencies.
        </li>
        <li>
          <strong>Experience &amp; Seniority (30%):</strong> Matches your verified years of
          experience against the role tier (Junior, Mid, Senior, Staff, Lead).
        </li>
        <li>
          <strong>Education &amp; Domain Relevance (20%):</strong> Degree field alignment and domain
          expertise multipliers.
        </li>
        <li>
          <strong>pgvector Semantic Bonus:</strong> Cosine similarity between your profile embedding
          and the job posting requirements surfaces conceptual alignment even when phrasing differs.
        </li>
      </ul>
      <h2 className="mt-8 text-lg font-semibold">Reading the breakdown &amp; Gap-to-Plan</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Click any job card to inspect the match breakdown. SiraFit highlights exact overlapping
        skills, missing keywords, and automatically triggers the Gap-to-Plan engine to give you
        targeted talking points and interview preparation notes.
      </p>
    </article>
  ),
});
