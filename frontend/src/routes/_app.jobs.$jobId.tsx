import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, ScorePill, StatusPill, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getJob } from "@/lib/mock-jobs";

export const Route = createFileRoute("/_app/jobs/$jobId")({
  head: () => ({ meta: [{ title: "Job details · SiraFit" }] }),
  component: JobDetails,
});

function JobDetails() {
  const { jobId } = Route.useParams();
  const j = getJob(jobId);
  const breakdown = [
    { label: "Skill overlap", value: 87 },
    { label: "Seniority alignment", value: 92 },
    { label: "Domain relevance", value: 78 },
    { label: "Location / remote", value: 100 },
    { label: "Infra & tooling", value: 91 },
  ];
  return (
    <PageBody>
      <PageHeader
        eyebrow={`${j.source} · ${j.id}`}
        title={`${j.company} — ${j.role}`}
        description={`${j.location} · ${j.remote} · ${j.salary}`}
        actions={
          <>
            {j.status ? <StatusPill status={j.status} /> : null}
            <Link to="/resumes/builder" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Tailor resume</Link>
            <Link to="/cover-letters/builder" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">Apply</Link>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Panel title="Description">
            <div className="space-y-4 p-5">
              <p className="text-sm text-foreground/90">{j.description ?? "—"}</p>
              {j.responsibilities ? (
                <div>
                  <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Responsibilities</div>
                  <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm">{j.responsibilities.map((r) => (<li key={r}>{r}</li>))}</ul>
                </div>
              ) : null}
              {j.required ? (
                <div>
                  <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Required</div>
                  <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm">{j.required.map((r) => (<li key={r}>{r}</li>))}</ul>
                </div>
              ) : null}
              {j.preferred ? (
                <div>
                  <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Preferred</div>
                  <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm">{j.preferred.map((r) => (<li key={r}>{r}</li>))}</ul>
                </div>
              ) : null}
              <div className="flex flex-wrap gap-1.5 pt-2">{j.tags.map((t) => (<Tag key={t}>{t}</Tag>))}</div>
            </div>
          </Panel>

          <Panel title="AI analysis" description="Bounded interpretation only — does not change the score">
            <div className="space-y-3 p-5 text-sm">
              <p><span className="font-semibold">Classification:</span> Backend / Infrastructure Engineer (mid-senior IC).</p>
              <p><span className="font-semibold">Strongest alignment:</span> Your Cloud Scale Labs internship maps directly to the distributed-systems and Kubernetes asks.</p>
              <p><span className="font-semibold">Skill gaps:</span> Limited gRPC and Terraform exposure on file. Consider surfacing related coursework or projects.</p>
              <p className="font-mono text-[11px] text-muted-foreground">Generated 12m ago · Gemini 1.5 Pro · validated against canonical schema (no repair needed).</p>
            </div>
          </Panel>
        </div>

        <div className="space-y-4">
          <Panel title="Match score" actions={<ScorePill value={j.match} />}>
            <div className="space-y-3 p-4">
              {breakdown.map((b) => (
                <div key={b.label}>
                  <div className="mb-1 flex items-center justify-between text-[12px]">
                    <span className="text-muted-foreground">{b.label}</span>
                    <span className="font-mono font-semibold tabular-nums">{b.value}</span>
                  </div>
                  <ScoreMeter value={b.value} />
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Recommendations">
            <ul className="divide-y divide-border text-sm">
              {["Lead with distributed-systems project in summary", "Add gRPC line item to skills cluster", "Surface scale numbers (req/s, p99) on first bullet"].map((r) => (
                <li key={r} className="flex items-start gap-2 px-4 py-2.5"><span className="mt-1 h-1 w-1 rounded-full bg-[color:var(--brand)]" />{r}</li>
              ))}
            </ul>
          </Panel>
          <Panel title="Application history">
            <div className="p-4 text-[12px] text-muted-foreground">No prior application. Saved to pipeline on 21 Jun.</div>
          </Panel>
        </div>
      </div>
    </PageBody>
  );
}