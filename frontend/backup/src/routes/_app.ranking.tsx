import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, Tag } from "@/components/sirafit/bits";
import { jobs } from "@/lib/mock";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/ranking")({
  head: () => ({ meta: [{ title: "Opportunity ranking · SiraFit" }] }),
  component: () => {
    const ranked = [...jobs].sort((a, b) => b.match - a.match);
    return (
      <PageBody>
        <PageHeader eyebrow="Intelligence" title="Opportunity ranking" description="Where to spend your next hour. Deterministic priorities, you decide what to apply to." actions={<Button>Run re-ranking</Button>} />
        <Panel>
          <ol className="divide-y divide-border">
            {ranked.map((j, i) => (
              <li key={j.id} className="flex items-center gap-4 px-4 py-3">
                <span className="w-8 font-mono text-sm font-semibold tabular-nums text-muted-foreground">#{String(i + 1).padStart(2, "0")}</span>
                <div className="flex-1">
                  <Link to="/jobs/$jobId" params={{ jobId: j.id }} className="text-sm font-semibold hover:underline">{j.company} — {j.role}</Link>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground"><span>{j.location}</span>·<span>{j.salary}</span>·<Tag>{j.source}</Tag></div>
                </div>
                <div className="w-40"><ScoreMeter value={j.match} /></div>
                <Link to="/resumes/builder" className="text-xs font-medium text-[color:var(--brand)] hover:underline">Tailor →</Link>
              </li>
            ))}
          </ol>
        </Panel>
      </PageBody>
    );
  },
});