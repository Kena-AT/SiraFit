export interface JobData {
  id?: string;
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
  import_status?: "imported" | "duplicate" | "failed";
  status?: "imported" | "duplicate" | "failed";
  error?: string | null;
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
  errors?: string[];
  error?: string | null;
  partial?: boolean;
  processed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ImportResult {
  import_record: JobImportRecord;
  jobs: JobData[];
  errors: string[];
  scrape_method?: "scrapling" | "heuristic" | "async";
  scrape_duration_ms?: number;
  fields_extracted?: number;
  source_platform?: string;
}

export interface JobImportData {
  source_type: "url" | "description" | "csv";
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
  status: "pending" | "processing" | "done" | "failed";
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

export interface RankedJob {
  job: Job;
  match_score: JobMatchScore | null;
}

export interface RankedJobListResponse {
  jobs: RankedJob[];
  total: number;
}

// --- Sprint 9 Application Types ---

export interface JobApplication {
  id: string;
  user_id: string;
  job_id: string;
  status: string;
  stage: number;
  general_notes: string | null;
  score: number | null;
  score_reason: string | null;
  created_at: string;
  updated_at: string;
  job?: {
    id: string;
    title: string;
    company: string;
    location?: string;
    salary_min?: number;
    salary_max?: number;
    tags?: string[];
  };
  events?: ApplicationEvent[];
  resumes?: unknown[];
}

export interface ApplicationEvent {
  id: string;
  application_id: string;
  event_type: string;
  title: string;
  description: string | null;
  event_metadata: Record<string, unknown> | null;
  occurred_at: string;
  created_at: string;
}

export interface ApplicationNote {
  id: string;
  application_id: string;
  body: string;
  author: string | null;
  pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApplicationContact {
  id: string;
  application_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  role: string;
  company: string | null;
  linkedin: string | null;
  notes: string | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface SessionImportPayload {
  cookies: Record<string, string>;
  headers?: Record<string, string>;
  user_agent?: string;
  expires_at?: string;
  consent_confirmed: boolean;
}

export interface SessionValidationResult {
  valid: boolean;
  platform: string;
  message: string;
}

export interface UserSessionRecord {
  platform: string;
  stored_at: string;
  expires_at: string | null;
  last_used_at: string | null;
}
