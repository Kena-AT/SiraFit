import { apiFetch } from "./client";

export type BatchOperationType = "analyze" | "score" | "tag" | "archive";
export type BatchStatus = "pending" | "running" | "completed" | "failed" | "partial" | "cancelled";

export interface BatchItemResult {
  status: "success" | "error";
  result?: unknown;
  error?: string;
}

export interface BatchJob {
  id: string;
  user_id: string;
  operation_type: BatchOperationType;
  status: BatchStatus;
  total_items: number;
  processed_items: number;
  succeeded_items: number;
  failed_items: number;
  payload: Record<string, unknown>;
  result_summary: Record<string, BatchItemResult>;
  cancel_requested: boolean;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BatchJobListResponse {
  jobs: BatchJob[];
  total: number;
  skip: number;
  limit: number;
}

export interface BatchJobCreateInput {
  operation_type: BatchOperationType;
  job_ids: string[];
  params?: Record<string, unknown>;
}

export const getBatchJobs = async (params?: {
  status?: string;
  operation_type?: string;
}): Promise<BatchJobListResponse> => {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.operation_type) search.set("operation_type", params.operation_type);
  const qs = search.toString();
  const response = await apiFetch(`/api/v1/batch${qs ? `?${qs}` : ""}`);
  if (!response.ok) throw new Error("Failed to fetch batch jobs");
  return response.json();
};

export const getBatchJob = async (id: string): Promise<BatchJob> => {
  const response = await apiFetch(`/api/v1/batch/${id}`);
  if (!response.ok) throw new Error("Failed to fetch batch job");
  return response.json();
};

export const createBatchJob = async (input: BatchJobCreateInput): Promise<BatchJob> => {
  const response = await apiFetch("/api/v1/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to create batch job" }));
    throw new Error(err.detail || "Failed to create batch job");
  }
  return response.json();
};

export const retryBatchJob = async (id: string): Promise<BatchJob> => {
  const response = await apiFetch(`/api/v1/batch/${id}/retry`, { method: "POST" });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to retry batch job" }));
    throw new Error(err.detail || "Failed to retry batch job");
  }
  return response.json();
};

export const cancelBatchJob = async (id: string): Promise<BatchJob> => {
  const response = await apiFetch(`/api/v1/batch/${id}/cancel`, { method: "POST" });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to cancel batch job" }));
    throw new Error(err.detail || "Failed to cancel batch job");
  }
  return response.json();
};
