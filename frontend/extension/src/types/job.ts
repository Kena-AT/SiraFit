export interface CapturedJob {
  sourceUrl: string;
  applyUrl?: string;
  sourcePlatform: string;
  title: string;
  company?: string;
  location?: string;
  description?: string;
  technologies?: string[];
}

export interface CaptureValidationResult {
  data: CapturedJob;
  warnings: string[];
  confidence: "high" | "medium" | "low";
}
