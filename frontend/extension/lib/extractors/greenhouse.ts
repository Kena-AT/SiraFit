import { CapturedJob } from "../../types/job";
import { JobExtractor } from "./base";

export class GreenhouseExtractor implements JobExtractor {
  matches(url: string, document: Document): boolean {
    return url.includes("boards.greenhouse.io") || !!document.querySelector('meta[property="og:url"][content*="greenhouse.io"]');
  }

  extract(url: string, document: Document): CapturedJob | null {
    const title = document.querySelector("h1.app-title")?.textContent?.trim() || "";
    const company = document.querySelector("span.company-name")?.textContent?.trim()?.replace(/at\s+/i, "") || "";
    const location = document.querySelector("div.location")?.textContent?.trim() || "";
    const description = document.querySelector("div#content")?.innerHTML || "";

    if (!title) return null;

    return {
      sourceUrl: url,
      applyUrl: url,
      sourcePlatform: "greenhouse",
      title,
      company,
      location,
      description
    };
  }
}
