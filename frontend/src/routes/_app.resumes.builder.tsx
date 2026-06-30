import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/resumes/builder")({
  head: () => ({ meta: [{ title: "Resume builder · SiraFit" }] }),
  component: Builder,
});

function Builder() {
  return (
    <PageBody className="max-w-none">
      <PageHeader eyebrow="Assets · Builder" title="Tailored resume: Stripe — Infra Engineer" description="Structured input → AI tailoring → schema validation → ATS-ready PDF." actions={<><Button variant="outline">Re-validate</Button><Button>Generate v2.2</Button></>} />

      <div className="grid gap-4 lg:grid-cols-12">
        <Panel title="Structure" className="lg:col-span-3" bodyClassName="p-4 space-y-4">
          {["Header","Summary","Experience","Projects","Skills","Education"].map((s, i) => (
            <div key={s} className="flex items-center justify-between text-sm">
              <span className={i === 2 ? "font-semibold" : "text-muted-foreground"}>{s}</span>
              <Tag>{i === 2 ? "edit" : "ok"}</Tag>
            </div>
          ))}
        </Panel>

        <Panel title="Generation settings" className="lg:col-span-4" bodyClassName="p-4 space-y-4">
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">Tailoring priorities</div>
            <div className="mt-2 space-y-2">
              {[["Distributed systems",95],["Kubernetes",90],["PostgreSQL",80],["Go",75]].map(([s,v]) => (
                <div key={s as string}>
                  <div className="mb-1 flex items-center justify-between text-[12px]"><span>{s}</span><span className="font-mono">{v}</span></div>
                  <ScoreMeter value={v as number} />
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">Template</div>
            <div className="mt-2 flex flex-wrap gap-1.5">{["Minimal","Technical","Modern","Corporate","Compact"].map((t) => (<Tag key={t}>{t}{t === "Technical" ? " ·" : ""}</Tag>))}</div>
          </div>
          <div className="rounded bg-muted/40 p-3 text-[11px] text-muted-foreground">Schema validation enforced. AI repair attempts capped at 1.</div>
        </Panel>

        <Panel title="Live preview" className="lg:col-span-5" bodyClassName="p-6 bg-muted/30 flex justify-center">
          <ResumePreview />
        </Panel>
      </div>

      <Panel title="Generation log">
        <ul className="divide-y divide-border font-mono text-[11px]">
          {[["09:14","Generation complete: v2.1 · 1242 tokens"],["09:13","Schema valid · 0 repair attempts"],["09:13","Prompt built: 4 sections, 2 priorities"],["09:12","Pulled master profile rev 87"]].map((r) => (
            <li key={r[1]} className="flex gap-3 px-4 py-2"><span className="text-muted-foreground">{r[0]}</span><span>{r[1]}</span></li>
          ))}
        </ul>
      </Panel>

      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
        <span>Resume rv-12 · linked to job j-001 (Stripe)</span>
        <Link to="/resumes/$id" params={{ id: "rv-12" }} className="text-[color:var(--brand)] hover:underline">Open preview →</Link>
      </div>
    </PageBody>
  );
}

function ResumePreview() {
  return (
    <div className="w-full max-w-md space-y-4 rounded-sm bg-card p-8 shadow-2xl ring-1 ring-border">
      <header className="border-b border-border pb-3">
        <h3 className="text-lg font-semibold tracking-tight">{profile.name}</h3>
        <p className="text-[11px] text-muted-foreground">{profile.email} · {profile.location} · {profile.github}</p>
      </header>
      <section>
        <h4 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Experience</h4>
        {profile.experience.map((e) => (
          <div key={e.company} className="mt-2 space-y-1">
            <div className="flex items-baseline justify-between text-[12px]"><span className="font-semibold">{e.role} · {e.company}</span><span className="text-muted-foreground">{e.period}</span></div>
            <ul className="list-disc pl-4 text-[11px] leading-relaxed text-foreground/90">{e.bullets.map((b) => (<li key={b}>{b}</li>))}</ul>
          </div>
        ))}
      </section>
      <section>
        <h4 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Skills</h4>
        <p className="mt-1 text-[11px] text-foreground/90">{profile.skills.join(" · ")}</p>
      </section>
      <section>
        <h4 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Education</h4>
        {profile.education.map((e) => (
          <div key={e.school} className="flex items-baseline justify-between text-[11px]"><span>{e.degree} · {e.school}</span><span className="text-muted-foreground">{e.period}</span></div>
        ))}
      </section>
    </div>
  );
}