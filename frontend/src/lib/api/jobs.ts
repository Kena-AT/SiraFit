import type { JobImportData, ImportResult, JobImportRecord } from "@/types/job";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const importJobs = async (data: JobImportData): Promise<ImportResult> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAIHeaders() },
    credentials: 'include',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to import jobs' }));
    throw new Error(err.detail || 'Failed to import jobs');
  }
  return response.json();
};

export const getImportHistory = async (skip = 0, limit = 50): Promise<JobImportRecord[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/import/history?skip=${skip}&limit=${limit}`, {
    credentials: 'include',
    headers: { ...getAIHeaders() },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch import history');
  }
  return response.json();
};

import { getAIHeaders } from "./headers";

export const getImportDetail = async (importId: string): Promise<ImportResult> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/import/${importId}`, {
    credentials: 'include',
    headers: { ...getAIHeaders() }
  });
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
  
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs?${queryParams.toString()}`, {
    credentials: 'include',
    headers: { ...getAIHeaders() }
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      window.location.href = '/login';
      throw new Error('Session expired. Please log in again.');
    }
    throw new Error('Failed to fetch jobs');
  }
  return response.json();
};

export const getJob = async (jobId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
    credentials: 'include',
    headers: { ...getAIHeaders() }
  });
  if (!response.ok) {
    throw new Error('Failed to fetch job');
  }
  return response.json();
};

export const triggerAnalysis = async (jobId: string, forceRefresh = false) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAIHeaders() },
    credentials: 'include',
    body: JSON.stringify({ force_refresh: forceRefresh }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to trigger analysis' }));
    throw new Error(err.detail || 'Failed to trigger analysis');
  }
  return response.json();
};

export const getJobAnalysis = async (jobId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/analysis`, {
    credentials: 'include',
    headers: { ...getAIHeaders() },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error('Failed to fetch analysis');
  return response.json();
};

