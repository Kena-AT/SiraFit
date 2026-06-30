import type { JobImportData, ImportResult, JobImportRecord } from "@/types/job";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const importJobs = async (data: JobImportData): Promise<ImportResult> => {
  return {
    import_record: {
      id: "hist-2",
      user_id: "user-1",
      source: data.source_type,
      source_type: data.source_type,
      status: "completed",
      total_found: 1,
      ok_count: 1,
      fail_count: 0,
      created_at: new Date().toISOString()
    },
    jobs: [
      {
        title: "Mock Job Title",
        company: "Mock Company",
        location: "Mock Location",
        salary_min: 100000,
        salary_max: 150000,
        source: data.source_type,
        is_duplicate: false,
        tags: ["React", "TypeScript"],
        description: "This is a mock job description."
      }
    ],
    errors: []
  };
};

export const getImportHistory = async (skip = 0, limit = 50): Promise<JobImportRecord[]> => {
  return [
    {
      id: "hist-1",
      user_id: "user-1",
      source: "url",
      source_type: "url",
      status: "completed",
      total_found: 5,
      ok_count: 5,
      fail_count: 0,
      created_at: new Date().toISOString()
    }
  ];
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

export const getJobs = async (skip = 0, limit = 100) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs?skip=${skip}&limit=${limit}`, {
    credentials: 'include',
    headers: { ...getAIHeaders() }
  });
  if (!response.ok) {
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
