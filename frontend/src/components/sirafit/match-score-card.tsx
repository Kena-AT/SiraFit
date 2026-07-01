import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { JobMatchScore } from "@/types/job";

interface MatchScoreCardProps {
  score: JobMatchScore;
}

function Meter({ value, label }: { value: number; label: string }) {
  const tone =
    value >= 85
      ? "bg-green-500"
      : value >= 70
        ? "bg-yellow-500"
        : "bg-muted-foreground/60";
  const textCls =
    value >= 85
      ? "text-green-600"
      : value >= 70
        ? "text-yellow-600"
        : "text-muted-foreground";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="capitalize text-muted-foreground">{label}</span>
        <span className={`font-mono font-semibold tabular-nums ${textCls}`}>
          {value}%
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full ${tone} rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export const MatchScoreCard: React.FC<MatchScoreCardProps> = ({ score }) => {
  const scoreTone =
    score.score >= 85
      ? "text-green-600"
      : score.score >= 70
        ? "text-yellow-600"
        : "text-muted-foreground";

  return (
    <Card>
      <CardContent className="p-5 space-y-4">
        <div className="text-center">
          <div className={`text-4xl font-bold tabular-nums ${scoreTone}`}>
            {score.score}
            <span className="text-lg font-normal text-muted-foreground">/100</span>
          </div>
          <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
            {score.explanation}
          </p>
        </div>
        <div className="space-y-3 pt-3 border-t border-border">
          {Object.entries(score.breakdown).map(([key, value]) => (
            <Meter key={key} value={value} label={key} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
