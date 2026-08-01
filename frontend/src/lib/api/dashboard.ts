import { apiFetch } from "./client";

export interface DashboardStats {
  active_applications: number;
  resumes_generated: number;
  jobs_scored: number;
  recent_activity: {
    id: string;
    action: string;
    created_at: string;
  }[];
}

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiFetch("/api/v1/dashboard/stats");
  if (!response.ok) throw new Error("Failed to fetch dashboard stats");
  return response.json();
};
