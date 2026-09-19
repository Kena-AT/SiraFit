import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/track-applications")({
  head: () => ({ meta: [{ title: "Application tracking & analytics · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">
          Documentation
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span>Track applications</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">
        Application tracking &amp; analytics
      </h1>
      <p className="mt-4 text-muted-foreground">
        Move cards through your end-to-end career pipeline with drag-and-drop or status transitions.
        SiraFit tracks response rates, flags stalled applications, and sends real-time updates via
        WebSockets and Server-Sent Events.
      </p>
      <h2 className="mt-8 text-lg font-semibold">Pipeline lifecycle stages</h2>
      <table className="mt-4 w-full table-auto text-sm">
        <thead>
          <tr className="border-b border-border text-left">
            <th className="pb-2">Stage</th>
            <th className="pb-2">Description &amp; Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          <tr>
            <td className="py-2 font-medium">Saved</td>
            <td>Bookmarked from job scraping or extension import.</td>
          </tr>
          <tr>
            <td className="py-2 font-medium">Preparing</td>
            <td>Tailoring resume variant and drafting AI-aligned cover letter.</td>
          </tr>
          <tr>
            <td className="py-2 font-medium">Applied</td>
            <td>Application submitted. Follow-up timer automatically armed.</td>
          </tr>
          <tr>
            <td className="py-2 font-medium">Screening / Interview</td>
            <td>Recruiter or technical screens. Interview Prep Plan activated.</td>
          </tr>
          <tr>
            <td className="py-2 font-medium">Final Round</td>
            <td>Onsite or leadership presentations.</td>
          </tr>
          <tr>
            <td className="py-2 font-medium">Offer</td>
            <td>Final offer received. Compare compensation against market benchmarks.</td>
          </tr>
        </tbody>
      </table>
      <h2 className="mt-8 text-lg font-semibold">Analytics &amp; Follow-ups</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Stay proactive with automated follow-up reminders, salary benchmark distributions, market
        skill demand curves, and one-click Excel (.xlsx) export of your entire pipeline.
      </p>
    </article>
  ),
});
