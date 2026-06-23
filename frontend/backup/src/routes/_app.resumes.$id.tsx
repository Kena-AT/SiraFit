import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScorePill } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { profile, resumeVersions } from "@/lib/mock";

export const Route = createFileRoute("/_app/resumes/$id")({
  head: () => ({ meta: [{ title: "Resume preview · SiraFit" }] }),
  component: Preview,
});

function Preview() {
  const { id } = Route.useParams();
  const v = resumeVersions.find((r) => r.id === id) ?? resumeVersions[0];
  return (
    <PageBody className="max-w-none">
      <PageHeader eyebrow={`Resume · ${v.id}`} title={v.name} description={`${v.template} template · created ${v.createdAt}`} actions={<><Button variant="outline">Download .docx</Button><Button>Export PDF</Button></>} />
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Panel bodyClassName="bg-muted/30 p-8 grid place-items-center">
          <div className="w-full max-w-2xl space-y-5 rounded-sm bg-card p-12 shadow-2xl ring-1 ring-border">
            <header className="border-b border-border pb-4">
              <h2 className="text-2xl font-semibold tracking-tight">{profile.name}</h2>
              <p className="text-xs text-muted-foreground">{profile.email} · {profile.location} · {profile.github}</p>
            </header>
            <section><h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Summary</h3><p className="mt-1 text-[13px]">Junior software engineer with hands-on experience in distributed systems, Kubernetes, and Go. Comfortable owning services from design to on-call.</p></section>
            <section><h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Experience</h3>
              {profile.experience.map((e) => (
                <div key={e.company} className="mt-3 space-y-1">
                  <div className="flex items-baseline justify-between text-sm"><span className="font-semibold">{e.role} · {e.company}</span><span className="text-muted-foreground">{e.period}</span></div>
                  <ul className="list-disc space-y-0.5 pl-5 text-[12px] leading-relaxed">{e.bullets.map((b) => (<li key={b}>{b}</li>))}</ul>
                </div>
              ))}
            </section>
            <section><h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Projects</h3>
              {profile.projects.map((p) => (<div key={p.name} className="mt-2 text-[12px]"><div className="font-semibold">{p.name}</div><div className="text-foreground/80">{p.desc}</div></div>))}
            </section>
            <section><h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Skills</h3><p className="mt-1 text-[12px]">{profile.skills.join(" · ")}</p></section>
            <section><h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Education</h3>
              {profile.education.map((e) => (<div key={e.school} className="flex items-baseline justify-between text-[12px]"><span>{e.degree} · {e.school}</span><span className="text-muted-foreground">{e.period}</span></div>))}
            </section>
          </div>
        </Panel>
        <div className="space-y-4">
          <Panel title="ATS readiness">
            <div className="space-y-3 p-4 text-sm">
              <div className="flex items-center justify-between"><span>Keyword coverage</span>{v.score ? <ScorePill value={v.score} /> : <span>—</span>}</div>
              <div className="flex items-center justify-between"><span>Parsable structure</span><ScorePill value={98} /></div>
              <div className="flex items-center justify-between"><span>Section ordering</span><ScorePill value={90} /></div>
            </div>
          </Panel>
          <Panel title="Versions">
            <ul className="divide-y divide-border text-sm">
              {resumeVersions.map((r) => (
                <li key={r.id} className="flex items-center justify-between px-3 py-2">
                  <Link to="/resumes/$id" params={{ id: r.id }} className="hover:underline">{r.name}</Link>
                  <span className="font-mono text-[11px] text-muted-foreground tabular-nums">{r.createdAt}</span>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>
    </PageBody>
  );
}