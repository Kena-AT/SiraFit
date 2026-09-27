import { apiFetch } from "./client";

export interface InterviewQuestion {
  question: string;
  focus_skill: string;
  ideal_answer_points: string[];
}

export interface InterviewPrepResponse {
  questions: InterviewQuestion[];
  usage_count: number;
  rate_limit: number;
}

export async function generateInterviewPrep(jobId: string): Promise<InterviewPrepResponse> {
  const res = await apiFetch(`/api/v1/interview-prep/${jobId}`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to generate interview prep" }));
    throw new Error(err.detail || "Failed to generate interview prep");
  }
  return res.json();
}
