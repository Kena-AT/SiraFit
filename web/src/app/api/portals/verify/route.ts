import { execFile } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { careerOpsRoot, rootScript } from "@/lib/sirafit";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 120;

// Orchestrates the core's verify-portals.mjs (#1016) â€” the SAME ATS-slug
// validator the CLI uses. Catches the silent 404s that quietly drop a company
// from every future scan (= lost offers). We parse its console output; we do NOT
// reimplement the validation.
const STATUS: Record<string, "live" | "empty" | "broken" | "skipped"> = {
  "âœ…": "live",
  "ðŸŸ¡": "empty",
  "âŒ": "broken",
  "âž–": "skipped",
};

export async function GET() {
  const root = careerOpsRoot();
  const verifyPortals = rootScript("verify-portals");
  if (!fs.existsSync(verifyPortals)) {
    return Response.json({ available: false, configured: false, companies: [] });
  }
  if (!fs.existsSync(path.join(root, "portals.yml"))) {
    return Response.json({ available: true, configured: false, companies: [] });
  }

  const stdout = await new Promise<string>((resolve) => {
    execFile(
      "node",
      [verifyPortals],
      { cwd: root, timeout: 110_000, maxBuffer: 4 * 1024 * 1024 },
      (_e, out, err) => resolve((out || "") + (err || "")),
    );
  });

  const companies: { name: string; status: string; detail: string }[] = [];
  for (const line of stdout.split("\n")) {
    const m = line.match(/^\s*(âœ…|ðŸŸ¡|âŒ|âž–)\s+(.+?)\s+â€”\s+(.*)$/);
    if (m) companies.push({ name: m[2].trim(), status: STATUS[m[1]] ?? "unknown", detail: m[3].trim() });
  }
  return Response.json({ available: true, configured: true, companies });
}

