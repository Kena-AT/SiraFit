import { createFileRoute } from "@tanstack/react-router";
import { Panel } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/settings/")({
  head: () => ({ meta: [{ title: "Account settings · SiraFit" }] }),
  component: () => (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Profile">
        <div className="grid gap-3 p-4">
          <div className="space-y-1.5"><Label>Name</Label><Input defaultValue={profile.name} /></div>
          <div className="space-y-1.5"><Label>Email</Label><Input defaultValue={profile.email} /></div>
          <div className="space-y-1.5"><Label>Location</Label><Input defaultValue={profile.location} /></div>
          <Button className="w-fit">Save changes</Button>
        </div>
      </Panel>
      <Panel title="Password">
        <div className="grid gap-3 p-4">
          <div className="space-y-1.5"><Label>Current password</Label><Input type="password" /></div>
          <div className="space-y-1.5"><Label>New password</Label><Input type="password" /></div>
          <div className="space-y-1.5"><Label>Confirm password</Label><Input type="password" /></div>
          <Button variant="outline" className="w-fit">Update password</Button>
        </div>
      </Panel>
      <Panel title="Devices" className="lg:col-span-2">
        <ul className="divide-y divide-border text-sm">
          <li className="flex items-center justify-between px-4 py-3"><div><div className="font-semibold">MacBook Pro · alex-mbp</div><div className="text-[11px] text-muted-foreground">Active · last seen 12s ago</div></div><span className="rounded bg-[color:var(--brand)]/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-[color:var(--brand)]">This device</span></li>
        </ul>
      </Panel>
    </div>
  ),
});