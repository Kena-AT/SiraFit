import { apiFetch } from "./client";

export interface TopMatchItem {
  company: string;
  role: string;
  match_score: number;
  status: string; // "new" | "saved" | "seen"
}

export interface LandingStatsResponse {
  jobs_ingested_per_day: number;
  ats_sources_polled: number;
  sector_interview_rate: number;
  top_match_queue: TopMatchItem[];
  generated_at: string;
}

export interface HealthStatusResponse {
  frontend: boolean;
  backend: boolean;
  database: boolean;
  deployment: boolean;
  agent_api: {
    connected: boolean;
    source: string; // "env" | "settings_ui" | "none"
    provider?: string;
    error?: string;
  };
  checked_at: string;
  color: string;
  message: string;
}

export const getLandingStats = async (): Promise<LandingStatsResponse> => {
  const response = await apiFetch("/api/v1/stats/landing");
  if (!response.ok) throw new Error("Failed to fetch landing stats");
  return response.json();
};

export const getHealthStatus = async (): Promise<HealthStatusResponse> => {
  const response = await apiFetch("/api/v1/health/status");
  if (!response.ok) throw new Error("Failed to fetch health status");
  return response.json();
};