import { CapturedJob } from "../../types/job";
import { JobExtractor } from "./base";

export class LeverExtractor implements JobExtractor {
  matches(url: string, document: Document): boolean {
    return url.includes("jobs.lever.co") || !!document.querySelector('meta[property="og:url"][content*="lever.co"]');
  }

  extract(url: string, document: Document): CapturedJob | null {
    const title = document.querySelector(".posting-headline h2")?.textContent?.trim() || "";
    const company = document.title.split("-")[0]?.trim() || "";
    const location = document.querySelector(".sort-by-time")?.textContent?.trim() || "";
    const description = document.querySelector(".posting-page-content")?.innerHTML || "";

    if (!title) return null;

    return {
      sourceUrl: url,
      applyUrl: document.querySelector('a.postings-btn[href*="apply"]')?.getAttribute("href") || url,
      sourcePlatform: "lever",
      title,
      company,
      location,
      description
    };
  }
}
