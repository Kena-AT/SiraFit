import { apiFetch } from "./client";

// Types for Sprint 9
export interface ApplicationNote {
  id: string;
  application_id: string;
  body: string;
  author?: string | null;
  pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApplicationContact {
  id: string;
  application_id: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  role: string;
  company?: string | null;
  linkedin?: string | null;
  notes?: string | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApplicationEvent {
  id: string;
  application_id: string;
  event_type: string;
  title: string;
  description?: string | null;
  event_metadata?: Record<string, unknown> | null;
  occurred_at: string;
  created_at: string;
}

export interface StatusTransitionRequest {
  to_status: string;
}

// Applications API
export const getApplications = async () => {
  const response = await apiFetch("/api/v1/applications");
  if (!response.ok) throw new Error("Failed to fetch applications");
  return response.json();
};

export const createApplication = async (jobId: string) => {
  const response = await apiFetch("/api/v1/applications", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to create application" }));
    throw new Error(err.detail || "Failed to create application");
  }
  return response.json();
};

export const getApplication = async (applicationId: string) => {
  const response = await apiFetch(`/api/v1/applications/${applicationId}`);
  if (!response.ok) throw new Error("Failed to fetch application");
  return response.json();
};

export const transitionApplicationStatus = async (applicationId: string, toStatus: string) => {
  const response = await apiFetch(`/api/v1/applications/${applicationId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to_status: toStatus }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Invalid status transition" }));
    throw new Error(err.detail || "Invalid status transition");
  }
  return response.json();
};

// Notes API
export const getApplicationNotes = async (applicationId: string): Promise<ApplicationNote[]> => {
  const response = await apiFetch(`/api/v1/applications/${applicationId}/notes`);
  if (!response.ok) throw new Error("Failed to fetch notes");
  return response.json();
};

export const createApplicationNote = async (applicationId: string, body: string, author?: string, pinned?: boolean): Promise<ApplicationNote> => {
  const response = await apiFetch(`/api/v1/applications/${applicationId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ body, author, pinned }),
  });
  if (!response.ok) throw new Error("Failed to create note");
  return response.json();
};

export const updateApplicationNote = async (noteId: string, body?: string, pinned?: boolean): Promise<ApplicationNote> => {
  const response = await apiFetch(`/api/v1/applications/notes/${noteId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ body, pinned }),
  });
  if (!response.ok) throw new Error("Failed to update note");
  return response.json();
};

export const deleteApplicationNote = async (noteId: string): Promise<void> => {
  const response = await apiFetch(`/api/v1/applications/notes/${noteId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete note");
};

// Contacts API
export const getApplicationContacts = async (applicationId: string): Promise<ApplicationContact[]> => {
  const response = await apiFetch(`/api/v1/applications/${applicationId}/contacts`);
  if (!response.ok) throw new Error("Failed to fetch contacts");
  return response.json();
};

export const createApplicationContact = async (
  applicationId: string,
  contact: {
    name: string;
    email?: string;
    phone?: string;
    role?: string;
    company?: string;
    linkedin?: string;
    notes?: string;
    is_primary?: boolean;
  }
): Promise<ApplicationContact> => {
  const response = await apiFetch(`/api/v1/applications/${applicationId}/contacts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(contact),
  });
  if (!response.ok) throw new Error("Failed to create contact");
  return response.json();
};

export const updateApplicationContact = async (
  contactId: string,
  contact: Partial<ApplicationContact>
): Promise<ApplicationContact> => {
  const response = await apiFetch(`/api/v1/applications/contacts/${contactId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(contact),
  });
  if (!response.ok) throw new Error("Failed to update contact");
  return response.json();
};

export const deleteApplicationContact = async (contactId: string): Promise<void> => {
  const response = await apiFetch(`/api/v1/applications/contacts/${contactId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete contact");
};

// Timeline API
export const getUserTimeline = async (limit = 100): Promise<ApplicationEvent[]> => {
  const response = await apiFetch(`/api/v1/applications/timeline?limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch timeline");
  return response.json();
};

export const getApplicationEvents = async (applicationId: string): Promise<ApplicationEvent[]> => {
  const response = await apiFetch(`/api/v1/applications/${applicationId}/events`);
  if (!response.ok) throw new Error("Failed to fetch events");
  return response.json();
};