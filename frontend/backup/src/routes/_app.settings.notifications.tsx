import { createFileRoute } from "@tanstack/react-router";
import { Panel } from "@/components/sirafit/bits";

const rows = [
  ["Resume generation complete", true, true],
  ["High-match job ingested (>85%)", true, false],
  ["Interview scheduled / updated", true, true],
  ["Recruiter follow-up reminders", true, true],
  ["Scraper rate-limit warnings", false, false],
  ["Sync failure (degraded mode)", true, false],
] as const;

export const Route = createFileRoute("/_app/settings/notifications")({
  head: () => ({ meta: [{ title: "Notification settings · SiraFit" }] }),
  component: () => (
    <Panel title="Channels">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-border bg-muted/40 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          <tr><th className="px-4 py-2.5">Event</th><th className="px-4 py-2.5">In-app</th><th className="px-4 py-2.5">Email</th></tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map(([label, a, b]) => (
            <tr key={label as string}>
              <td className="px-4 py-3">{label}</td>
              <td className="px-4 py-3"><input type="checkbox" defaultChecked={a as boolean} className="h-4 w-4" /></td>
              <td className="px-4 py-3"><input type="checkbox" defaultChecked={b as boolean} className="h-4 w-4" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  ),
});