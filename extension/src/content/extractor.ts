import { ExtractedJob } from "../shared/types";

function generateCaptureId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "cap_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9);
}

function cleanText(text: string | null | undefined): string {
  if (!text) return "";
  return text.replace(/\s+/g, " ").trim();
}

export function extractFromJsonLd(doc: Document): Partial<ExtractedJob> | null {
  const scripts = doc.querySelectorAll('script[type="application/ld+json"]');
  for (const script of Array.from(scripts)) {
    try {
      const raw = script.textContent;
      if (!raw) continue;
      const data = JSON.parse(raw);
      const items = Array.isArray(data) ? data : data["@graph"] ? data["@graph"] : [data];

      for (const item of items) {
        if (item["@type"] === "JobPosting") {
          const title = cleanText(item.title);
          let company = "";
          if (item.hiringOrganization) {
            company = cleanText(
              typeof item.hiringOrganization === "string"
                ? item.hiringOrganization
                : item.hiringOrganization.name
            );
          }

          let location = "";
          if (item.jobLocation) {
            const loc = item.jobLocation;
            if (typeof loc === "string") {
              location = cleanText(loc);
            } else if (loc.address) {
              const addr = loc.address;
              location = cleanText(
                typeof addr === "string"
                  ? addr
                  : [addr.addressLocality, addr.addressRegion, addr.addressCountry]
                      .filter(Boolean)
                      .join(", ")
              );
            }
          }

          let description = item.description || "";
          // Strip HTML in description
          const temp = doc.createElement("div");
          temp.innerHTML = description;
          description = temp.textContent || temp.innerText || description;

          if (title) {
            return {
              title,
              company: company || "Unknown Company",
              location: location || null,
              description: description.trim(),
              extracted_via: "json_ld",
              confidence: 0.95,
            };
          }
        }
      }
    } catch (_) {}
  }
  return null;
}

export function extractFromMetaTags(doc: Document): Partial<ExtractedJob> | null {
  const getMeta = (props: string[]): string => {
    for (const prop of props) {
      const el = doc.querySelector(`meta[property="${prop}"], meta[name="${prop}"]`);
      const content = el?.getAttribute("content");
      if (content) return cleanText(content);
    }
    return "";
  };

  const title = getMeta(["og:title", "twitter:title"]);
  const description = getMeta(["og:description", "twitter:description", "description"]);
  const siteName = getMeta(["og:site_name"]);

  if (title && description) {
    return {
      title,
      company: siteName || "Unknown Company",
      description,
      extracted_via: "generic",
      confidence: 0.75,
    };
  }
  return null;
}

export function extractFromPlatformAdapters(
  doc: Document,
  url: string
): Partial<ExtractedJob> | null {
  const lowerUrl = url.toLowerCase();

  // 1. LinkedIn
  if (lowerUrl.includes("linkedin.com")) {
    const titleEl = doc.querySelector(
      ".jobs-unified-top-card__job-title, .job-details-jobs-unified-top-card__job-title, h1.t-24, .jobs-top-card__job-title"
    );
    const companyEl = doc.querySelector(
      ".jobs-unified-top-card__company-name, .job-details-jobs-unified-top-card__company-name, .jobs-top-card__company-url"
    );
    const locationEl = doc.querySelector(
      ".jobs-unified-top-card__bullet, .job-details-jobs-unified-top-card__bullet, .jobs-unified-top-card__workplace-type"
    );
    const descEl = doc.querySelector(
      "#job-details, .jobs-description__content, .jobs-box__html-content"
    );

    const title = cleanText(titleEl?.textContent);
    if (title) {
      return {
        title,
        company: cleanText(companyEl?.textContent) || "LinkedIn Source",
        location: cleanText(locationEl?.textContent) || null,
        description: (descEl?.textContent || "").trim() || `Job listing for ${title} on LinkedIn`,
        extracted_via: "dom_adapter",
        confidence: 0.9,
      };
    }
  }

  // 2. Greenhouse
  if (lowerUrl.includes("greenhouse.io")) {
    const titleEl = doc.querySelector(".app-title, h1.app-title, h1");
    const companyEl = doc.querySelector(".company-name");
    const locationEl = doc.querySelector(".location");
    const descEl = doc.querySelector("#content, #main");

    const title = cleanText(titleEl?.textContent);
    if (title) {
      return {
        title,
        company: cleanText(companyEl?.textContent) || "Greenhouse Company",
        location: cleanText(locationEl?.textContent) || null,
        description: (descEl?.textContent || "").trim(),
        extracted_via: "dom_adapter",
        confidence: 0.9,
      };
    }
  }

  // 3. Lever
  if (lowerUrl.includes("lever.co")) {
    const titleEl = doc.querySelector(".posting-headline h2, .posting-header h2");
    const teamEl = doc.querySelector(".posting-categories .sort-by-team");
    const locationEl = doc.querySelector(".posting-categories .sort-by-time.posting-category");
    const descEl = doc.querySelector(".section.page-centered:not(.posting-header)");

    const title = cleanText(titleEl?.textContent);
    if (title) {
      return {
        title,
        company: cleanText(teamEl?.textContent) || "Lever Company",
        location: cleanText(locationEl?.textContent) || null,
        description: (descEl?.textContent || "").trim(),
        extracted_via: "dom_adapter",
        confidence: 0.9,
      };
    }
  }

  // 4. Ashby
  if (lowerUrl.includes("ashbyhq.com")) {
    const titleEl = doc.querySelector("h1, [class*='title']");
    const descEl = doc.querySelector("[class*='description'], [class*='JobPosting']");

    const title = cleanText(titleEl?.textContent);
    if (title) {
      return {
        title,
        company: "Ashby Posting",
        location: null,
        description: (descEl?.textContent || "").trim(),
        extracted_via: "dom_adapter",
        confidence: 0.85,
      };
    }
  }

  // 5. Indeed
  if (lowerUrl.includes("indeed.com")) {
    const titleEl = doc.querySelector("h1.jobsearch-JobInfoHeader-title, [data-testid='jobsearch-JobInfoHeader-title']");
    const companyEl = doc.querySelector("[data-testid='inlineHeader-companyName'], .jobsearch-CompanyInfoContainer");
    const locationEl = doc.querySelector("[data-testid='inlineHeader-companyLocation']");
    const descEl = doc.querySelector("#jobDescriptionText");

    const title = cleanText(titleEl?.textContent);
    if (title) {
      return {
        title,
        company: cleanText(companyEl?.textContent) || "Indeed Employer",
        location: cleanText(locationEl?.textContent) || null,
        description: (descEl?.textContent || "").trim(),
        extracted_via: "dom_adapter",
        confidence: 0.9,
      };
    }
  }

  return null;
}

