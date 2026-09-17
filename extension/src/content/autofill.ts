import { AutofillResult, CandidateProfile } from "../shared/types";

type FieldType =
  | "first_name"
  | "last_name"
  | "full_name"
  | "email"
  | "phone"
  | "location"
  | "linkedin"
  | "github"
  | "website"
  | "headline"
  | "summary";

const SENSITIVE_PATTERN =
  /password|ssn|social.*security|credit.*card|salary.*expectation|desired.*salary|veteran|disability|gender|race|ethnicity/i;

function getAssociatedLabelText(el: HTMLElement, doc: Document): string {
  let labelText = "";
  if (el.id) {
    const label = doc.querySelector(`label[for="${el.id}"]`);
    if (label && label.textContent) {
      labelText += " " + label.textContent;
    }
  }
  const parentLabel = el.closest("label");
  if (parentLabel && parentLabel.textContent) {
    labelText += " " + parentLabel.textContent;
  }
  const ariaLabel = el.getAttribute("aria-label") || "";
  if (ariaLabel) {
    labelText += " " + ariaLabel;
  }
  return labelText.toLowerCase().trim();
}

export function classifyField(el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement, doc: Document): FieldType | null {
  const name = (el.name || "").toLowerCase();
  const id = (el.id || "").toLowerCase();
  const autocomplete = (el.getAttribute("autocomplete") || "").toLowerCase();
  const placeholder = (el.getAttribute("placeholder") || "").toLowerCase();
  const label = getAssociatedLabelText(el, doc);
  const type = el instanceof HTMLInputElement ? el.type.toLowerCase() : "";

  // Skip sensitive or non-candidate fields
  if (
    SENSITIVE_PATTERN.test(name) ||
    SENSITIVE_PATTERN.test(id) ||
    SENSITIVE_PATTERN.test(label)
  ) {
    return null;
  }

  // 1. Check Autocomplete
  if (autocomplete === "given-name") return "first_name";
  if (autocomplete === "family-name") return "last_name";
  if (autocomplete === "name") return "full_name";
  if (autocomplete === "email") return "email";
  if (autocomplete === "tel") return "phone";
  if (autocomplete === "address-level2" || autocomplete === "city") return "location";
  if (autocomplete === "url") return "website";

  // 2. Email
  if (
    type === "email" ||
    name.includes("email") ||
    id.includes("email") ||
    label.includes("email")
  ) {
    return "email";
  }

  // 3. Phone
  if (
    type === "tel" ||
    /phone|mobile|telephone|cell/i.test(name) ||
    /phone|mobile|telephone|cell/i.test(id) ||
    /phone|mobile|telephone|cell/i.test(label)
  ) {
    return "phone";
  }

  // 4. LinkedIn
  if (
    name.includes("linkedin") ||
    id.includes("linkedin") ||
    placeholder.includes("linkedin.com") ||
    label.includes("linkedin")
  ) {
    return "linkedin";
  }

  // 5. GitHub
  if (
    name.includes("github") ||
    id.includes("github") ||
    placeholder.includes("github.com") ||
    label.includes("github")
  ) {
    return "github";
  }

  // 6. Portfolio / Website
  if (
    (type === "url" && !name.includes("linkedin") && !name.includes("github")) ||
    /website|portfolio|blog|personal.*site/i.test(name) ||
    /website|portfolio|blog|personal.*site/i.test(id) ||
    /website|portfolio|blog|personal.*site/i.test(label)
  ) {
    return "website";
  }

  // 7. First Name
  if (
    /first.*name|fname|given.*name/i.test(name) ||
    /first.*name|fname|given.*name/i.test(id) ||
    /first.*name|given.*name/i.test(label)
  ) {
    return "first_name";
  }

  // 8. Last Name
  if (
    /last.*name|lname|surname|family.*name/i.test(name) ||
    /last.*name|lname|surname|family.*name/i.test(id) ||
    /last.*name|surname|family.*name/i.test(label)
  ) {
    return "last_name";
  }

  // 9. Full Name
  if (
    /(^|_)full_?name|applicant_?name|candidate_?name|(^|_)name$/i.test(name) ||
    /(^|_)full_?name|applicant_?name|candidate_?name|(^|_)name$/i.test(id) ||
    /full.*name|legal.*name|your.*name/i.test(label)
  ) {
    return "full_name";
  }

  // 10. Location / City
  if (
    /location|city|current.*city|residence/i.test(name) ||
    /location|city|current.*city|residence/i.test(id) ||
    /location|city|current.*location/i.test(label)
  ) {
    return "location";
  }

  // 11. Headline / Summary
  if (/headline|title/i.test(name) || /headline/i.test(label)) {
    return "headline";
  }
  if (
    (el instanceof HTMLTextAreaElement || type === "textarea") &&
    (/summary|about/i.test(name) || /summary|about.*you/i.test(label))
  ) {
    return "summary";
  }

  return null;
}

