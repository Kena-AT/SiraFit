import { ChevronDown, ChevronUp, AlertCircle, CheckCircle } from "lucide-react";
import { useState } from "react";

interface BatchItemRowProps {
  itemId: string;
  result: { status: "success" | "error"; result?: unknown; error?: string };
}

export function BatchItemRow({ itemId, result }: BatchItemRowProps) {
  const [expanded, setExpanded] = useState(false);
  const isError = result.status === "error";

  return (
    <tr className={isError ? "bg-destructive/5" : ""}>
      <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground">
        {itemId.slice(0, 8)}…
      </td>
      <td className="px-4 py-3">
        {isError ? (
          <span className="inline-flex items-center gap-1.5 text-destructive text-sm">
            <AlertCircle className="w-3 h-3" /> Failed
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-[color:var(--success)] text-sm">
            <CheckCircle className="w-3 h-3" /> Success
          </span>
        )}
      </td>
      <td className="px-4 py-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-muted-foreground hover:text-foreground text-sm underline"
        >
          {expanded ? "Hide" : "Show"} details
        </button>
      </td>
      <td className="px-4 py-3 text-right">
        {isError && (
          <span className="text-xs text-destructive font-mono">
            {result.error?.slice(0, 80)}…
          </span>
        )}
      </td>
    </tr>
  );
}