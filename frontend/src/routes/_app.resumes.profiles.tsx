import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";

const variants = [
  { id: "p1", name: "Backend / Infra master", health: 92, sections: 8, tags: ["Go", "Kubernetes", "PostgreSQL"], active: true },
  { id: "p2", name: "Fullstack TypeScript", health: 87, sections: 8, tags: ["TypeScript", "React", "Node"] },
  { id: "p3", name: "AI / ML focused", health: 64, sections: 6, tags: ["Python", "PyTorch", "LangChain"] },
];

export const Route = createFileRoute("/_app/resumes/profiles")({
  head: () => ({ meta: [{ title: "Resume profiles · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Assets" title="Resume profiles" description="The canonical source of truth for your career data. Tailored resumes are derived from these." actions={<Link to="/resumes/profile-editor" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">New profile</Link>} />
      <div className="grid gap-3 md:grid-cols-3">
        {variants.map((v) => (
          <div key={v.id} className="rounded-lg bg-card p-5 ring-1 ring-border">
            <div className="flex items-center justify-between"><div className="text-sm font-semibold">{v.name}</div>{v.active ? <span className="rounded bg-[color:var(--brand)]/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-widest text-[color:var(--brand)]">Active</span> : null}</div>
            <div className="mt-3 text-[11px] text-muted-foreground">{v.sections} sections · health {v.health}%</div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted"><div className="h-full bg-[color:var(--brand)]" style={{ width: `${v.health}%` }} /></div>
            <div className="mt-4 flex flex-wrap gap-1.5">{v.tags.map((t) => (<Tag key={t}>{t}</Tag>))}</div>
            <div className="mt-4 flex items-center justify-between">
              <Link to="/resumes/profile-editor" className="text-xs font-medium text-[color:var(--brand)] hover:underline">Edit →</Link>
              <Button variant="ghost" size="sm">Duplicate</Button>
            </div>
          </div>
        ))}
      </div>
    </PageBody>
  ),
});