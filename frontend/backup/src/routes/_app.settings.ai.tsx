import { createFileRoute } from "@tanstack/react-router";
import { Panel, AgentDot, Tag } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/settings/ai")({
  head: () => ({ meta: [{ title: "AI & agent settings · SiraFit" }] }),
  component: () => (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Gemini API key" description="Stored locally only. Never transmitted to SiraFit cloud.">
        <div className="space-y-3 p-4">
          <div className="space-y-1.5"><Label>API key</Label><Input type="password" defaultValue="AIza••••••••••••••••••••" /></div>
          <div className="flex flex-wrap items-center gap-2">{["Gemini 1.5 Pro","Gemini 1.5 Flash","Custom endpoint"].map((m) => (<Tag key={m}>{m}{m === "Gemini 1.5 Pro" ? " · active" : ""}</Tag>))}</div>
          <Button variant="outline">Test connection</Button>
        </div>
      </Panel>
      <Panel title="Local agent">
        <div className="space-y-3 p-4 text-sm">
          <AgentDot label="Connected · v0.8.2" />
          <div className="text-[12px] text-muted-foreground">Auto-update enabled. Next check in 4h.</div>
          <div className="grid grid-cols-2 gap-2 text-[12px]">
            <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Scrape rate</div>1 req / 1.2s</div>
            <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Queue cap</div>64</div>
            <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Retry max</div>3</div>
            <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Cooldown</div>60s</div>
          </div>
          <div className="flex gap-2"><Button variant="outline" size="sm">Restart agent</Button><Button variant="ghost" size="sm">View logs</Button></div>
        </div>
      </Panel>
      <Panel title="Generation options" className="lg:col-span-2">
        <div className="grid gap-3 p-4 sm:grid-cols-3 text-sm">
          <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Repair attempts</div>1 (max)</div>
          <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Tokens / generation</div>1500</div>
          <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Throttle</div>5 / min</div>
        </div>
      </Panel>
    </div>
  ),
});