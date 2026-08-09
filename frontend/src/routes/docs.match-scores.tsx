import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/match-scores")({
  head: () => ({ meta: [{ title: "Understand match scores · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">Documentation</Link>
        <ChevronRight className="h-3 w-3" />
        <span>Understand match scores</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Understand match scores</h1>
      <p className="mt-4 text-muted-foreground">
        Every job is scored with a deterministic algorithm — no black-box AI
        decides outcomes. Scores combine three weighted dimensions.
      </p>
      <h2 className="mt-8 text-lg font-semibold">The formula</h2>
      <ul className="mt-4 list-disc list-inside space-y-1 text-sm">
        <li><strong>Skills (50%):</strong> Keyword overlap between your profile and the job's required tags.</li>
        <li><strong>Experience (30%):</strong> Years of experience relative to the role's seniority tier.</li>
        <li><strong>Education (20%):</strong> Highest degree level mapped to a point multiplier.</li>
      </ul>
      <h2 className="mt-8 text-lg font-semibold">Reading the breakdown</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Hover any job card to see the score breakdown. A score of 30+ is the
        application threshold — jobs below that typically lack the minimum skill
        overlap for a competitive application.
      </p>
    </article>
  ),
});