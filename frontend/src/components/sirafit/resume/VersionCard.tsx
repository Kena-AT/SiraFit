import React from "react";
import type { ResumeVersion } from "@/types/resume";
import { ScorePill, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";

interface VersionCardProps {
  version: ResumeVersion;
  isSelectedForCompare: boolean;
  isActive: boolean;
  onSelect: () => void;
  onToggleCompare: () => void;
  onRevertClick: () => void;
  isReverting?: boolean;
}

export const VersionCard: React.FC<VersionCardProps> = ({
  version,
  isSelectedForCompare,
  isActive,
  onSelect,
  onToggleCompare,
  onRevertClick,
  isReverting = false,
}) => {
  const getSourceBadge = () => {
    switch (version.source_type) {
      case "base":
        return <Tag className="bg-blue-500/10 text-blue-500 border-blue-500/20 font-medium">Base</Tag>;
      case "tailored":
        return <Tag className="bg-purple-500/10 text-purple-500 border-purple-500/20 font-medium">Tailored</Tag>;
      case "revert":
        return <Tag className="bg-amber-500/10 text-amber-500 border-amber-500/20 font-medium">Reverted</Tag>;
      default:
        return <Tag>{version.source_type}</Tag>;
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`group relative rounded-lg border p-3.5 transition-all cursor-pointer ${
        isActive
          ? "border-[color:var(--brand)] bg-muted/40 shadow-sm"
          : "border-border hover:border-border/80 hover:bg-muted/20"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={isSelectedForCompare}
            onChange={(e) => {
              e.stopPropagation();
              onToggleCompare();
            }}
            aria-label={`Select version v${version.version_number} for comparison`}
            className="h-4 w-4 rounded border-border text-[color:var(--brand)] focus:ring-[color:var(--brand)] cursor-pointer"
          />
          <div className="font-mono text-sm font-semibold">v{version.version_number}</div>
          {getSourceBadge()}
        </div>

        {version.score !== null && version.score !== undefined && (
          <ScorePill value={version.score} />
        )}
      </div>

      {version.job_title && (
        <div className="mt-2 text-xs font-medium text-foreground/90 truncate">
          {version.job_title}
          {version.job_company && (
            <span className="text-muted-foreground font-normal"> · {version.job_company}</span>
          )}
        </div>
      )}

      {version.tailoring_notes && (
        <div className="mt-1 text-[11px] text-muted-foreground line-clamp-2 italic">
          {version.tailoring_notes}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between pt-2 border-t border-border/50 text-[11px] text-muted-foreground">
        <span>{new Date(version.created_at).toLocaleDateString()}</span>

        <div className="flex items-center gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity">
          <Button
            size="sm"
            variant="ghost"
            className="h-6 px-2 text-[11px] text-muted-foreground hover:text-foreground"
            onClick={(e) => {
              e.stopPropagation();
              onRevertClick();
            }}
            disabled={isReverting}
          >
            Revert to this
          </Button>
        </div>
      </div>
    </div>
  );
};
