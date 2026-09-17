import { AgentStatus, CandidateProfile, CaptureResult, ExtractedJob } from "./types";

export const DEFAULT_API_BASE = "http://localhost:8000/api/v1";

export class AgentApiClient {
  private apiBase: string;
  private timeoutMs: number;

  constructor(apiBase: string = DEFAULT_API_BASE, timeoutMs: number = 10000) {
    this.apiBase = apiBase.replace(/\/+$/, "");
    this.timeoutMs = timeoutMs;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    token?: string
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${this.apiBase}${endpoint}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorDetail = `HTTP ${response.status} ${response.statusText}`;
        try {
          const errJson = await response.json();
          if (errJson.detail) {
            errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch (_) {}
        throw new Error(errorDetail);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err.name === "AbortError") {
        throw new Error(`Request timed out after ${this.timeoutMs / 1000}s`);
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async getStatus(token: string): Promise<AgentStatus> {
    return this.request<AgentStatus>("/agent/status", { method: "GET" }, token);
  }

  async getProfile(token: string): Promise<CandidateProfile> {
    return this.request<CandidateProfile>("/agent/profile", { method: "GET" }, token);
  }

  async importJob(token: string, payload: ExtractedJob): Promise<CaptureResult> {
    return this.request<CaptureResult>(
      "/agent/import",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      token
    );
  }

  async logout(token: string): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(
      "/agent/logout",
      { method: "POST" },
      token
    );
  }
}
