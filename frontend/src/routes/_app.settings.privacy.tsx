import { createFileRoute } from "@tanstack/react-router";
import { Panel } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/settings/privacy")({
  head: () => ({ meta: [{ title: "Data & privacy · SiraFit" }] }),
  component: () => (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Export your data">
        <div className="space-y-3 p-4 text-sm">
          <p>
            Download a JSON archive of every job, application, resume, and event in your account.
          </p>
          <Button>Generate export</Button>
        </div>
      </Panel>
      <Panel title="Retention">
        <div className="space-y-3 p-4 text-sm">
          <div className="flex items-center justify-between">
            <span>Raw HTML</span>
            <span className="font-mono text-muted-foreground">30 days</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Event log (cloud)</span>
            <span className="font-mono text-muted-foreground">365 days</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Event log (local)</span>
            <span className="font-mono text-muted-foreground">forever</span>
          </div>
        </div>
      </Panel>
      <Panel title="Danger zone" className="lg:col-span-2">
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
          <div>
            Permanently delete your account, cloud projections, and local agent registration.
          </div>
          <Button variant="destructive">Delete account</Button>
        </div>
      </Panel>
    </div>
  ),
});
