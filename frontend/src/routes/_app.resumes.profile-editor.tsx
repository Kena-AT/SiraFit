import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

const sections = ["Header", "Experience", "Projects", "Skills", "Education", "Certifications", "Awards", "Languages", "Social"];

export const Route = createFileRoute("/_app/resumes/profile-editor")({
  head: () => ({ meta: [{ title: "Profile editor · SiraFit" }] }),
  component: () => (
    <PageBody className="max-w-none">
      <PageHeader eyebrow="Assets · Profile" title="Backend / Infra master" description="Edit your structured resume profile. Auto-saved locally every 5s." actions={<Button>Save snapshot</Button>} />
      <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
        <Panel title="Sections">
          <ul className="divide-y divide-border">
            {sections.map((s, i) => (
              <li key={s} className={`flex items-center justify-between px-3 py-2 text-sm ${i === 1 ? "bg-muted/50 font-semibold" : ""}`}>
                <span>{s}</span>
                <span className="font-mono text-[10px] text-muted-foreground">{i === 1 ? "2" : ""}</span>
              </li>
            ))}
          </ul>
        </Panel>
        <div className="space-y-4">
          <Panel title="Header">
            <div className="grid gap-3 p-4 sm:grid-cols-2">
              <div><label className="text-[10px] font-semibold uppercase text-muted-foreground">Name</label><Input defaultValue={profile.name} /></div>
              <div><label className="text-[10px] font-semibold uppercase text-muted-foreground">Title</label><Input defaultValue={profile.title} /></div>
              <div><label className="text-[10px] font-semibold uppercase text-muted-foreground">Email</label><Input defaultValue={profile.email} /></div>
              <div><label className="text-[10px] font-semibold uppercase text-muted-foreground">Location</label><Input defaultValue={profile.location} /></div>
            </div>
          </Panel>
          <Panel title="Experience" actions={<Button variant="outline" size="sm">+ Add role</Button>}>
            <div className="divide-y divide-border">
              {profile.experience.map((e) => (
                <div key={e.company} className="space-y-3 p-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="sm:col-span-1"><label className="text-[10px] font-semibold uppercase text-muted-foreground">Company</label><Input defaultValue={e.company} /></div>
                    <div className="sm:col-span-1"><label className="text-[10px] font-semibold uppercase text-muted-foreground">Role</label><Input defaultValue={e.role} /></div>
                    <div className="sm:col-span-1"><label className="text-[10px] font-semibold uppercase text-muted-foreground">Period</label><Input defaultValue={e.period} /></div>
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold uppercase text-muted-foreground">Achievements</label>
                    <Textarea defaultValue={e.bullets.join("\n")} rows={3} />
                  </div>
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Skills">
            <div className="flex flex-wrap gap-1.5 p-4">
              {profile.skills.map((s) => (<Tag key={s}>{s}</Tag>))}
              <Button variant="ghost" size="sm">+ Add skill</Button>
            </div>
          </Panel>
        </div>
      </div>
    </PageBody>
  ),
});