import { apiFetch } from "./client";

export interface DashboardActivity {
  id: string;
  action: string;
  entity_type?: string | null;
  created_at: string;
  details?: Record<string, unknown> | null;
}

export interface DashboardStats {
  active_applications: number;
  resumes_generated: number;
  jobs_scored: number;
  total_jobs: number;
  upcoming_followups_count: number;
  recent_activity: DashboardActivity[];
}

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiFetch("/api/v1/dashboard/stats");
  if (!response.ok) throw new Error("Failed to fetch dashboard stats");
  return response.json();
};

export interface MarketPulseTag {
  tag: string;
  count: number;
  pct: number;
}

export interface MarketPulseResponse {
  total_jobs_analyzed: number;
  top_tags: MarketPulseTag[];
}

export const getMarketPulse = async (): Promise<MarketPulseResponse> => {
  const response = await apiFetch("/api/v1/dashboard/market-pulse");
  if (!response.ok) throw new Error("Failed to fetch market pulse");
  return response.json();
};

export interface BriefingResponse {
  briefing: string;
  date: string;
}

/**
 * Returns today's AI briefing, or null when unavailable (no key configured /
 * providers down) so callers can fall back to the rule-based action card.
 *
 * Uses a raw fetch (not apiFetch) so that expected non-2xx responses like 503
 * "no AI key configured" are not logged as errors by the shared error handler.
 */
export const getBriefing = async (): Promise<BriefingResponse | null> => {
  try {
    const response = await fetch("/api/v1/dashboard/briefing", {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
};
