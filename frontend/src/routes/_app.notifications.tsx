import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/notifications")({
  head: () => ({ meta: [{ title: "Notifications · SiraFit" }] }),
  component: Notifications,
});

function Notifications() {
  const queryClient = useQueryClient();

  const {
    data: response,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => getNotifications({ limit: 50 }),
  });

  const notifications = response?.notifications || [];

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="System" title="Notifications" description="Loading..." />
        <div className="grid place-items-center py-20">Loading...</div>
      </PageBody>
    );
  }

  if (error) {
    return (
      <PageBody>
        <PageHeader
          eyebrow="System"
          title="Notifications"
          description="Failed to load notifications"
        />
        <div className="px-4 py-8 text-center">
          <div className="text-sm text-destructive">{error.message}</div>
        </div>
      </PageBody>
    );
  }

  const unreadCount = notifications.filter(
    (n: (typeof notifications)[number]) => n.status === "unread",
  ).length;

  return (
    <PageBody>
      <PageHeader
        eyebrow="System"
        title="Notifications"
        description="Alerts, reminders, sync events."
        actions={
          unreadCount > 0 ? (
            <Button variant="outline" onClick={() => markAllReadMutation.mutate()}>
              Mark all read ({unreadCount})
            </Button>
          ) : (
            <Button variant="outline" disabled>
              All caught up
            </Button>
          )
        }
      />
      <Panel>
        <ul className="divide-y divide-border">
          {notifications.length === 0 ? (
            <li className="px-4 py-8 text-center text-muted-foreground">No notifications yet</li>
          ) : (
            notifications.map((n: (typeof notifications)[number]) => (
              <li
                key={n.id}
                className={`flex items-start gap-3 px-4 py-3 ${n.status === "unread" ? "bg-muted/20" : ""}`}
              >
                <span
                  className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${n.status === "unread" ? "bg-[color:var(--brand)]" : "bg-muted-foreground/30"}`}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <div className="text-sm font-semibold">{n.title}</div>
                    <StatusPill status={n.kind} />
                  </div>
                  <div className="text-[12px] text-muted-foreground">{n.body}</div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <div className="font-mono text-[11px] text-muted-foreground tabular-nums">
                    {new Date(n.created_at).toLocaleString()}
                  </div>
                  {n.status === "unread" && (
                    <button
                      onClick={() => markReadMutation.mutate(n.id)}
                      className="rounded px-1.5 py-0.5 text-[10px] font-medium ring-1 ring-border hover:bg-muted"
                    >
                      Mark read
                    </button>
                  )}
                </div>
              </li>
            ))
          )}
        </ul>
      </Panel>
    </PageBody>
  );
}

async function getNotifications(params?: { status?: string; skip?: number; limit?: number }) {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.skip !== undefined) search.set("skip", params.skip.toString());
  if (params?.limit !== undefined) search.set("limit", params.limit.toString());

  const response = await fetch(`/api/v1/notifications?${search}`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error("Failed to fetch notifications");
  return response.json();
}

async function markNotificationRead(id: string) {
  const response = await fetch(`/api/v1/notifications/${id}/read`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) throw new Error("Failed to mark notification as read");
  return response.json();
}

async function markAllNotificationsRead() {
  const response = await fetch("/api/v1/notifications/mark-all-read", {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) throw new Error("Failed to mark all notifications as read");
  return response.json();
}
