import type { JobImportData, ImportResult, JobImportRecord } from "@/types/job";
import { apiFetch } from "./client";

export const importJobs = async (data: JobImportData): Promise<ImportResult> => {
  const response = await apiFetch('/api/v1/jobs/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to import jobs' }));
    throw new Error(err.detail || 'Failed to import jobs');
  }
  return response.json();
};

export const getImportHistory = async (skip = 0, limit = 50): Promise<JobImportRecord[]> => {
  const response = await apiFetch(`/api/v1/jobs/import/history?skip=${skip}&limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch import history');
  }
  return response.json();
};

export const getImportDetail = async (importId: string): Promise<ImportResult> => {
  const response = await apiFetch(`/api/v1/jobs/import/${importId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch import details');
  }
  return response.json();
};

export interface JobSearchParams {
  skip?: number;
  limit?: number;
  search?: string;
  company?: string;
  location?: string;
  source?: string;
  tags?: string;
  min_salary?: number;
  max_salary?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const getJobs = async (params: JobSearchParams = {}) => {
  const queryParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      queryParams.append(key, value.toString());
    }
  });
  
  const response = await apiFetch(`/api/v1/jobs?${queryParams.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch jobs');
  }
  return response.json();
};

export const getJob = async (jobId: string) => {
  const response = await apiFetch(`/api/v1/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch job');
  }
  return response.json();
};

export const triggerAnalysis = async (jobId: string, forceRefresh = false) => {
  const response = await apiFetch(`/api/v1/jobs/${jobId}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force_refresh: forceRefresh }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to trigger analysis' }));
    throw new Error(err.detail || 'Failed to trigger analysis');
  }
  return response.json();
};

export const getJobAnalysis = async (jobId: string) => {
  const response = await apiFetch(`/api/v1/jobs/${jobId}/analysis`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error('Failed to fetch analysis');
  return response.json();
};

export const getMatchScore = async (jobId: string) => {
  const response = await apiFetch(`/api/v1/jobs/${jobId}/match-score`);
  if (!response.ok) {
    throw new Error('Failed to fetch match score');
  }
  return response.json();
};

