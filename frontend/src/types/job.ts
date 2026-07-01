export interface JobData {
  external_id: string;
  title: string;
  company: string;
  location?: string;
  description?: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  tags: string[];
  url?: string;
  source: string;
  is_duplicate: boolean;
}

export interface Job {
  id: string;
  external_id: string;
  title: string;
  company: string;
  location?: string;
  description?: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  tags: string[];
  url?: string;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  skip: number;
  limit: number;
}

export interface JobImportRecord {
  id: string;
  source: string;
  status: string;
  total_found: number;
  ok_count: number;
  fail_count: number;
  created_at: string;
  updated_at: string;
}

export interface ImportResult {
  import_record: JobImportRecord;
  jobs: JobData[];
  errors: string[];
}

export interface JobImportData {
  source_type: 'url' | 'description' | 'csv';
  data: string;
}

export interface JobAnalysis {
  id: string;
  job_id: string;
  score: number;
  summary: string;
  pros: string[];
  cons: string[];
  skills_gap: string[];
  key_requirements: string[];
  seniority: string | null;
  analysis_version: string | null;
  status: 'pending' | 'processing' | 'done' | 'failed';
  created_at: string;
  updated_at: string | null;
}

export interface JobMatchScore {
  id: string;
  job_id: string;
  user_id: string;
  score: number;
  breakdown: Record<string, number>;
  explanation: string | null;
  created_at: string;
  updated_at: string | null;
}

