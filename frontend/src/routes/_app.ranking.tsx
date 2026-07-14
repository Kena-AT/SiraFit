import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getJobs, getMatchScore } from "@/lib/api/jobs";
import type { Job, JobMatchScore } from "@/types/job";

interface JobWithScore {
  job: Job;
  score: JobMatchScore | null;
}

export const Route = createFileRoute("/_app/ranking")({
  head: () => ({ meta: [{ title: "Opportunity ranking · SiraFit" }] }),
  component: OpportunityRanking,
});

function OpportunityRanking() {
  const [items, setItems] = useState<JobWithScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRanked = async () => {
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
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchRanked().finally(() => setLoading(false));
  }, []);

  const handleReRank = async () => {
    setRefreshing(true);
    await fetchRanked();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <PageBody>
        <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
          Ranking opportunities...
        </div>
      </PageBody>
    );
  }

  if (error) {
    return (
      <PageBody>
        <PageHeader
          eyebrow="Intelligence"
          title="Opportunity ranking"
          description="Deterministic priorities, you decide what to apply to."
        />
        <div className="px-4 py-8 text-sm text-destructive">{error}</div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Intelligence"
        title="Opportunity ranking"
        description="Where to spend your next hour. Deterministic priorities, you decide what to apply to."
        actions={
          <Button onClick={handleReRank} disabled={refreshing}>
            {refreshing ? "Re-ranking..." : "Run re-ranking"}
          </Button>
        }
      />
      <Panel>
        {items.length === 0 ? (
          <div className="p-4 text-xs text-muted-foreground">
            No jobs imported. Import some jobs first.
          </div>
        ) : (
          <ol className="divide-y divide-border">
            {items.map(({ job, score }, i) => (
              <li key={job.id} className="flex items-center gap-4 px-4 py-3">
                <span className="w-8 font-mono text-sm font-semibold tabular-nums text-muted-foreground">
                  #{String(i + 1).padStart(2, "0")}
                </span>
                <div className="flex-1">
                  <Link
                    to="/jobs/$jobId"
                    params={{ jobId: job.id }}
                    className="text-sm font-semibold hover:underline"
                  >
                    {job.company} &mdash; {job.title}
                  </Link>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                    <span>{job.location || "Remote"}</span>
                    <span>&middot;</span>
                    <span>{job.salary_min ? `$${job.salary_min}k` : "—"}</span>
                    <span>&middot;</span>
                    <Tag>{job.source}</Tag>
                  </div>
                </div>
                <div className="w-40">
                  {score ? (
                    <ScoreMeter value={score.score} />
                  ) : (
                    <span className="text-[11px] text-muted-foreground">No score</span>
                  )}
                </div>
                <Link
                  to="/resumes/builder"
                  className="text-xs font-medium text-[color:var(--brand)] hover:underline"
                >
                  Tailor &rarr;
                </Link>
              </li>
            ))}
          </ol>
        )}
      </Panel>
    </PageBody>
  );
}
