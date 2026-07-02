import type { Resume, ResumeVersion } from "@/types/resume";
import { apiFetch } from "./client";

// --- Resumes ---

export const getResumes = async (): Promise<Resume[]> => {
  const response = await apiFetch("/api/v1/resumes/");
  if (!response.ok) {
    throw new Error("Failed to fetch resumes");
  }
  return response.json();
};

export const getResume = async (id: string): Promise<Resume> => {
  const response = await apiFetch(`/api/v1/resumes/${id}`);
  if (!response.ok) {
    throw new Error("Failed to fetch resume");
  }
  return response.json();
};

export const createResume = async (data: {
  title: string;
  content: string;
  is_primary?: boolean;
  application_id?: string;
}): Promise<Resume> => {
  const response = await apiFetch("/api/v1/resumes/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to create resume" }));
    throw new Error(err.detail || "Failed to create resume");
  }
  return response.json();
};

export const updateResume = async (
  id: string,
  data: Partial<Resume>
): Promise<Resume> => {
  const response = await apiFetch(`/api/v1/resumes/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to update resume" }));
    throw new Error(err.detail || "Failed to update resume");
  }
  return response.json();
};

export const deleteResume = async (id: string): Promise<void> => {
  const response = await apiFetch(`/api/v1/resumes/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete resume");
  }
};

// --- Resume Versions ---

export const getResumeVersions = async (resumeId: string): Promise<ResumeVersion[]> => {
  const response = await apiFetch(`/api/v1/resumes/${resumeId}/versions`);
  if (!response.ok) {
    throw new Error("Failed to fetch resume versions");
  }
  return response.json();
};

export const createResumeVersion = async (
  resumeId: string,
  data: {
    content: string;
    template?: string;
    job_id?: string;
    tailoring_notes?: string;
    score?: number;
    status?: string;
  }
): Promise<ResumeVersion> => {
  const response = await apiFetch(`/api/v1/resumes/${resumeId}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to create version" }));
    throw new Error(err.detail || "Failed to create version");
  }
  return response.json();
};

// --- AI Resume Generation ---

export const generateResume = async (
  resumeId: string,
  params: {
    job_id: string;
    template?: string;
  }
): Promise<ResumeVersion> => {
  const queryParams = new URLSearchParams();
  queryParams.append("job_id", params.job_id);
  if (params.template) {
    queryParams.append("template", params.template);
  }

  const response = await apiFetch(
    `/api/v1/resumes/${resumeId}/generate?${queryParams.toString()}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    }
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to generate resume" }));
    throw new Error(err.detail || "Failed to generate resume");
  }
  return response.json();
};
