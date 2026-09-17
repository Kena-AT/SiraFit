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

export type ResumeVersionSource = "base" | "tailored" | "revert";

export interface ResumeVersion {
  id: string;
  resume_id: string;
  version_number: number;
  content: string;
  template: string | null;
  job_id: string | null;
  parent_version_id: string | null;
  source_type: ResumeVersionSource;
  job_title?: string | null;
  job_company?: string | null;
  tailoring_notes: string | null;
  score: number | null;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  updated_at: string | null;
}

export interface ResumeGenerationRequest {
  job_id: string;
  parent_version_id?: string | null;
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

// --- Resume Diff Types ---

export interface DiffSummary {
  added: number;
  removed: number;
  changed: number;
}

export interface StringListDiff {
  added: string[];
  removed: string[];
  preserved: string[];
}

export interface TextDiff {
  from_text: string | null;
  to_text: string | null;
  changed: boolean;
}

export interface ExperienceItemDiff {
  key: string;
  status: "added" | "removed" | "modified" | "unchanged";
  company: string;
  title: string;
  period_from: string | null;
  period_to: string | null;
  location_from: string | null;
  location_to: string | null;
  bullets_added: string[];
  bullets_removed: string[];
  bullets_preserved: string[];
}

export interface ProjectItemDiff {
  name: string;
  status: "added" | "removed" | "modified" | "unchanged";
  description_from: string | null;
  description_to: string | null;
  url_from: string | null;
  url_to: string | null;
}

export interface EducationItemDiff {
  key: string;
  status: "added" | "removed" | "modified" | "unchanged";
  institution: string;
  degree: string;
  field_of_study_from: string | null;
  field_of_study_to: string | null;
  period_from: string | null;
  period_to: string | null;
}

export interface ResumeDiffSections {
  summary: TextDiff;
  skills: StringListDiff;
  experience: ExperienceItemDiff[];
  projects: ProjectItemDiff[];
  education: EducationItemDiff[];
}

export interface ResumeDiffResponse {
  from_version_id: string;
  to_version_id: string;
  from_version_number: number;
  to_version_number: number;
  has_changes: boolean;
  summary: DiffSummary;
  sections: ResumeDiffSections;
}