export function setNativeValue(
  el: HTMLInputElement | HTMLTextAreaElement,
  value: string
): void {
  const prototype =
    el instanceof HTMLInputElement
      ? window.HTMLInputElement.prototype
      : window.HTMLTextAreaElement.prototype;

  const descriptor = Object.getOwnPropertyDescriptor(prototype, "value");
  if (descriptor && descriptor.set) {
    descriptor.set.call(el, value);
  } else {
    el.value = value;
  }

  // Dispatch events to satisfy React, Vue, Angular, TanStack synthetic event handlers
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
  el.dispatchEvent(new Event("blur", { bubbles: true }));
}

export function autofillApplicationForm(
  doc: Document = document,
  profile: CandidateProfile,
  overwriteExisting: boolean = false
): AutofillResult {
  const formElements = doc.querySelectorAll<
    HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
  >("input, textarea, select");

  let filledCount = 0;
  let skippedCount = 0;
  const fieldsFilled: string[] = [];

  const profileMap: Record<FieldType, string | null | undefined> = {
    first_name: profile.first_name,
    last_name: profile.last_name,
    full_name:
      profile.full_name ||
      [profile.first_name, profile.last_name].filter(Boolean).join(" ") ||
      null,
    email: profile.email,
    phone: profile.phone,
    location: profile.location,
    linkedin: profile.linkedin,
    github: profile.github,
    website: profile.website,
    headline: profile.headline,
    summary: profile.summary,
  };

  for (const el of Array.from(formElements)) {
    // Skip file inputs, hidden inputs, buttons, submit
    if (el instanceof HTMLInputElement) {
      if (
        ["file", "hidden", "submit", "button", "reset", "image"].includes(
          el.type.toLowerCase()
        )
      ) {
        continue;
      }
    }

    // Do not overwrite existing content unless requested
    if (!overwriteExisting && el.value && el.value.trim().length > 0) {
      skippedCount++;
      continue;
    }

    const fieldType = classifyField(el, doc);
    if (!fieldType) continue;

    const valueToFill = profileMap[fieldType];
    if (!valueToFill) continue;

    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      setNativeValue(el, valueToFill);
      filledCount++;
      if (!fieldsFilled.includes(fieldType)) {
        fieldsFilled.push(fieldType);
      }
    } else if (el instanceof HTMLSelectElement) {
      // Find matching option
      const lowerVal = valueToFill.toLowerCase().trim();
      let matched = false;
      for (let i = 0; i < el.options.length; i++) {
        const opt = el.options[i];
        if (
          opt.text.toLowerCase().includes(lowerVal) ||
          opt.value.toLowerCase().includes(lowerVal)
        ) {
          el.selectedIndex = i;
          el.dispatchEvent(new Event("change", { bubbles: true }));
          filledCount++;
          matched = true;
          if (!fieldsFilled.includes(fieldType)) {
            fieldsFilled.push(fieldType);
          }
          break;
        }
      }
    }
  }

  return {
    filled_count: filledCount,
    skipped_count: skippedCount,
    fields_filled: fieldsFilled,
  };
}
