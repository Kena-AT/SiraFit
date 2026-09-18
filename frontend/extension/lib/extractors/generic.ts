import { CapturedJob } from "../../types/job";
import { JobExtractor } from "./base";

export class GenericExtractor implements JobExtractor {
  matches(url: string, document: Document): boolean {
    return true;
  }

  extract(url: string, document: Document): CapturedJob | null {
    // 1. Try JSON-LD JobPosting
    const jsonLdScripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
    for (const script of jsonLdScripts) {
      try {
        const data = JSON.parse(script.textContent || "{}");
        // Handle array or single object
        const items = Array.isArray(data) ? data : (data["@graph"] || [data]);
        const job = items.find((item: any) => item["@type"] === "JobPosting");
        if (job) {
          let companyName = "";
          if (job.hiringOrganization) {
            companyName = typeof job.hiringOrganization === "string" ? job.hiringOrganization : job.hiringOrganization.name;
          }
          let locationName = "";
          if (job.jobLocation) {
            const loc = Array.isArray(job.jobLocation) ? job.jobLocation[0] : job.jobLocation;
            if (loc?.address) {
              if (typeof loc.address === "string") locationName = loc.address;
              else locationName = [loc.address.addressLocality, loc.address.addressRegion, loc.address.addressCountry].filter(Boolean).join(", ");
            }
          }
          return {
            sourceUrl: url,
            applyUrl: url,
            sourcePlatform: "generic",
            title: job.title || "",
            company: companyName,
            location: locationName,
            description: job.description || ""
          };
        }
      } catch (e) {}
    }

    // 2. Fallback to OpenGraph / Meta tags
    const title = document.querySelector('meta[property="og:title"]')?.getAttribute("content") || document.title;
    const description = document.querySelector('meta[property="og:description"]')?.getAttribute("content") || 
                       document.querySelector('meta[name="description"]')?.getAttribute("content") || "";

    if (title && !title.toLowerCase().includes("page not found")) {
      return {
        sourceUrl: url,
        sourcePlatform: "generic",
        title: title,
        description: description
      };
    }

    return null;
  }
}
