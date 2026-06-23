import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel } from "@/components/sirafit/bits";
import { followUps } from "@/lib/mock";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/applications/followups")({
  head: () => ({ meta: [{ title: "Follow-ups · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Pipeline" title="Follow-up center" description="Recruiter pings, deadlines, and reminders. Nothing falls through." actions={<Button>+ New reminder</Button>} />
      <Panel>
        <ul className="divide-y divide-border">
          {followUps.map((f) => (
            <li key={f.id} className="flex items-center justify-between gap-4 px-4 py-3.5">
              <div className="flex items-center gap-3">
                <input type="checkbox" className="h-4 w-4 rounded border-input" />
                <div>
                  <div className="text-sm font-medium">{f.what}</div>
                  <div className="text-[11px] text-muted-foreground">{f.who}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-[11px] text-muted-foreground tabular-nums">{f.when}</span>
                <Button variant="ghost" size="sm">Snooze</Button>
              </div>
            </li>
          ))}
        </ul>
      </Panel>
    </PageBody>
  ),
});