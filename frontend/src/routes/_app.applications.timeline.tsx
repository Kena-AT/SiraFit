import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill, EmptyState } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { getUserTimeline } from "@/lib/api/applications";
import { useState } from "react";

const PAGE_SIZE = 50;

// Human-readable labels for non-status_change event types
const EVENT_TYPE_LABELS: Record<string, string> = {
  note_added: "Note added",
  note_updated: "Note updated",
  contact_added: "Contact added",
  contact_updated: "Contact updated",
  follow_up_set: "Follow-up set",
  follow_up_cleared: "Follow-up cleared",
  resume_attached: "Resume attached",
  email_sent: "Email sent",
  reminder: "Reminder",
};

function formatEventType(type: string): string {
  return EVENT_TYPE_LABELS[type] ?? type.replace(/_/g, " ");
}

export const Route = createFileRoute("/_app/applications/timeline")({
  head: () => ({ meta: [{ title: "Application timeline · SiraFit" }] }),
  component: TimelinePage,
});

function TimelinePage() {
  const [limit, setLimit] = useState(PAGE_SIZE);

  const { data: events = [], isLoading } = useQuery({
    queryKey: ["application-timeline", limit],
    queryFn: () => getUserTimeline(limit, 0),
  });

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Pipeline" title="Application timeline" />
        <div className="grid place-items-center py-20">Loading timeline...</div>
      </PageBody>
    );
  }

  if (events.length === 0) {
    return (
      <PageBody>
        <PageHeader
          eyebrow="Pipeline"
          title="Application timeline"
          description="Chronological activity across every application."
        />
        <EmptyState
          title="No activity yet"
          body="Status changes, notes, and contacts will appear here as you track applications."
        />
      </PageBody>
    );
  }

  // Group events by date label, preserving chronological order
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  type GroupEntry = { key: string; date: Date; items: typeof events };
  const groupMap = new Map<string, GroupEntry>();

  for (const event of events) {
    const d = new Date((event as any).occurred_at);
    let key: string;
    if (d.toDateString() === today.toDateString()) {
      key = "Today";
    } else if (d.toDateString() === yesterday.toDateString()) {
      key = "Yesterday";
    } else {
      key = d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
    }
    if (!groupMap.has(key)) {
      groupMap.set(key, { key, date: d, items: [] });
    }
    groupMap.get(key)!.items.push(event);
  }

  // Sort groups newest-first
  const groups = Array.from(groupMap.values()).sort(
    (a, b) => b.date.getTime() - a.date.getTime(),
  );

  return (
    <PageBody>
      <PageHeader
        eyebrow="Pipeline"
        title="Application timeline"
        description="Chronological activity across every application."
      />
      <Panel>
        <div className="divide-y divide-border">
          {groups.map(({ key, items }) => (
            <div key={key} className="p-5">
              <div className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                {key}
              </div>
              <ul className="space-y-3">
                {items.map((event: any) => (
                  <li key={event.id} className="flex items-start gap-3 text-sm">
                    <span className="w-14 shrink-0 font-mono text-[11px] text-muted-foreground tabular-nums">
                      {new Date(event.occurred_at).toLocaleTimeString("en-US", {
                        hour: "numeric",
                        minute: "2-digit",
                      })}
                    </span>

                    {event.event_type === "status_change" ? (
                      <StatusPill status={event.event_metadata?.to_status ?? "unknown"} />
                    ) : (
                      <span className="inline-block rounded-full bg-muted px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
                        {formatEventType(event.event_type)}
                      </span>
                    )}

                    <span className="flex-1 text-foreground/90">{event.title}</span>

                    {/* Link back to the application */}
                    {event.application_id && (
                      <Link
                        to="/applications/$id"
                        params={{ id: event.application_id }}
                        className="shrink-0 font-mono text-[10px] text-[color:var(--brand)] hover:underline"
                      >
                        View →
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Load more */}
        {events.length === limit && (
          <div className="flex justify-center border-t border-border py-4">
            <Button variant="outline" size="sm" onClick={() => setLimit((n) => n + PAGE_SIZE)}>
              Load more
            </Button>
          </div>
        )}
      </Panel>
    </PageBody>
  );
}
