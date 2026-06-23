import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";

const events = [
  { d: "Today", items: [{ t: "10:42", status: "Interview", text: "Recruiter call confirmed with Linear for Thu 10:00." }, { t: "09:18", status: "Applied", text: "Submitted application to Stripe — Infrastructure." }] },
  { d: "Yesterday", items: [{ t: "16:05", status: "Assessment", text: "Received PlanetScale take-home brief." }, { t: "11:20", status: "Saved", text: "Saved Supabase DevRel Engineer." }] },
  { d: "20 Jun", items: [{ t: "14:00", status: "Rejected", text: "Retool — resume screen." }, { t: "09:30", status: "Applied", text: "PostHog — Full Stack Engineer." }] },
];

export const Route = createFileRoute("/_app/applications/timeline")({
  head: () => ({ meta: [{ title: "Application timeline · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Pipeline" title="Application timeline" description="Chronological activity across every application." />
      <Panel>
        <div className="divide-y divide-border">
          {events.map((g) => (
            <div key={g.d} className="p-5">
              <div className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">{g.d}</div>
              <ul className="space-y-3">
                {g.items.map((it, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm">
                    <span className="w-12 shrink-0 font-mono text-[11px] text-muted-foreground tabular-nums">{it.t}</span>
                    <StatusPill status={it.status} />
                    <span className="text-foreground/90">{it.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Panel>
    </PageBody>
  ),
});