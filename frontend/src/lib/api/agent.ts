import { apiFetch } from "./client";

export interface ExtensionTokenCreate {
  name?: string;
  expires_days?: number;
}

export interface ExtensionTokenOut {
  token: string;
  token_type: string;
  name: string;
  expires_at: string;
}

export async function issueExtensionToken(data?: ExtensionTokenCreate): Promise<ExtensionTokenOut> {
  const response = await apiFetch("/api/v1/agent/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data || {}),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to issue extension token");
  }
  return response.json();
}
