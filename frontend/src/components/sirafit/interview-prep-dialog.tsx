import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  generateInterviewPrep,
  InterviewQuestion,
  InterviewPrepResponse,
} from "@/lib/api/interview_prep";
import { Sparkles, Loader2, Copy, Check, Target, Lightbulb } from "lucide-react";
import { toast } from "sonner";

interface InterviewPrepDialogProps {
  jobId: string;
  jobTitle: string;
  company: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaveToNotes?: (content: string) => void;
}

export function InterviewPrepDialog({
  jobId,
  jobTitle,
  company,
  open,
  onOpenChange,
  onSaveToNotes,
}: InterviewPrepDialogProps) {
  const [prepData, setPrepData] = useState<InterviewPrepResponse | null>(null);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const mutation = useMutation({
    mutationFn: () => generateInterviewPrep(jobId),
    onSuccess: (data) => {
      setPrepData(data);
      toast.success("Interview prep generated!");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to generate interview prep");
    },
  });

  const handleCopyQuestion = (q: InterviewQuestion, idx: number) => {
    const text = `Q: ${q.question}\nTarget Skill: ${q.focus_skill}\nKey points to cover:\n${q.ideal_answer_points.map((pt) => `• ${pt}`).join("\n")}`;
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    toast.success("Copied question & talking points");
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const handleSaveAllToNotes = () => {
    if (!prepData || !onSaveToNotes) return;
    const formatted =
      `### AI Interview Prep for ${jobTitle} (${company})\n\n` +
      prepData.questions
        .map(
          (q, i) =>
            `**Question ${i + 1} (${q.focus_skill})**:\n${q.question}\n\n*Talking Points*:\n${q.ideal_answer_points.map((p) => `- ${p}`).join("\n")}`,
        )
        .join("\n\n---\n\n");
    onSaveToNotes(formatted);
    toast.success("Saved interview prep to application notes");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between gap-3 pr-6">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500 ring-1 ring-indigo-500/20">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <DialogTitle className="text-base font-semibold">
                  AI Interview Prep Coach
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground">
                  {jobTitle} · {company}
                </DialogDescription>
              </div>
            </div>
            {prepData && (
              <span className="rounded-full bg-muted/60 px-2.5 py-0.5 text-[11px] font-mono text-muted-foreground">
                {prepData.usage_count}/{prepData.rate_limit} today
              </span>
            )}
          </div>
        </DialogHeader>

        {!prepData && !mutation.isPending && (
          <div className="py-8 text-center space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted/80 text-muted-foreground">
              <Target className="h-6 w-6" />
            </div>
            <div className="max-w-md mx-auto space-y-1">
              <h4 className="text-sm font-medium">Generate Targeted Interview Questions</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Our AI analyzes your candidate profile against this job description to predict
                technical & behavioral questions specifically designed to test your skill gaps.
              </p>
            </div>
            <Button
              onClick={() => mutation.mutate()}
              className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
            >
              <Sparkles className="h-4 w-4" />
              Generate 3 Prep Questions
            </Button>
          </div>
        )}

        {mutation.isPending && (
          <div className="py-12 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
            <div className="text-center space-y-1">
              <p className="text-sm font-medium">Analyzing skill gaps & formulating questions...</p>
              <p className="text-xs text-muted-foreground">Using your configured AI model</p>
            </div>
          </div>
        )}

        {prepData && (
          <div className="space-y-4 py-2">
            <div className="space-y-3">
              {prepData.questions.map((q, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-border/70 bg-card p-4 space-y-3 shadow-xs transition-colors hover:border-indigo-500/30"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500/15 text-[11px] font-bold text-indigo-500">
                          {idx + 1}
                        </span>
                        <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/20">
                          <Target className="h-3 w-3" /> Focus: {q.focus_skill}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-foreground pt-1 leading-snug">
                        {q.question}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 px-2 text-xs text-muted-foreground hover:text-foreground shrink-0"
                      onClick={() => handleCopyQuestion(q, idx)}
                    >
                      {copiedIdx === idx ? (
                        <Check className="h-3.5 w-3.5 text-emerald-500" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </div>

                  <div className="rounded-lg bg-muted/40 p-3 space-y-1.5 text-xs">
                    <div className="flex items-center gap-1.5 font-medium text-muted-foreground">
                      <Lightbulb className="h-3.5 w-3.5 text-indigo-500" />
                      <span>Ideal Answer & Talking Points</span>
                    </div>
                    <ul className="space-y-1 pl-5 list-disc text-foreground/90">
                      {q.ideal_answer_points.map((pt, pidx) => (
                        <li key={pidx} className="leading-relaxed">
                          {pt}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-border">
              <Button
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending}
              >
                Regenerate
              </Button>
              {onSaveToNotes && (
                <Button
                  size="sm"
                  className="text-xs gap-1.5 bg-foreground text-background hover:bg-foreground/90"
                  onClick={handleSaveAllToNotes}
                >
                  Save to Notes
                </Button>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
