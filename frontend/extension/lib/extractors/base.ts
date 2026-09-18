import { CapturedJob } from "../../types/job";

export interface JobExtractor {
  matches(url: string, document: Document): boolean;
  extract(url: string, document: Document): CapturedJob | null;
}
