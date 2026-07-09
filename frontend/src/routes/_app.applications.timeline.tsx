import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";
import { useQuery } from "@tanstack/react-query";
import { getUserTimeline } from "@/lib/api/applications";

export const Route = createFileRoute("/_app/applications/timeline")({
  head: () => ({ meta: [{ title: "Application timeline · SiraFit" }] }),
  component: () => {
    const { data: events = [], isLoading } = useQuery({
      queryKey: ["application-timeline"],
      queryFn: () => getUserTimeline(100),
    });

    // Group events by date
    const grouped = events.reduce((acc: Record<string, typeof events>, event: any) => {
      const date = new Date(event.occurred_at);
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      
      const key = date.toDateString() === today.toDateString() 
        ? "Today" 
        : date.toDateString() === yesterday.toDateString()
        ? "Yesterday"
        : date.toLocaleDateString("en-US", { day: "numeric", month: "short" });
      
      if (!acc[key]) acc[key] = [];
      acc[key].push(event);
      return acc;
    }, {});

    if (isLoading) {
      return (
        <PageBody>
          <PageHeader eyebrow="Pipeline" title="Application timeline" />
          <div className="grid place-items-center py-20">Loading timeline...</div>
        </PageBody>
      );
    }

    return (
      <PageBody>
        <PageHeader eyebrow="Pipeline" title="Application timeline" description="Chronological activity across every application." />
        <Panel>
          <div className="divide-y divide-border">
            {Object.entries(grouped).map(([date, items]) => (
              <div key={date} className="p-5">
                <div className="mb-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  {date}
                </div>
                <ul className="space-y-3">
                  {items.map((event: any, i: number) => (
                    <li key={event.id} className="flex items-start gap-3 text-sm">
                      <span className="w-12 shrink-0 font-mono text-[11px] text-muted-foreground tabular-nums">
                        {new Date(event.occurred_at).toLocaleTimeString("en-US", { 
                          hour: "numeric", 
                          minute: "2-digit" 
                        })}
                      </span>
                      <StatusPill status={event.event_type === "status_change" ? event.event_metadata?.to_status : event.event_type} />
                      <span className="text-foreground/90">{event.title}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Panel>
      </PageBody>
    );
  },
});