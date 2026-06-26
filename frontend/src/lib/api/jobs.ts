import type { JobImportData, ImportResult, JobImportRecord } from "@/types/job";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const importJobs = async (data: JobImportData): Promise<ImportResult> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
  });
  if (!response.ok) {
    throw new Error('Failed to fetch import history');
  }
  return response.json();
};

export const getImportDetail = async (importId: string): Promise<ImportResult> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/import/${importId}`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch import details');
  }
  return response.json();
};

export const getJobs = async (skip = 0, limit = 100) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs?skip=${skip}&limit=${limit}`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch jobs');
  }
  return response.json();
};

export const getJob = async (jobId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch job');
  }
  return response.json();
};
