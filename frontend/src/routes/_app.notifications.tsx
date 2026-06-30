import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/notifications")({
  head: () => ({ meta: [{ title: "Notifications · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="System" title="Notifications" description="Alerts, reminders, sync events." actions={<Button variant="outline">Mark all read</Button>} />
      <Panel>
        <ul className="divide-y divide-border">
          {notifications.map((n) => (
            <li key={n.id} className="flex items-start gap-3 px-4 py-3">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--brand)]" />
              <div className="flex-1">
                <div className="flex items-center gap-2"><div className="text-sm font-semibold">{n.title}</div><StatusPill status={n.kind} /></div>
                <div className="text-[12px] text-muted-foreground">{n.body}</div>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground tabular-nums">{n.time}</div>
            </li>
          ))}
        </ul>
      </Panel>
    </PageBody>
  ),
});