import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScorePill, Tag } from "@/components/sirafit/bits";
import { resumeVersions } from "@/lib/mock";

export const Route = createFileRoute("/_app/resumes/")({
  head: () => ({ meta: [{ title: "Resume versions · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader
        eyebrow="Assets"
        title="Resume versions"
        description="Every resume you've generated. Immutable history, version-aware merging."
        actions={
          <>
            <Link to="/resumes/profiles" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Manage profiles</Link>
            <Link to="/resumes/builder" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">New resume</Link>
          </>
        }
      />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {resumeVersions.map((r) => (
          <Link key={r.id} to="/resumes/$id" params={{ id: r.id }} className="group block rounded-lg bg-card p-4 ring-1 ring-border hover:ring-[color:var(--brand)]/40">
            <div className="flex items-center justify-between">
              <Tag>{r.template}</Tag>
              {r.score ? <ScorePill value={r.score} /> : <span className="font-mono text-[10px] text-muted-foreground uppercase">master</span>}
            </div>
            <div className="mt-3 text-sm font-semibold">{r.name}</div>
            <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground">
              <span className="font-mono">{r.id}</span>
              <span className="tabular-nums">{r.createdAt}</span>
            </div>
            <div className="mt-3 grid h-32 place-items-center rounded border border-border bg-muted/30">
              <div className="space-y-1">
                <div className="h-1 w-24 bg-foreground/80" />
                <div className="h-1 w-16 bg-muted-foreground/40" />
                <div className="mt-2 h-1 w-28 bg-muted-foreground/30" />
                <div className="h-1 w-20 bg-muted-foreground/30" />
                <div className="h-1 w-24 bg-muted-foreground/30" />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </PageBody>
  ),
});