import { apiFetch } from "./client";

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  body: string;
  kind: "alert" | "reminder" | "system_event" | "follow_up";
  status: "unread" | "read";
  read_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  skip: number;
  limit: number;
}

export interface UnreadCountResponse {
  count: number;
}

export interface MetricsResponse {
  total_applications: number;
  interview_rate: number;
  avg_response_time_days: number;
  offer_rate: number;
  conversion_funnel: Array<[string, number]>;
  rejection_stages: Array<[string, number]>;
  skill_coverage: Array<{ skill: string; you: number; market: number }>;
  market_demand: Array<{ role: string; demand: number; postings: number; change: string }>;
  top_technologies: Array<[string, number]>;
  salary_medians: Array<[string, string]>;
  skill_gaps?: string[];
  generated_at: string;
}

export interface AnalyticsSnapshot {
  id: string;
  user_id: string;
  snapshot_date: string;
  metrics: MetricsResponse;
  created_at: string;
}

export interface AnalyticsSnapshotListResponse {
  snapshots: AnalyticsSnapshot[];
  total: number;
  skip: number;
  limit: number;
}

export const getNotifications = async (params?: {
  status?: string;
  skip?: number;
  limit?: number;
}): Promise<NotificationListResponse> => {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.skip !== undefined) search.set("skip", params.skip.toString());
  if (params?.limit !== undefined) search.set("limit", params.limit.toString());

  const response = await apiFetch(`/api/v1/notifications?${search}`);
  if (!response.ok) throw new Error("Failed to fetch notifications");
  return response.json();
};

export const getUnreadCount = async (): Promise<UnreadCountResponse> => {
  const response = await apiFetch("/api/v1/notifications/unread-count");
  if (!response.ok) throw new Error("Failed to fetch unread count");
  return response.json();
};

export const markNotificationRead = async (id: string): Promise<Notification> => {
  const response = await apiFetch(`/api/v1/notifications/${id}/read`, {
    method: "POST",
  });
  if (!response.ok) throw new Error("Failed to mark notification as read");
  return response.json();
};

export const markAllNotificationsRead = async (): Promise<{ updated: number }> => {
  const response = await apiFetch("/api/v1/notifications/mark-all-read", {
    method: "POST",
  });
  if (!response.ok) throw new Error("Failed to mark all notifications as read");
  return response.json();
};

export const deleteNotification = async (id: string): Promise<{ message: string }> => {
  const response = await apiFetch(`/api/v1/notifications/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete notification");
  return response.json();
};

export const getAnalyticsMetrics = async (): Promise<MetricsResponse> => {
  const response = await apiFetch("/api/v1/analytics/metrics");
  if (!response.ok) throw new Error("Failed to fetch analytics metrics");
  return response.json();
};

export const createAnalyticsSnapshot = async (): Promise<AnalyticsSnapshot> => {
  const response = await apiFetch("/api/v1/analytics/snapshots", {
    method: "POST",
  });
  if (!response.ok) throw new Error("Failed to create analytics snapshot");
  return response.json();
};

export const getAnalyticsSnapshots = async (params?: {
  skip?: number;
  limit?: number;
}): Promise<AnalyticsSnapshotListResponse> => {
  const search = new URLSearchParams();
  if (params?.skip !== undefined) search.set("skip", params.skip.toString());
  if (params?.limit !== undefined) search.set("limit", params.limit.toString());

  const response = await apiFetch(`/api/v1/analytics/snapshots?${search}`);
  if (!response.ok) throw new Error("Failed to fetch analytics snapshots");
  return response.json();
};

export const getLatestAnalyticsSnapshot = async (): Promise<AnalyticsSnapshot> => {
  const response = await apiFetch("/api/v1/analytics/snapshots/latest");
  if (!response.ok) throw new Error("Failed to fetch latest analytics snapshot");
  return response.json();
};
