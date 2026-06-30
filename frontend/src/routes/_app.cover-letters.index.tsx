import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";

export const Route = createFileRoute("/_app/cover-letters/")({
  head: () => ({ meta: [{ title: "Cover letters · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Assets" title="Cover letters" description="Concise, role-aware letters generated from your master profile." actions={<Link to="/cover-letters/builder" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">New letter</Link>} />
      <Panel>
        <ul className="divide-y divide-border">
          {coverLetters.map((c) => (
            <li key={c.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <div className="text-sm font-semibold">{c.job}</div>
                <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground"><Tag>{c.id}</Tag>{c.words} words · {c.createdAt}</div>
              </div>
              <Link to="/cover-letters/builder" className="text-xs font-medium text-[color:var(--brand)] hover:underline">Open →</Link>
            </li>
          ))}
        </ul>
      </Panel>
    </PageBody>
  ),
});