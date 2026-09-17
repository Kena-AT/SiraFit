import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Panel, StatusPill } from "@/components/sirafit/bits";
import { getImportDetail } from "@/lib/api/jobs";
import type { ImportResult } from "@/types/job";

interface ImportProgressCardProps {
  importId: string;
  sourceType?: string;
  initialStatus?: string;
  onCompleted?: (result: ImportResult) => void;
  onError?: (err: Error) => void;
}

export function ImportProgressCard({
  importId,
  sourceType = "URL",
  initialStatus = "processing",
  onCompleted,
  onError,
}: ImportProgressCardProps) {
  const [status, setStatus] = useState<string>(initialStatus);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [pollCount, setPollCount] = useState(0);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let timer: any = null;

    const poll = async () => {
      try {
        const detail = await getImportDetail(importId);
        if (cancelled) return;

        setResult(detail);
        const currentStatus = detail.import_record.status;
        setStatus(currentStatus);

        if (currentStatus === "completed" || currentStatus === "failed") {
          onCompleted?.(detail);
        } else {
          // Poll every 2.5s up to 180s (3 minutes = 72 attempts)
          setPollCount((prev) => {
            if (prev < 72) {
              timer = setTimeout(poll, 2500);
              return prev + 1;
            } else {
              setTimedOut(true);
              return prev;
            }
          });
        }
      } catch (err: any) {
        if (!cancelled) {
          onError?.(err);
        }
      }
    };

    poll();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [importId]);

  const isTerminal = status === "completed" || status === "failed";

  return (
    <Panel title="Import progress">
      <div className="space-y-4 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {!isTerminal && !timedOut && (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
            )}
            <span className="text-sm font-medium capitalize">
              {sourceType} import: {isTerminal ? status : timedOut ? "Background Processing" : "Processing..."}
            </span>
          </div>
          <StatusPill status={timedOut && !isTerminal ? "processing" : status} />
        </div>

        {!isTerminal && !timedOut && (
          <div className="w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-1.5 animate-pulse rounded-full bg-foreground transition-all duration-300"
              style={{ width: `${Math.min(15 + pollCount * 1.2, 95)}%` }}
            />
          </div>
        )}

        {timedOut && !isTerminal && (
          <div className="rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
            <p>
              This import is taking longer than usual and is continuing in the background.
            </p>
            <Link
              to="/jobs/history"
              className="mt-1.5 inline-block font-medium text-foreground underline"
            >
              View Import History →
            </Link>
          </div>
        )}

        {result && (
          <div className="flex flex-wrap gap-4 pt-2 text-xs text-muted-foreground">
            <span>
              Found: <strong className="text-foreground">{result.import_record.total_found}</strong>
            </span>
            <span>
              Imported:{" "}
              <strong className="text-emerald-600">{result.import_record.ok_count}</strong>
            </span>
            {result.import_record.fail_count > 0 && (
              <span>
                Failed:{" "}
                <strong className="text-destructive">{result.import_record.fail_count}</strong>
              </span>
            )}
            {result.scrape_method && (
              <span className="capitalize">Method: {result.scrape_method}</span>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
