import { GreenhouseExtractor } from "./greenhouse";
import { LeverExtractor } from "./lever";
import { GenericExtractor } from "./generic";
import { JobExtractor } from "./base";
import { CapturedJob, CaptureValidationResult } from "../../types/job";

const EXTRACTORS: JobExtractor[] = [
  new GreenhouseExtractor(),
  new LeverExtractor(),
  new GenericExtractor()
];

export function extractJobFromPage(url: string, document: Document): CaptureValidationResult | null {
  for (const extractor of EXTRACTORS) {
    if (extractor.matches(url, document)) {
      const data = extractor.extract(url, document);
      if (data) {
        return validateCapture(data);
      }
    }
  }
  return null;
}

function validateCapture(data: CapturedJob): CaptureValidationResult {
  const warnings: string[] = [];
  let confidence: "high" | "medium" | "low" = "high";

  if (!data.title) {
    warnings.push("Title is missing");
    confidence = "low";
  } else if (data.title.length > 200) {
    warnings.push("Title seems unusually long");
    confidence = "low";
  }

  if (!data.company) {
    warnings.push("Company is missing");
    if (confidence === "high") confidence = "medium";
  }

  if (!data.description || data.description.length < 50) {
    warnings.push("Description is missing or too short");
    confidence = "low";
  }

  if (data.sourcePlatform === "generic" && confidence === "high") {
    confidence = "medium"; // Generic extraction is inherently less confident
  }

  return { data, warnings, confidence };
}
