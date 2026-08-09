import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/track-applications")({
  head: () => ({ meta: [{ title: "Track applications · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">Documentation</Link>
        <ChevronRight className="h-3 w-3" />
        <span>Track applications</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Track applications</h1>
      <p className="mt-4 text-muted-foreground">
        Move cards through your pipeline. Each application starts in <em>Saved</em>
        and progresses as you take action.
      </p>
      <h2 className="mt-8 text-lg font-semibold">Pipeline stages</h2>
      <table className="mt-4 w-full table-auto text-sm">
        <thead>
          <tr className="border-b border-border text-left">
            <th className="pb-2">Stage</th>
            <th className="pb-2">When to use</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          <tr>
            <td className="py-2 font-medium">Saved</td>
            <td>Auto-applied when you click <strong>Save</strong> on a job card.</td>
          </tr>
          <tr>
            <td className="py-2 font-medium">Applied</td>
            <td>Manually move when you submit your resume.</td>
          </tr>
          <tr>
            <td className="py-2 font-medium">Interview</td>
            <td>Update when you get a response — scheduling, onsite, etc.</td>
          </tr>
          <tr>
            <td className="py-2 font-medium">Offer</td>
            <td>Final stage. Add compensation details for reference.</td>
          </tr>
        </tbody>
      </table>
      <h2 className="mt-8 text-lg font-semibold">Follow-ups</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Missed a stage update? The agent can auto-schedule follow-up reminders on
        your timeline so nothing falls through the cracks.
      </p>
    </article>
  ),
});