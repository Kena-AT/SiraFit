import path from "node:path";
import { pathToFileURL } from "node:url";
import { careerOpsRoot } from "@/lib/sirafit";
import { normalizeTextKey as fallbackKey } from "./normalize-text-key.mjs";

/**
 * ACL for the core's `normalizeTextKey` (tracker-parse.mjs) â€” the shared
 * matching/dedup key helper that scan.mjs and tracker-parse.mjs use (#2569).
 *
 * DERIVED, NOT COPIED (#2369, #2666). The web used to reimplement this with
 * `[^a-z0-9]`, which deletes every non-ASCII letter: "NestlÃ©" keyed to "nestl",
 * "Å koda" to "koda" and "æ—¥æœ¬é›»ç”£" to the empty string. Two companies could then
 * collide after stripping and a genuinely new offer got suppressed as "already
 * evaluated" â€” a job the user never saw, with no signal.
 *
 * We can't `import` it statically: the core lives in the USER's checkout,
 * resolved at runtime via careerOpsRoot(), and is not a build dependency of this
 * app. So we import it dynamically per resolved root and cache the module â€”
 * keyed by path, and NEVER caching a failure (the lesson from #2590, where a
 * cached fallback pinned stale definitions for the process lifetime).
 *
 * Consequence, by design: the web keys with the normalizeTextKey of the user's
 * OWN core, so web dedup always matches their CLI dedup. Version skew is
 * semantic, and that's the correct behaviour â€” not a bug to paper over.
 *
 * Client components cannot use this ACL (Node-only). They import the Unicode-safe
 * mirror from normalize-text-key.mjs instead â€” same algorithm, parity-tested
 * against the core so [^a-z0-9] cannot creep back in.
 */

type NormalizeTextKey = (value: unknown, separator?: string) => string;

const modCache = new Map<string, NormalizeTextKey>();

let warned = false;

/** Resolve the core's normalizeTextKey for the current root, or the fallback. */
export async function getNormalizeTextKey(): Promise<NormalizeTextKey> {
  const file = path.join(careerOpsRoot(), "tracker-parse.mjs");
  const hit = modCache.get(file);
  if (hit) return hit;
  try {
    const mod = await import(/* webpackIgnore: true */ pathToFileURL(file).href);
    const fn = mod?.normalizeTextKey;
    if (typeof fn === "function") {
      modCache.set(file, fn); // only successes are cached (#2590)
      return fn;
    }
    if (!warned) {
      warned = true;
      console.warn(
        `[SiraFit] ${file} has no normalizeTextKey export â€” company matching falls back to a local Unicode-safe key. Update SiraFit to keep web dedup identical to CLI dedup.`,
      );
    }
  } catch {
    if (!warned) {
      warned = true;
      console.warn(
        `[SiraFit] could not load ${file} â€” company matching falls back to a local Unicode-safe key. Update SiraFit to keep web dedup identical to CLI dedup.`,
      );
    }
  }
  return fallbackKey;
}

