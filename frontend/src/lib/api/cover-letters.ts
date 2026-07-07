import type { CoverLetter, CoverLetterCreate, CoverLetterUpdate, CoverLetterGenerateRequest } from "@/types/cover-letter";
import { apiFetch } from "./client";

// --- Cover Letters ---

export const getCoverLetters = async (): Promise<CoverLetter[]> => {
  const response = await apiFetch("/api/v1/cover-letters/");
  if (!response.ok) {
    throw new Error("Failed to fetch cover letters");
  }
  return response.json();
};

export const getCoverLetter = async (id: string): Promise<CoverLetter> => {
  const response = await apiFetch(`/api/v1/cover-letters/${id}`);
  if (!response.ok) {
    throw new Error("Failed to fetch cover letter");
  }
  return response.json();
};

export const createCoverLetter = async (data: CoverLetterCreate): Promise<CoverLetter> => {
  const response = await apiFetch("/api/v1/cover-letters/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to create cover letter" }));
    throw new Error(err.detail || "Failed to create cover letter");
  }
  return response.json();
};

export const updateCoverLetter = async (id: string, data: CoverLetterUpdate): Promise<CoverLetter> => {
  const response = await apiFetch(`/api/v1/cover-letters/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to update cover letter" }));
    throw new Error(err.detail || "Failed to update cover letter");
  }
  return response.json();
};

export const deleteCoverLetter = async (id: string): Promise<void> => {
  const response = await apiFetch(`/api/v1/cover-letters/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete cover letter");
  }
};

// --- Generation ---

export const generateCoverLetter = async (
  data: CoverLetterGenerateRequest
): Promise<{ cover_letter_id: string; status: string; message: string }> => {
  const response = await apiFetch(`/api/v1/cover-letters/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to generate cover letter" }));
    throw new Error(err.detail || "Failed to generate cover letter");
  }
  return response.json();
};

export const regenerateCoverLetter = async (
  letterId: string,
  data: CoverLetterGenerateRequest
): Promise<{ cover_letter_id: string; status: string; message: string }> => {
  const response = await apiFetch(`/api/v1/cover-letters/${letterId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to regenerate cover letter" }));
    throw new Error(err.detail || "Failed to regenerate cover letter");
  }
  return response.json();
};

export const exportCoverLetterPdf = (letterId: string): string => {
  return `/api/v1/cover-letters/${letterId}/export?format=pdf`;
};
