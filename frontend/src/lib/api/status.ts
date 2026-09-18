import { apiFetch } from "./client";

export type SystemHealthState = "healthy" | "degraded" | "failed" | "unknown";

export interface SystemStatusData {
  overall: SystemHealthState;
  api: SystemHealthState;
  database: SystemHealthState;
  redis: SystemHealthState;
  background_jobs: SystemHealthState;
  last_checked: string;
}

export async function fetchSystemStatus(): Promise<SystemStatusData> {
  const res = await apiFetch("/health/system-status");
  return res.json();
}
