import { useEffect, useState } from "react";
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
          // Keep polling if still pending or processing (max 60 attempts = ~90s)
          setPollCount((prev) => {
            if (prev < 60) {
              timer = setTimeout(poll, 1500);
            }
            return prev + 1;
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
            {!isTerminal && (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
            )}
            <span className="text-sm font-medium capitalize">
              {sourceType} import: {isTerminal ? status : "Processing..."}
            </span>
          </div>
          <StatusPill status={status} />
        </div>

        {!isTerminal && (
          <div className="w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-1.5 animate-pulse rounded-full bg-foreground transition-all duration-300"
              style={{ width: `${Math.min(25 + pollCount * 10, 95)}%` }}
            />
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
