"use client";

import { useState } from "react";
import { Sparkles, ArrowRight, ShieldCheck, CheckCircle2, AlertTriangle, FileText, Search, Play, HelpCircle } from "lucide-react";
import { Panel } from "@/components/sirafit/bits";
import { MatchScoreCard } from "@/components/sirafit/match-score-card";
import { GapToPlanPanel } from "@/components/sirafit/gap-to-plan-panel";
import { InterviewPrepDialog } from "@/components/sirafit/interview-prep-dialog";
import type { AhEvaluationResult, GapToPlanResult, InterviewPrepResult } from "@/lib/sirafit-engine";

export default function MatchAnalysisPage() {
  const [company, setCompany] = useState("Scale AI");
  const [role, setRole] = useState("Senior Full-Stack / Platform Engineer");
  const [jobDescription, setJobDescription] = useState(
`Scale AI is looking for a Senior Platform Engineer to build scalable evaluation pipelines and developer tooling.
Requirements:
- 4+ years of software engineering experience in Python or TypeScript.
- Strong hands-on experience with React, Next.js, and modern web architectures.
- Experience with Docker, Kubernetes, PostgreSQL, and distributed caching (Redis).
- Familiarity with CI/CD automation, cloud infrastructure (AWS/GCP), and microservices.
- Collaborative mindset, strong ownership, and high velocity execution.`
  );
  const [experienceYears, setExperienceYears] = useState(4);
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<AhEvaluationResult | null>(null);
  const [gapPlan, setGapPlan] = useState<GapToPlanResult | null>(null);
  const [prepResult, setPrepResult] = useState<InterviewPrepResult | null>(null);
  const [prepOpen, setPrepOpen] = useState(false);

  async function handleAnalyze() {
    setEvaluating(true);
    try {
      // 1. Evaluate A-H Match Score
      const res = await fetch("/api/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company,
          jobTitle: role,
          jobDescription,
          experienceYears,
        }),
      });
      const data = await res.json();
      if (data.ok && data.result) {
        setEvalResult(data.result);

        // 2. Fetch Gap to Plan
        const planRes = await fetch("/api/learning", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            candidateSkills: data.result.matchedSkills,
            jobRequirements: [...data.result.matchedSkills, ...data.result.missingSkills],
          }),
        });
        const planData = await planRes.json();
        if (planData.ok) {
          setGapPlan(planData.plan);
        }
      }
    } catch (err) {
      console.error("Evaluation error:", err);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleOpenInterviewPrep() {
    if (!evalResult) return;
    try {
      const res = await fetch("/api/interview-prep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidateSkills: evalResult.matchedSkills,
          jobRequirements: [...evalResult.matchedSkills, ...evalResult.missingSkills],
          company,
          role,
        }),
      });
      const data = await res.json();
      if (data.ok && data.prep) {
        setPrepResult(data.prep);
        setPrepOpen(true);
      }
    } catch (err) {
      console.error("Interview prep error:", err);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="grid h-6 w-6 place-items-center rounded-sm bg-emerald-500 text-[11px] font-bold text-white shadow-xs">
              S
            </div>
            <h1 className="font-display text-2xl tracking-tight text-foreground">
              Match Analysis & Strategic Decision
            </h1>
          </div>
          <p className="mt-1 text-sm text-muted">
            Deterministic SiraFit A-H evaluation engine, skill gap roadmap, and automated interview prep.
          </p>
        </div>

        {evalResult && (
          <button
            type="button"
            onClick={handleOpenInterviewPrep}
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 dark:bg-emerald-500 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:opacity-90 transition-opacity"
          >
            <Sparkles className="size-3.5" />
            Generate Interview Prep
          </button>
        )}
      </div>

      {/* Input Form & Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <Panel title="Listing & Target Parameters">
            <div className="space-y-3.5 text-xs">
              <div>
                <label className="block font-medium text-foreground mb-1">Company Name</label>
                <input
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-foreground focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block font-medium text-foreground mb-1">Target Role</label>
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-foreground focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block font-medium text-foreground mb-1">
                  Candidate Experience: <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">{experienceYears} years</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="12"
                  step="0.5"
                  value={experienceYears}
                  onChange={(e) => setExperienceYears(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>

              <div>
                <label className="block font-medium text-foreground mb-1">Job Description Text</label>
                <textarea
                  rows={8}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface p-2.5 font-mono text-[11px] text-foreground focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
                  placeholder="Paste raw JD text here..."
                />
              </div>

              <button
                type="button"
                onClick={handleAnalyze}
                disabled={evaluating || !jobDescription.trim()}
                className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 dark:bg-emerald-500 py-2.5 text-xs font-semibold text-white shadow-xs hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {evaluating ? (
                  <>
                    <span className="size-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Running A-H Gates & Evaluation...
                  </>
                ) : (
                  <>
                    <Play className="size-3.5 fill-current" />
                    Run Match Evaluation
                  </>
                )}
              </button>
            </div>
          </Panel>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-2 space-y-6">
          {evalResult ? (
            <div className="space-y-6">
              {/* Score & recommendation overview */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <MatchScoreCard
                  score={evalResult.score}
                  maxScore={5.0}
                  recommendation={evalResult.recommendation}
                  breakdown={{
                    "Core Skills": Math.min(100, Math.round((evalResult.matchedSkills.length / Math.max(1, evalResult.matchedSkills.length + evalResult.missingSkills.length)) * 100)),
                    "Experience Match": Math.min(100, Math.round((experienceYears / 4.0) * 100)),
                    "Posting Integrity": evalResult.blocks["Block G (Ghost Job Audit)"].includes("None") ? 95 : 60,
                  }}
                  explanation={evalResult.blocks["Block F (Decision)"]}
                />

                <Panel title="A-H Block Audit Breakdown">
                  <div className="space-y-2.5 text-xs">
                    <div className="flex items-start gap-2">
                      <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold shrink-0">Block A:</span>
                      <span className="text-foreground">{evalResult.blocks["Block A (Match Score)"]}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold shrink-0">Block B:</span>
                      <span className="text-muted">{evalResult.blocks["Block B (Requirements)"]?.notes}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold shrink-0">Block E:</span>
                      <span className="text-muted">{evalResult.blocks["Block E (CV Strategy)"]}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold shrink-0">Block G:</span>
                      <span className="text-muted">{evalResult.blocks["Block G (Ghost Job Audit)"]}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold shrink-0">Block H:</span>
                      <span className="text-muted">{evalResult.blocks["Block H (Work Authorization)"]}</span>
                    </div>
                  </div>
                </Panel>
              </div>

              {/* Gap to plan */}
              {gapPlan && <GapToPlanPanel data={gapPlan} />}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-border p-12 text-center space-y-3">
              <div className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-surface-hover text-muted">
                <Search className="size-6" />
              </div>
              <h3 className="text-base font-semibold text-foreground">Ready to Evaluate Job Fit</h3>
              <p className="max-w-md mx-auto text-xs text-muted leading-relaxed">
                Click <strong>Run Match Evaluation</strong> to compare this job specification against your local profile and CV. The engine will calculate gate checks, skill alignment, and personalized interview questions.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Interview Prep Modal */}
      {prepResult && (
        <InterviewPrepDialog
          prep={prepResult}
          open={prepOpen}
          onClose={() => setPrepOpen(false)}
        />
      )}
    </div>
  );
}
