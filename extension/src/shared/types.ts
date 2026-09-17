export interface CandidateProfile {
  first_name?: string | null;
  last_name?: string | null;
  full_name?: string | null;
  headline?: string | null;
  summary?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  website?: string | null;
  linkedin?: string | null;
  github?: string | null;
  skills: string[];
}

export interface ExtractedJob {
  capture_id: string;
  page_url: string;
  apply_url?: string | null;
  platform: string;
  title: string;
  company: string;
  location?: string | null;
  description: string;
  salary_raw?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string;
  tags?: string[];
  confidence: number;
  extracted_via: "json_ld" | "dom_adapter" | "generic";
  metadata?: Record<string, any>;
}

export interface CaptureResult {
  success: boolean;
  status: "imported" | "duplicate" | "failed";
  job_id?: string | null;
  import_id: string;
  capture_id: string;
  title: string;
  company: string;
  message: string;
}

export interface AgentStatus {
  connected: boolean;
  user_id?: string;
  user_email?: string;
  user_name?: string | null;
  version?: string;
}

export interface AutofillResult {
  filled_count: number;
  skipped_count: number;
  fields_filled: string[];
}
