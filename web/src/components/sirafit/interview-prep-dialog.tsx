"use client";

import { useState } from "react";
import { Sparkles, Copy, Check, Target, Lightbulb, X } from "lucide-react";
import type { InterviewPrepResult, InterviewQuestion } from "@/lib/sirafit-engine";

export interface InterviewPrepDialogProps {
  prep: InterviewPrepResult;
  open: boolean;
  onClose: () => void;
}

export function InterviewPrepDialog({ prep, open, onClose }: InterviewPrepDialogProps) {
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  if (!open) return null;

  const handleCopy = (q: InterviewQuestion, idx: number) => {
    const text = `Q: ${q.question}\nTarget Skill: ${q.focusSkill}\nKey points:\n${q.idealAnswerPoints.map((p) => `- ${p}`).join('\n')}`;
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="w-full max-w-2xl rounded-2xl border border-border bg-surface p-6 shadow-xl space-y-5 animate-terminal-popup max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between border-b border-border pb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Sparkles className="size-4 text-brand" />
              <h3 className="text-base font-semibold text-foreground">
                SiraFit Targeted Interview Prep
              </h3>
            </div>
            <p className="text-xs text-muted">
              Role: <strong className="text-foreground">{prep.role}</strong> at <strong className="text-foreground">{prep.company}</strong>
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted hover:bg-surface-hover hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="space-y-4">
          {prep.questions.map((q, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-brand/10 border border-brand/20 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-brand">
                      {q.difficulty}
                    </span>
                    <span className="text-xs font-semibold text-foreground flex items-center gap-1">
                      <Target className="size-3 text-muted" /> {q.focusSkill}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-foreground leading-snug">{q.question}</h4>
                </div>

                <button
                  type="button"
                  onClick={() => handleCopy(q, idx)}
                  className="rounded-md border border-border p-1.5 text-xs text-muted hover:bg-surface hover:text-foreground transition-colors shrink-0"
                  title="Copy question & talking points"
                >
                  {copiedIdx === idx ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
                </button>
              </div>

              <div className="space-y-1.5 pl-3 border-l-2 border-brand/40 text-xs text-muted">
                <div className="font-semibold text-foreground text-[11px] flex items-center gap-1">
                  <Lightbulb className="size-3 text-amber-500" /> Talking Points & Scoring Keys:
                </div>
                <ul className="space-y-1 list-disc pl-4">
                  {q.idealAnswerPoints.map((pt, pIdx) => (
                    <li key={pIdx}>{pt}</li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end pt-2 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-brand px-4 py-2 text-xs font-medium text-brand-foreground hover:opacity-90"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
