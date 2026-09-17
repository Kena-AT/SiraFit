export interface Experience {
  id?: string;
  title: string;
  company: string;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
}

export interface Education {
  id?: string;
  institution: string;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  description?: string | null;
}

export interface Skill {
  id?: string;
  name: string;
  category?: string | null;
  proficiency?: string | null;
}

export interface Project {
  id?: string;
  name: string;
  description?: string | null;
  url?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface Certification {
  id?: string;
  name: string;
  issuer: string;
  issue_date?: string | null;
  expiration_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
}

export interface Profile {
  id?: string;
  user_id?: string;
  first_name?: string | null;
  last_name?: string | null;
  headline?: string | null;
  summary?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  website?: string | null;
  linkedin?: string | null;
  github?: string | null;
  revision?: number;
  created_at?: string;
  updated_at?: string;

  experiences: Experience[];
  educations: Education[];
  skills: Skill[];
  projects: Project[];
  certifications: Certification[];
}

export interface ProfileVersionSummary {
  id: string;
  version: number;
  created_at: string | null;
  source: "update" | "revert" | "baseline" | string;
  summary: string;
}

export interface ProfileVersionDetail {
  id: string;
  user_id: string;
  version: number;
  created_at: string | null;
  source: "update" | "revert" | "baseline" | string;
  reverted_from_version_id?: string | null;
  schema_version: number;
  profile: Omit<Profile, "id" | "user_id" | "revision" | "created_at" | "updated_at">;
  summary: string;
}

export class RevisionConflictError extends Error {
  currentRevision: number;
  constructor(message: string, currentRevision: number) {
    super(message);
    this.name = "RevisionConflictError";
    this.currentRevision = currentRevision;
  }
}
