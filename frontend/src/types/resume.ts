// Resume types
export interface Resume {
  id: string;
  user_id: string;
  title: string;
  content: string;
  pdf_url: string | null;
  is_primary: boolean;
  application_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResumeVersion {
  id: string;
  resume_id: string;
  version_number: number;
  content: string;
  template: string | null;
  job_id: string | null;
  tailoring_notes: string | null;
  score: number | null;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  updated_at: string | null;
}

export interface ResumeGenerationRequest {
  job_id: string;
  template: string;
  provider?: string;
  model?: string;
}

export interface TailoredResumeData {
  name: string;
  email: string;
  phone: string | null;
  location: string | null;
  linkedin: string | null;
  github: string | null;
  website: string | null;
  summary: string;
  experience: {
    title: string;
    company: string;
    location: string | null;
    period: string;
    bullets: string[];
  }[];
  projects: {
    name: string;
    description: string;
    url: string | null;
  }[];
  skills: string[];
  education: {
    institution: string;
    degree: string;
    field_of_study: string | null;
    period: string;
  }[];
}