export function extractJobFromDOM(
  doc: Document = document,
  pageUrl: string = typeof window !== "undefined" ? window.location.href : ""
): ExtractedJob {
  // 1. Try JSON-LD
  const jsonLdResult = extractFromJsonLd(doc);
  if (jsonLdResult && jsonLdResult.title && jsonLdResult.description) {
    return {
      capture_id: generateCaptureId(),
      page_url: pageUrl,
      platform: detectPlatformName(pageUrl),
      title: jsonLdResult.title,
      company: jsonLdResult.company || "Unknown Company",
      location: jsonLdResult.location,
      description: jsonLdResult.description,
      extracted_via: "json_ld",
      confidence: jsonLdResult.confidence || 0.95,
      tags: [detectPlatformName(pageUrl)],
    };
  }

  // 2. Try Platform Adapter
  const adapterResult = extractFromPlatformAdapters(doc, pageUrl);
  if (adapterResult && adapterResult.title) {
    return {
      capture_id: generateCaptureId(),
      page_url: pageUrl,
      platform: detectPlatformName(pageUrl),
      title: adapterResult.title,
      company: adapterResult.company || "Unknown Company",
      location: adapterResult.location,
      description: adapterResult.description || `Job posting for ${adapterResult.title}`,
      extracted_via: "dom_adapter",
      confidence: adapterResult.confidence || 0.9,
      tags: [detectPlatformName(pageUrl)],
    };
  }

  // 3. Try Meta Tags
  const metaResult = extractFromMetaTags(doc);
  if (metaResult && metaResult.title && metaResult.description) {
    return {
      capture_id: generateCaptureId(),
      page_url: pageUrl,
      platform: detectPlatformName(pageUrl),
      title: metaResult.title,
      company: metaResult.company || "Unknown Company",
      location: null,
      description: metaResult.description,
      extracted_via: "generic",
      confidence: metaResult.confidence || 0.7,
      tags: [detectPlatformName(pageUrl)],
    };
  }

  // 4. Generic Fallback
  const h1 = doc.querySelector("h1");
  const fallbackTitle = cleanText(h1?.textContent) || cleanText(doc.title) || "Job Listing";
  const mainEl = doc.querySelector("main, article, #content, body");
  const fallbackDesc = (mainEl?.textContent || "").substring(0, 1000).trim();

  return {
    capture_id: generateCaptureId(),
    page_url: pageUrl,
    platform: detectPlatformName(pageUrl),
    title: fallbackTitle,
    company: "Generic Site",
    location: null,
    description: fallbackDesc || `Extracted job from ${pageUrl}`,
    extracted_via: "generic",
    confidence: 0.5,
    tags: [detectPlatformName(pageUrl)],
  };
}

function detectPlatformName(url: string): string {
  const lower = url.toLowerCase();
  if (lower.includes("linkedin.com")) return "linkedin";
  if (lower.includes("greenhouse.io")) return "greenhouse";
  if (lower.includes("lever.co")) return "lever";
  if (lower.includes("ashbyhq.com")) return "ashby";
  if (lower.includes("indeed.com")) return "indeed";
  return "generic";
}
