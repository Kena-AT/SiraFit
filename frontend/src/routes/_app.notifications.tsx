import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { useState } from "react";
import {
  getNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
} from "@/lib/api/notifications";

export const Route = createFileRoute("/_app/notifications")({
  head: () => ({ meta: [{ title: "Notifications · SiraFit" }] }),
  component: Notifications,
});

function Notifications() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [limit, setLimit] = useState<number>(50);

  const {
    data: response,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["notifications", statusFilter, limit],
    queryFn: () =>
      getNotifications({
        status: statusFilter === "all" ? undefined : statusFilter,
        limit,
      }),
    refetchInterval: 5000,
  });

  const { data: unreadData } = useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: getUnreadCount,
    refetchInterval: 5000,
  });

  const notifications = response?.notifications || [];
  const total = response?.total || 0;
  const unreadCount = unreadData?.count || 0;

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteNotification,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  if (isLoading && limit === 50) {
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
      <div className="mb-4 flex items-center gap-2">
        {["all", "unread", "read"].map((tab) => (
          <Button
            key={tab}
            variant={statusFilter === tab ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setStatusFilter(tab);
              setLimit(50);
            }}
            className="capitalize text-xs"
          >
            {tab}
          </Button>
        ))}
      </div>
      <Panel>
        <ul className="divide-y divide-border">
          {notifications.length === 0 ? (
            <li className="px-4 py-8 text-center text-muted-foreground">No notifications found</li>
          ) : (
            notifications.map((n) => (
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
                  <button
                    onClick={() => deleteMutation.mutate(n.id)}
                    className="text-muted-foreground hover:text-destructive p-1"
                    title="Delete notification"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </li>
            ))
          )}
        </ul>
        {notifications.length < total && (
          <div className="p-4 border-t border-border text-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLimit((prev) => prev + 50)}
            >
              Load more ({total - notifications.length} remaining)
            </Button>
          </div>
        )}
      </Panel>
    </PageBody>
  );
}
