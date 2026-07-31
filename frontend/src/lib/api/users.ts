import { apiFetch } from "./client";

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface NotificationPreferences {
  email_job_matches: boolean;
  email_daily_summary: boolean;
  push_notifications: boolean;
  email_new_opportunities: boolean;
}

export interface ResumeDefaults {
  default_template: string;
  auto_tailor_enabled: boolean;
  export_format: string;
}

export interface AIProviderKeys {
  anthropic_key?: string | null;
  openai_key?: string | null;
  grok_key?: string | null;
  mistral_key?: string | null;
  nvidia_key?: string | null;
}

export interface AIProviderKeysRead {
  anthropic_configured: boolean;
  openai_configured: boolean;
  grok_configured: boolean;
  mistral_configured: boolean;
  nvidia_configured: boolean;
}

export interface DeviceSession {
  id: number;
  device_name: string;
  ip_address?: string | null;
  is_active: boolean;
  last_seen?: string | null;
  created_at?: string | null;
}

export interface ExportUserData {
  profile: Record<string, unknown>;
  applications: Record<string, unknown>[];
  resumes: Record<string, unknown>[];
  cover_letters: Record<string, unknown>[];
  preferences: Record<string, unknown>;
  exported_at: string;
}

// --- Password ---

export async function changePassword(
  data: PasswordChangeRequest,
): Promise<{ message: string }> {
  const response = await apiFetch("/api/v1/users/me/password", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to change password");
  }
  return response.json();
}

// --- Notification Preferences ---

export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  const response = await apiFetch("/api/v1/users/me/preferences/notifications");
  if (!response.ok) {
    throw new Error("Failed to fetch notification preferences");
  }
  return response.json();
}

export async function updateNotificationPreferences(
  prefs: Partial<NotificationPreferences>,
): Promise<NotificationPreferences> {
  const response = await apiFetch("/api/v1/users/me/preferences/notifications", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(prefs),
  });
  if (!response.ok) {
    throw new Error("Failed to update notification preferences");
  }
  return response.json();
}

// --- Resume Defaults ---

export async function getResumeDefaults(): Promise<ResumeDefaults> {
  const response = await apiFetch("/api/v1/users/me/preferences/resume");
  if (!response.ok) {
    throw new Error("Failed to fetch resume defaults");
  }
  return response.json();
}

export async function updateResumeDefaults(
  prefs: Partial<ResumeDefaults>,
): Promise<ResumeDefaults> {
  const response = await apiFetch("/api/v1/users/me/preferences/resume", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(prefs),
  });
  if (!response.ok) {
    throw new Error("Failed to update resume defaults");
  }
  return response.json();
}

// --- AI Provider Keys ---

export async function getAIProviderKeys(): Promise<AIProviderKeysRead> {
  const response = await apiFetch("/api/v1/users/me/preferences/ai-keys");
  if (!response.ok) {
    throw new Error("Failed to fetch AI provider keys");
  }
  return response.json();
}

export async function updateAIProviderKeys(
  keys: Partial<AIProviderKeys>,
): Promise<AIProviderKeysRead> {
  const response = await apiFetch("/api/v1/users/me/preferences/ai-keys", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(keys),
  });
  if (!response.ok) {
    throw new Error("Failed to update AI provider keys");
  }
  return response.json();
}

// --- Devices ---

export async function getDevices(): Promise<DeviceSession[]> {
  const response = await apiFetch("/api/v1/users/me/devices");
  if (!response.ok) {
    throw new Error("Failed to fetch devices");
  }
  return response.json();
}

export async function revokeDevice(deviceId: number): Promise<{ message: string }> {
  const response = await apiFetch(`/api/v1/users/me/devices/${deviceId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to revoke device");
  }
  return response.json();
}

// --- Data Export & Account Deletion ---

export async function exportUserData(): Promise<ExportUserData> {
  const response = await apiFetch("/api/v1/users/me/export");
  if (!response.ok) {
    throw new Error("Failed to export data");
  }
  return response.json();
}

export async function deleteAccount(): Promise<{ message: string }> {
  const response = await apiFetch("/api/v1/users/me", {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete account");
  }
  return response.json();
}
