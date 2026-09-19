import { apiFetch } from "./client";

export interface SalaryBenchmark {
  role: string;
  currency: string;
  period: string;
  sample_size: number;
  min_p50: number | null;
  max_p50: number | null;
  min_p25: number | null;
  max_p75: number | null;
}

export interface SkillGapItem {
  skill_id: string | null;
  skill: string;
  frequency: number;
  percentage: number;
  priority: boolean;
}

export interface SkillsGapResponse {
  analyzed_jobs: number;
  current_skill_count: number;
  skills: SkillGapItem[];
}

export interface StageInsight {
  stage: string;
  entered_count: number;
  progressed_count: number;
  dropped_count: number;
  drop_off_rate: number | null;
  median_duration_hours: number | null;
  duration_sample_size: number;
}

export interface StallInsightsResponse {
  total_applications: number;
  stages: StageInsight[];
  longest_median_stage: string | null;
  highest_drop_off_stage: string | null;
}

export interface FunnelItem {
  stage: string;
  count: number;
}

export interface TopTechItem {
  skill: string;
  count: number;
}

export interface LegacySkillGapItem {
  skill: string;
  demand_frequency: number;
  impact_score: number;
}

export interface ExpandedMetricsResponse {
  total_applications: number;
  applications_this_week?: number;
  applications_last_week?: number;
  applications_trend?: string;
  interview_rate: number;
  avg_response_time_days: number;
  offer_rate: number;
  conversion_funnel: FunnelItem[];
  rejection_stages: FunnelItem[];
  skill_coverage: Array<{ skill: string; you: number; market: number }>;
  market_demand: Array<{ role: string; demand: number; postings: number; change: string }>;
  top_technologies: TopTechItem[];
  salary_medians: Record<string, number>;
  skill_gaps: LegacySkillGapItem[];
  salary_benchmarks: SalaryBenchmark[];
  skills_gap_analysis?: SkillsGapResponse | null;
  stall_insights?: StallInsightsResponse | null;
  schema_version?: number;
  generated_at: string;
}

export const getAnalyticsMetrics = async (): Promise<ExpandedMetricsResponse> => {
  const response = await apiFetch("/api/v1/analytics/metrics");
  if (!response.ok) throw new Error("Failed to fetch analytics metrics");
  return response.json();
};

export const downloadAnalyticsExport = async (format = "xlsx"): Promise<void> => {
  const response = await apiFetch(`/api/v1/analytics/export?format=${format}`);
  if (!response.ok) throw new Error("Failed to export analytics report");

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `sirafit_analytics_export.${format}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};
