"use client";

import React from "react";
import { Panel } from "./bits";

export interface MatchScoreCardProps {
  score: number;
  maxScore?: number;
  recommendation?: "PROCEED" | "LOW_FRICTION" | "SKIP";
  breakdown?: Record<string, number>;
  explanation?: string;
}

function Meter({ value, label }: { value: number; label: string }) {
  const tone =
    value >= 85 ? "bg-emerald-500" : value >= 70 ? "bg-amber-500" : "bg-muted/60";
  const textCls =
    value >= 85
      ? "text-emerald-600 dark:text-emerald-400"
      : value >= 70
        ? "text-amber-600 dark:text-amber-400"
        : "text-muted";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="capitalize text-muted">{label}</span>
        <span className={`font-mono font-semibold tabular-nums ${textCls}`}>{value}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-hover border border-border/50">
        <div
          className={`h-full ${tone} rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export const MatchScoreCard: React.FC<MatchScoreCardProps> = ({
  score,
  maxScore = 5.0,
  recommendation = "PROCEED",
  breakdown = { "Core Skills": 88, "Experience Match": 80, "Domain Alignment": 75 },
  explanation,
}) => {
  const isFiveScale = maxScore <= 5;
  const normalized = isFiveScale ? (score / 5) * 100 : score;
  const scoreTone =
    normalized >= 80
      ? "text-emerald-600 dark:text-emerald-400"
      : normalized >= 60
        ? "text-amber-600 dark:text-amber-400"
        : "text-rose-600 dark:text-rose-400";

  return (
    <Panel className="space-y-4">
      <div className="text-center">
        <div className="text-xs uppercase tracking-wider text-muted font-medium mb-1">
          SiraFit Match Score
        </div>
        <div className={`text-4xl font-extrabold tabular-nums ${scoreTone}`}>
          {score.toFixed(1)}
          <span className="text-base font-normal text-muted">/{maxScore.toFixed(1)}</span>
        </div>
        <div className="mt-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-surface-hover border border-border">
          Recommendation: <strong className="ml-1 text-foreground">{recommendation}</strong>
        </div>
        {explanation && (
          <p className="mt-2 text-xs text-muted leading-relaxed max-w-sm mx-auto">{explanation}</p>
        )}
      </div>

      <div className="space-y-3 pt-3 border-t border-border">
        {Object.entries(breakdown).map(([key, val]) => (
          <Meter key={key} value={val} label={key} />
        ))}
      </div>
    </Panel>
  );
};
