import { apiFetch } from "./client";

export interface ReportCreate {
  title: string;
  markdown_content: string;
}

export async function generateReportPDF(data: ReportCreate): Promise<Blob> {
  const response = await apiFetch("/api/v1/reports/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate report PDF");
  }
  
  return await response.blob();
}
