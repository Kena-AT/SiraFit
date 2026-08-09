import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/resume-profile")({
  head: () => ({ meta: [{ title: "Build a resume profile · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">Documentation</Link>
        <ChevronRight className="h-3 w-3" />
        <span>Build a resume profile</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Build a resume profile</h1>
      <p className="mt-4 text-muted-foreground">
        Structured JSON beats PDF editing every time. Your profile defines your
        skills, experience, and education — which the matcher and resume builder
        consume deterministically.
      </p>
      <h2 className="mt-8 text-lg font-semibold">Profile sections</h2>
      <ul className="mt-4 list-disc list-inside space-y-1 text-sm">
        <li><strong>Skills:</strong> Tag-based, auto-suggested as you type.</li>
        <li><strong>Experience:</strong> Role, company, dates, and bullet points.</li>
        <li><strong>Education:</strong> Degrees, institutions, and graduation dates.</li>
      </ul>
      <h2 className="mt-8 text-lg font-semibold">From profile to PDF</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Once your profile is complete, click <strong>Generate Resume</strong> on any
        job page. The engine tailors bullet points by keyword overlap and seniority
        alignment, then exports an ATS-ready PDF.
      </p>
    </article>
  ),
});