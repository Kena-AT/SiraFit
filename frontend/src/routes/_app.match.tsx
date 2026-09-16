import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getJobsWithScores, getMatchScore } from "@/lib/api/jobs";
import type { Job, JobMatchScore } from "@/types/job";

interface JobWithScore {
  job: Job;
  score: JobMatchScore | null;
}

export const Route = createFileRoute("/_app/match")({
  head: () => ({ meta: [{ title: "Match analysis · SiraFit" }] }),
  component: MatchAnalysis,
});

function MatchAnalysis() {
  const [items, setItems] = useState<JobWithScore[]>([]);
  const [scoring, setScoring] = useState(false);
  const [showAll, setShowAll] = useState(false);

  // Single batched call: every job pre-joined with its stored match score,
  // replacing the old N+1 pattern (one getCachedMatchScore request per job).
  const {
    data,
    isLoading,
    error: queryError,
  } = useQuery({
    queryKey: ["jobs-with-scores"],
    queryFn: () => getJobsWithScores({ limit: 200 }),
  });

  // Seed `items` from the single response (replacing the per-job fetch loop).
  useEffect(() => {
    if (!data) return;
    const mapped: JobWithScore[] = data.jobs.map((r) => ({
      job: r.job,
      score: r.match_score ?? null,
    }));
    mapped.sort((a, b) => (b.score?.score ?? -1) - (a.score?.score ?? -1));
    setItems(mapped);
  }, [data]);

  // Re-score all jobs (writes to DB) — only on explicit user action.
  const handleScoreAll = async () => {
    setScoring(true);
    try {
      const updated: JobWithScore[] = await Promise.all(
        items.map(async ({ job }) => {
          try {
            const score = await getMatchScore(job.id);
            return { job, score };
          } catch {
            return { job, score: null };
          }
        }),
      );
      updated.sort((a, b) => (b.score?.score ?? -1) - (a.score?.score ?? -1));
      setItems(updated);
    } finally {
      setScoring(false);
    }
  };

  // Compute skill gaps: count job tags for jobs whose skill score is below
  // full coverage, weighted by how severe the gap is (0% counts 2x).
  const skillGapCounts: Record<string, number> = {};
  for (const { job, score } of items) {
    if (!score) continue;
    const skillScore = score.breakdown?.skills ?? 100;
    if (skillScore < 100) {
      const weight = skillScore === 0 ? 2 : 1;
      for (const tag of job.tags || []) {
        const key = tag.toLowerCase();
        skillGapCounts[key] = (skillGapCounts[key] || 0) + weight;
      }
    }
  }
  const topGaps = Object.entries(skillGapCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  const unscoredCount = items.filter((i) => !i.score).length;
  const displayItems = showAll ? items : items.slice(0, 20);
  const error = queryError ? (queryError as Error).message : null;

  if (isLoading) {
    return (
      <PageBody>
        <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
          Loading matches...
        </div>
      </PageBody>
    );
  }

  if (error) {
    return (
      <PageBody>
        <PageHeader
          eyebrow="Intelligence"
          title="Match analysis"
          description="Deterministic fit between your master profile and every job in pipeline."
        />
        <div className="px-4 py-8 text-sm text-destructive">{error}</div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Intelligence"
        title="Match analysis"
        description="Deterministic fit between your master profile and every job in pipeline."
        actions={
          <Button onClick={handleScoreAll} disabled={scoring} variant="outline">
            {scoring
              ? "Scoring…"
              : unscoredCount > 0
                ? `Score ${unscoredCount} unscored jobs`
                : "Re-score all"}
          </Button>
        }
      />
      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Skill gap" className="lg:col-span-1">
          {topGaps.length === 0 ? (
            <div className="p-4 text-xs text-muted-foreground">
              {items.some((i) => i.score)
                ? "No skill gaps detected — great coverage!"
                : "Score your jobs to see skill gaps."}
            </div>
          ) : (
            <ul className="divide-y divide-border text-sm">
              {topGaps.map(([skill, count]) => (
                <li key={skill} className="flex items-center justify-between px-4 py-2.5">
                  <span>{skill}</span>
                  <span className="text-[11px] text-muted-foreground">{count} jobs affected</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Top matches with explanations" className="lg:col-span-2">
          {items.length === 0 ? (
            <div className="p-4 text-xs text-muted-foreground">
              No jobs imported yet.{" "}
              <Link to="/jobs/import" className="underline">
                Import some jobs →
              </Link>
            </div>
          ) : (
            <>
              <ul className="divide-y divide-border">
                {displayItems.map(({ job, score }) => (
                  <li key={job.id} className="space-y-2 px-4 py-3">
                    <div className="flex items-center justify-between">
                      <Link
                        to="/jobs/$jobId"
                        params={{ jobId: job.id }}
                        className="text-sm font-semibold hover:underline"
                      >
                        {job.company} &mdash; {job.title}
                      </Link>
                      {score ? (
                        <ScoreMeter value={score.score} />
                      ) : (
                        <span className="text-[11px] text-muted-foreground">Not scored</span>
                      )}
                    </div>
                    <div className="text-[12px] text-muted-foreground">
                      {score?.explanation || "Run scoring to see match explanation."}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {(job.tags || []).map((t) => (
                        <Tag key={t}>{t}</Tag>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
              {items.length > 20 && (
                <div className="border-t border-border px-4 py-3">
                  <button
                    onClick={() => setShowAll((v) => !v)}
                    className="text-xs font-medium text-muted-foreground hover:text-foreground"
                  >
                    {showAll ? "Show less" : `Show all ${items.length} jobs`}
                  </button>
                </div>
              )}
            </>
          )}
        </Panel>
      </div>
    </PageBody>
  );
}
