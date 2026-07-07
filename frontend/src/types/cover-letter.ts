// Cover letter types

export interface CoverLetter {
  id: string;
  user_id: string;
  resume_id: string | null;
  job_id: string | null;
  title: string;
  body: string;
  tone: string | null;
  template: string | null;
  pdf_url: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface CoverLetterCreate {
  title: string;
  body: string;
  tone?: string;
  template?: string;
  resume_id?: string;
  job_id?: string;
}

export interface CoverLetterUpdate {
  title?: string;
  body?: string;
  tone?: string;
  template?: string;
  status?: string;
}

export interface CoverLetterGenerateRequest {
  job_id: string;
  resume_id?: string;
  tone?: string;
  template?: string;
}
