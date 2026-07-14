import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, Tag } from "@/components/sirafit/bits";
import { getJobs } from "@/lib/api/jobs";
import { getMatchScore } from "@/lib/api/jobs";
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      setError(null);
      try {
        const list = await getJobs({ limit: 200 });
        const withScores: JobWithScore[] = [];
        for (const job of list.jobs) {
          let score: JobMatchScore | null = null;
          try {
            score = await getMatchScore(job.id);
          } catch {
            /* no score */
          }
          withScores.push({ job, score });
        }
        withScores.sort((a, b) => (b.score?.score ?? 0) - (a.score?.score ?? 0));
        setItems(withScores);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  // Aggregate skill gaps
  const skillGapCounts: Record<string, number> = {};
  for (const { job, score } of items) {
    if (!score) continue;
    for (const tag of job.tags || []) {
      const tagLower = tag.toLowerCase();
      if (score.breakdown.skills < 100 && !skillGapCounts[tagLower]) {
        skillGapCounts[tagLower] = (skillGapCounts[tagLower] || 0) + 1;
      }
    }
  }
  const topGaps = Object.entries(skillGapCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  const topItems = items.slice(0, 8);

  if (loading) {
    return (
      <PageBody>
        <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
          Analysing matches...
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
      />
      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Skill gap" className="lg:col-span-1">
          {topGaps.length === 0 ? (
            <div className="p-4 text-xs text-muted-foreground">No skill gaps detected.</div>
          ) : (
            <ul className="divide-y divide-border text-sm">
              {topGaps.map(([skill, count]) => (
                <li key={skill} className="flex items-center justify-between px-4 py-2.5">
                  <span>{skill}</span>
                  <span className="text-[11px] text-muted-foreground">{count} jobs missing</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
        <Panel title="Top matches with explanations" className="lg:col-span-2">
          {topItems.length === 0 ? (
            <div className="p-4 text-xs text-muted-foreground">No jobs with scores yet.</div>
          ) : (
            <ul className="divide-y divide-border">
              {topItems.map(({ job, score }) => (
                <li key={job.id} className="space-y-2 px-4 py-3">
                  <div className="flex items-center justify-between">
                    <Link
                      to="/jobs/$jobId"
                      params={{ jobId: job.id }}
                      className="text-sm font-semibold hover:underline"
                    >
                      {job.company} &mdash; {job.title}
                    </Link>
                    {score && <ScoreMeter value={score.score} />}
                  </div>
                  <div className="text-[12px] text-muted-foreground">
                    {score?.explanation || "No match score computed yet."}
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(job.tags || []).map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </PageBody>
  );
}
