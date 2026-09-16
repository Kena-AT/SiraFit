import { Profile } from "@/types/profile";
import { apiFetch } from "./client";

/**
 * Date fields the backend types as Optional[date]; Pydantic rejects "" and
 * free-text like "2021 – Present", so empty values must be sent as null.
 */
const DATE_FIELDS = ["start_date", "end_date", "issue_date", "expiration_date"] as const;

// Server-generated fields that ProfileUpdate does not accept.
const STRIP_KEYS = ["id", "user_id", "created_at", "updated_at"];

type AnyItem = Record<string, unknown> & { id?: string };

function normalizeItems(items?: readonly unknown[] | null): AnyItem[] {
  if (!items) return [];
  return items.map((raw) => {
    const copy: AnyItem = { ...(raw as AnyItem) };
    delete copy.id;
    for (const field of DATE_FIELDS) {
      const v = copy[field];
      if (v === "" || v == null) copy[field] = null;
    }
    return copy;
  });
}

function extractErrorDetail(err: any, fallback: string): string {
  if (!err) return fallback;
  if (typeof err.detail === "string") return err.detail;
  if (Array.isArray(err.detail) && err.detail.length > 0) {
    const first = err.detail[0];
    const loc = Array.isArray(first.loc) ? first.loc.join(".") : "";
    return first.msg ? `${loc}: ${first.msg}` : fallback;
  }
  return fallback;
}

export async function getProfile(): Promise<Profile> {
  const response = await apiFetch("/api/v1/profiles/me");
  if (!response.ok) {
    throw new Error("Failed to fetch profile");
  }
  return response.json();
}

export async function updateProfile(profile: Profile): Promise<Profile> {
  const body: Record<string, unknown> = { ...profile };
  for (const key of STRIP_KEYS) delete body[key];
  body.experiences = normalizeItems(profile.experiences);
  body.educations = normalizeItems(profile.educations);
  body.skills = normalizeItems(profile.skills);
  body.projects = normalizeItems(profile.projects);
  body.certifications = normalizeItems(profile.certifications);

  const response = await apiFetch("/api/v1/profiles/me", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(extractErrorDetail(err, "Failed to update profile"));
  }
  return response.json();
}

/**
 * Rewrite a resume achievement bullet with AI via the backend's
 * multi-provider fallback chain. Throws with a user-friendly message.
 */
export async function polishBullet(text: string): Promise<string> {
  const response = await apiFetch("/api/v1/profiles/me/polish-bullet", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(extractErrorDetail(err, "AI polish is unavailable right now"));
  }
  const data = await response.json();
  return data.polished as string;
}

// --- Sprint 2: Version History ---

export interface ProfileVersionSummary {
  id: string;
  version: number;
  created_at: string | null;
  summary: string;
}

export async function getProfileHistory(): Promise<ProfileVersionSummary[]> {
  const response = await apiFetch("/api/v1/profiles/me/history");
  if (!response.ok) {
    throw new Error("Failed to fetch profile history");
  }
  return response.json();
}

export async function revertProfileToVersion(versionId: string): Promise<Profile> {
  const response = await apiFetch(`/api/v1/profiles/me/revert/${versionId}`, {
    method: "PUT",
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(extractErrorDetail(err, "Failed to revert profile"));
  }
  return response.json();
}
