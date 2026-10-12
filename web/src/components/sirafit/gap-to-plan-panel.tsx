"use client";

import { CheckCircle2, Sparkles, BookOpen, ExternalLink, Code } from "lucide-react";
import { Panel } from "./bits";
import type { GapToPlanResult } from "@/lib/sirafit-engine";

export interface GapToPlanPanelProps {
  data: GapToPlanResult;
  className?: string;
}

export function GapToPlanPanel({ data, className }: GapToPlanPanelProps) {
  const { missingSkills, planItems } = data;

  if (missingSkills.length === 0) {
    return (
      <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 flex items-center gap-2.5 text-xs text-emerald-600 dark:text-emerald-400">
        <CheckCircle2 className="size-4 shrink-0 text-emerald-500" />
        <span>You match all identified skill requirements for this role! No learning gaps detected.</span>
      </div>
    );
  }

  return (
    <Panel className={className}>
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="flex size-6 items-center justify-center rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Sparkles className="size-3.5" />
          </div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground">
            Gap-to-Plan Action Roadmap
          </h4>
        </div>
        <span className="text-[11px] font-mono text-muted">
          {missingSkills.length} missing skill{missingSkills.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {missingSkills.map((s) => (
          <span
            key={s}
            className="inline-flex items-center rounded-sm bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 text-xs font-medium text-rose-600 dark:text-rose-400 font-mono"
          >
            {s}
          </span>
        ))}
      </div>

      <div className="mt-4 space-y-2.5">
        <div className="text-xs font-semibold text-foreground">Recommended Learning & Projects:</div>
        <div className="grid gap-2 sm:grid-cols-2">
          {planItems.map((item, i) => (
            <div
              key={i}
              className="p-3 rounded-lg border border-border bg-surface-hover/40 flex flex-col justify-between space-y-2"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-[11px] font-semibold text-brand">
                  {item.type === 'project_template' ? <Code className="size-3" /> : <BookOpen className="size-3" />}
                  <span className="capitalize">{item.skill}</span>
                  <span className="ml-auto text-[10px] text-muted border border-border rounded px-1">
                    ~{item.estimatedHours}h
                  </span>
                </div>
                <div className="text-xs font-medium text-foreground">{item.title}</div>
                <p className="text-[11px] text-muted leading-relaxed">{item.description}</p>
              </div>

              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] text-brand hover:underline font-medium pt-1"
                >
                  Open Resource <ExternalLink className="size-3" />
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
}
