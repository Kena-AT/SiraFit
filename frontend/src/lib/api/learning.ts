import { apiFetch } from "./client";

export interface PlanItem {
  type: "learning_resource" | "project_template";
  id: string;
  skill_id?: string;
  skills?: string[];
  title: string;
  provider?: string;
  resource_type?: string;
  difficulty?: string;
  estimated_minutes?: number;
  url?: string;
}

export interface GapToPlanResponse {
  missing_skills: string[];
  plan_items: PlanItem[];
}

export async function getGapToPlan(jobId: string): Promise<GapToPlanResponse> {
  const res = await apiFetch(`/api/v1/learning/gap-to-plan/${jobId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to fetch gap-to-plan roadmap" }));
    throw new Error(err.detail || "Failed to fetch gap-to-plan roadmap");
  }
  return res.json();
}
