import { CapturedJob } from "../types/job";
import { getExtensionToken } from "./auth";

const API_BASE = "http://localhost:8000/api/v1";

export async function fetchAgentStatus() {
  const token = await getExtensionToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_BASE}/agent/status`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error("Agent status error", err);
    return null;
  }
}

export async function importCapturedJob(job: CapturedJob) {
  const token = await getExtensionToken();
  if (!token) throw new Error("Not authenticated");

  const res = await fetch(`${API_BASE}/agent/import`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(job)
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Failed to import job");
  }

  return await res.json();
}
