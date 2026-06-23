import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";
import { importHistory } from "@/lib/mock";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/jobs/history")({
  head: () => ({ meta: [{ title: "Import history · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Pipeline" title="Import history" description="Every scrape run, success or fail. Reprocess any failed batch." />
      <Panel>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-muted/40 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            <tr><th className="px-4 py-2.5">ID</th><th className="px-4 py-2.5">Source</th><th className="px-4 py-2.5">Count</th><th className="px-4 py-2.5">OK</th><th className="px-4 py-2.5">Fail</th><th className="px-4 py-2.5">When</th><th className="px-4 py-2.5">Status</th><th className="px-4 py-2.5 text-right">Action</th></tr>
          </thead>
          <tbody className="divide-y divide-border">
            {importHistory.map((h) => (
              <tr key={h.id} className="hover:bg-muted/30">
                <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground">{h.id}</td>
                <td className="px-4 py-3 font-medium">{h.source}</td>
                <td className="px-4 py-3 tabular-nums">{h.count}</td>
                <td className="px-4 py-3 tabular-nums text-[color:var(--success)]">{h.ok}</td>
                <td className="px-4 py-3 tabular-nums text-destructive">{h.fail}</td>
                <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground">{h.when}</td>
                <td className="px-4 py-3"><StatusPill status={h.status} /></td>
                <td className="px-4 py-3 text-right">{h.fail > 0 ? <Button variant="outline" size="sm">Reprocess</Button> : <span className="text-[11px] text-muted-foreground">—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </PageBody>
  ),
});