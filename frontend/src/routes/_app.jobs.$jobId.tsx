import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag, EmptyState, StatusPill } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import {
  getJob,
  deleteJob,
  archiveJob,
  triggerAnalysis,
  getJobAnalysis,
  getCachedMatchScore,
} from "@/lib/api/jobs";
import { getApplications, createApplication } from "@/lib/api/applications";
import { AnalysisInsights, AnalysisSkeleton } from "@/components/sirafit/analysis-insights";
import { MatchScoreCard } from "@/components/sirafit/match-score-card";
import { ConfirmDialog } from "@/components/sirafit/confirm-dialog";
import { toast } from "sonner";
import type { Job, JobAnalysis, JobMatchScore } from "@/types/job";

export const Route = createFileRoute("/_app/jobs/$jobId")({
  head: () => ({ meta: [{ title: "Job details · SiraFit" }] }),
  component: JobDetails,
});

function JobDetails() {
  const { jobId } = Route.useParams();
  const navigate = Route.useNavigate();
  const queryClient = useQueryClient();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Analysis: loaded via React Query and polled only while processing.
  // refetchInterval returns a number (ms) while status === "processing" and
  // `false` otherwise, so polling stops on completion/failure with no orphaned
  // timers. Inherits the global 60s staleTime from the QueryClient config.
  const {
    data: analysis,
    isLoading: analysisLoading,
    error: analysisQueryError,
  } = useQuery({
    queryKey: ["job-analysis", jobId],
    queryFn: () => getJobAnalysis(jobId),
    refetchInterval: (query) => (query.state.data?.status === "processing" ? 2500 : false),
    refetchIntervalInBackground: false,
    retry: 2,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 8000),
  });

  const analysisError =
    analysis?.status === "failed"
      ? (analysis as any).summary || "Analysis failed. Please try again."
      : analysisQueryError
        ? String((analysisQueryError as any)?.message ?? analysisQueryError)
        : null;

  // Match score state
  const [matchScore, setMatchScore] = useState<JobMatchScore | null>(null);
  const [matchScoreLoading, setMatchScoreLoading] = useState(false);

  // Application state for this job
  const [existingApplication, setExistingApplication] = useState<any | null>(null);
  const [savingPipeline, setSavingPipeline] = useState(false);
  const [pipelineMsg, setPipelineMsg] = useState<string | null>(null);

  // Load job
  useEffect(() => {
    const fetchJob = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getJob(jobId);
        setJob(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchJob();
  }, [jobId]);

  // Load match score + existing application on mount
  useEffect(() => {
    if (!jobId) return;

    const fetchData = async () => {
      try {
        setMatchScoreLoading(true);
        const matchScoreData = await getCachedMatchScore(jobId);
        setMatchScore(matchScoreData);
      } catch (e: any) {
        console.error("Failed to fetch match score:", e.message);
      } finally {
        setMatchScoreLoading(false);
      }

      try {
        const apps = await getApplications();
        const found = apps.find((a: any) => a.job_id === jobId);
        setExistingApplication(found ?? null);
      } catch (e: any) {
        console.error("Failed to fetch applications:", e.message);
      }
    };

    fetchData();
  }, [jobId]);

  // Auto-trigger analysis if status is not_started
  useEffect(() => {
    if (analysis?.status === "not_started") {
      handleRunAnalysis();
    }
  }, [analysis?.status, jobId]);

  const handleRunAnalysis = async (forceRefresh = false) => {
    try {
      const stub = await triggerAnalysis(jobId, forceRefresh);
      // Reflect the processing stub immediately so polling begins without a flash.
      queryClient.setQueryData(["job-analysis", jobId], stub);
    } catch (e: any) {
      queryClient.setQueryData(["job-analysis", jobId], (prev: JobAnalysis | null) => ({
        ...(prev ?? ({} as JobAnalysis)),
        status: "failed",
        summary: e.message || "Failed to start analysis",
      }));
    }
  };

  const handleSaveToPipeline = async () => {
    if (existingApplication) return; // already saved
    setSavingPipeline(true);
    setPipelineMsg(null);
    try {
      const app = await createApplication(jobId);
      setExistingApplication(app);
      setPipelineMsg("Saved to pipeline!");
    } catch (e: any) {
      setPipelineMsg(e.message || "Failed to save");
    } finally {
      setSavingPipeline(false);
      setTimeout(() => setPipelineMsg(null), 3000);
    }
  };

  const handleArchiveToggle = async () => {
    if (!job) return;
    const nextArchived = !(job as any).is_archived;
    setActionLoading(true);
    try {
      await archiveJob(job.id, nextArchived);
      setJob({ ...job, is_archived: nextArchived } as any);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast.success(nextArchived ? "Job archived" : "Job unarchived");
    } catch (e: any) {
      toast.error(e.message || "Failed to update archive status");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteJob = async () => {
    if (!job) return;
    setActionLoading(true);
    try {
      await deleteJob(job.id);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast.success("Job deleted");
      navigate({ to: "/jobs" });
    } catch (e: any) {
      toast.error(e.message || "Failed to delete job");
      setActionLoading(false);
    }
  };

  const handleExportDetails = () => {
    if (!job) return;
    const content = [
      `Title: ${job.title}`,
      `Company: ${job.company}`,
      `Location: ${job.location || "N/A"}`,
      `Source: ${job.source}`,
      `URL: ${job.url || "N/A"}`,
      `Salary: ${formatSalary(job)}`,
      `Tags: ${(job.tags || []).join(", ")}`,
      `Imported: ${formatDate(job.created_at)}`,
      "",
      "Description:",
      job.description || "No description available",
    ].join("\n");
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${job.company}-${job.title}.txt`.replace(/[^a-z0-9.-]/gi, "_");
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatSalary = (job: Job) => {
    if (!job.salary_min && !job.salary_max) return "Salary not specified";
    const currency = job.currency || "$";
    if (job.salary_min && job.salary_max) {
      return `${currency}${job.salary_min.toLocaleString()} – ${currency}${job.salary_max.toLocaleString()}`;
    }
    if (job.salary_max) return `Up to ${currency}${job.salary_max.toLocaleString()}`;
    return `${currency}${job.salary_min!.toLocaleString()}+`;
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <PageBody>
        <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
          Loading job details...
        </div>
      </PageBody>
    );
  }

  if (error || !job) {
    return (
      <PageBody>
        <EmptyState
          title="Job not found"
          body={error || "The job you're looking for doesn't exist"}
          action={
            <Link
              to="/jobs"
              className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background"
            >
              Back to jobs
            </Link>
          }
        />
      </PageBody>
    );
  }

  const isProcessing = analysis?.status === "processing";

  return (
    <PageBody>
      <PageHeader
        eyebrow={
          <div className="flex items-center gap-2">
            <Tag>{job.source}</Tag>
            <span className="text-muted-foreground">·</span>
            <span className="font-mono text-[11px]">{job.external_id}</span>
          </div>
        }
        title={job.title}
        description={
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold">{job.company}</span>
            {job.location && (
              <>
                <span className="text-muted-foreground">·</span>
                <span>{job.location}</span>
              </>
            )}
            <span className="text-muted-foreground">·</span>
            <span>{formatSalary(job)}</span>
          </div>
        }
        actions={
          <>
            <Link
              to="/jobs"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              Back to jobs
            </Link>
            {job.url && (
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
              >
                View original →
              </a>
            )}
            <Link
              to="/resumes/builder"
              search={{ jobId: undefined }}
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              Tailor resume
            </Link>
            <Link
              to="/cover-letters/builder"
              search={{ edit: undefined }}
              className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90"
            >
              Apply
            </Link>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Main content */}
        <div className="space-y-4 lg:col-span-2">
          <Panel title="Job description">
            <div className="space-y-4 p-5">
              {job.description ? (
                <div className="whitespace-pre-wrap text-sm text-foreground/90">
                  {job.description}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No description available</p>
              )}
              {job.tags && job.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 border-t border-border pt-4">
                  <div className="w-full font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Extracted tags
                  </div>
                  {job.tags.map((t) => (
                    <Tag key={t}>{t}</Tag>
                  ))}
                </div>
              )}
            </div>
          </Panel>

          <Panel title="Import details">
            <div className="grid gap-4 p-5 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    External ID
                  </div>
                  <div className="mt-1 font-mono text-xs">{job.external_id}</div>
                </div>
                <div>
                  <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Source
                  </div>
                  <div className="mt-1">
                    <Tag>{job.source}</Tag>
                  </div>
                </div>
                <div>
                  <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Imported on
                  </div>
                  <div className="mt-1">{formatDate(job.created_at)}</div>
                </div>
                <div>
                  <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Last updated
                  </div>
                  <div className="mt-1">{formatDate(job.updated_at)}</div>
                </div>
              </div>
              {job.url && (
                <div>
                  <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Original URL
                  </div>
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 block truncate text-xs text-[color:var(--brand)] hover:underline"
                  >
                    {job.url}
                  </a>
                </div>
              )}
            </div>
          </Panel>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Match Score panel */}
          <Panel title="Match Score">
            {matchScoreLoading ? (
              <div className="p-5 text-sm text-muted-foreground">Loading...</div>
            ) : matchScore ? (
              <div className="p-5">
                <MatchScoreCard score={matchScore} />
              </div>
            ) : (
              <div className="p-5 text-sm text-muted-foreground">No match score available.</div>
            )}
          </Panel>

          {/* AI Analysis panel */}
          <Panel
            title="AI Analysis"
            description={
              analysis?.status === "done"
                ? `Score: ${analysis.score}/100`
                : "Job intelligence from AI"
            }
          >
            {/* No analysis yet */}
            {(!analysis || analysis?.status === "not_started") && !isProcessing && (
              <div className="flex flex-col items-center gap-3 p-5 text-center">
                <div className="text-3xl">🔍</div>
                <p className="text-xs text-muted-foreground">
                  Run AI analysis to get a match score, pros & cons, and skills gap.
                </p>
                {analysisError && <p className="text-xs text-destructive">{analysisError}</p>}
                <Button
                  className="w-full"
                  onClick={() => handleRunAnalysis()}
                  disabled={isProcessing}
                >
                  Run AI Analysis
                </Button>
              </div>
            )}

            {/* Processing */}
            {isProcessing && (
              <div>
                <div className="flex items-center gap-2 px-4 pt-4 text-xs text-muted-foreground">
                  <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-border border-t-foreground" />
                  Analysing with AI…
                </div>
                <AnalysisSkeleton />
              </div>
            )}

            {/* Done */}
            {analysis?.status === "done" && !isProcessing && (
              <>
                <AnalysisInsights analysis={analysis} />
                <div className="border-t border-border px-4 pb-4">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => handleRunAnalysis(true)}
                  >
                    Re-run analysis
                  </Button>
                </div>
              </>
            )}

            {/* Failed */}
            {analysis?.status === "failed" && !isProcessing && (
              <div className="flex flex-col items-center gap-3 p-5 text-center">
                <p className="text-xs text-destructive">
                  {analysis.summary || "Analysis failed. Please try again."}
                </p>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => handleRunAnalysis(true)}
                >
                  Retry
                </Button>
              </div>
            )}
          </Panel>

          <Panel title="Compensation">
            <div className="p-4">
              <div className="text-2xl font-semibold">{formatSalary(job)}</div>
              {job.currency && (
                <div className="mt-1 text-xs text-muted-foreground">Currency: {job.currency}</div>
              )}
            </div>
          </Panel>

          <Panel title="Location">
            <div className="p-4">
              <div className="text-sm">{job.location || "Location not specified"}</div>
            </div>
          </Panel>

          <Panel title="Actions">
            <div className="space-y-2 p-4">
              {pipelineMsg && (
                <div className="rounded-md bg-muted px-3 py-2 text-xs font-medium text-foreground">
                  {pipelineMsg}
                </div>
              )}
              <Button
                className="w-full"
                variant="outline"
                onClick={handleSaveToPipeline}
                disabled={savingPipeline || !!existingApplication}
              >
                {savingPipeline
                  ? "Saving…"
                  : existingApplication
                    ? "In pipeline ✓"
                    : "Save to pipeline"}
              </Button>
              <Button className="w-full" variant="outline" onClick={handleExportDetails}>
                Export details
              </Button>
              <Button
                className="w-full"
                variant="outline"
                onClick={handleArchiveToggle}
                disabled={actionLoading}
              >
                {(job as any).is_archived ? "Unarchive job" : "Archive job"}
              </Button>
              <Button
                className="w-full text-destructive hover:bg-destructive/10"
                variant="outline"
                onClick={() => setDeleteConfirmOpen(true)}
                disabled={actionLoading}
              >
                Delete job
              </Button>
            </div>
          </Panel>

          <Panel title="Application history">
            {existingApplication ? (
              <div className="space-y-2 p-4 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Status</span>
                  <StatusPill status={existingApplication.status} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Added</span>
                  <span>{new Date(existingApplication.created_at).toLocaleDateString()}</span>
                </div>
                <Link
                  to="/applications/$id"
                  params={{ id: existingApplication.id }}
                  className="mt-2 block text-center text-xs font-medium text-[color:var(--brand)] hover:underline"
                >
                  View application →
                </Link>
              </div>
            ) : (
              <div className="p-4 text-xs text-muted-foreground">
                No application record for this job yet.
              </div>
            )}
          </Panel>
        </div>
      </div>

      <ConfirmDialog
        open={deleteConfirmOpen}
        title="Delete job?"
        description="This will permanently delete this job and any associated analysis. This action cannot be undone."
        confirmLabel="Delete job"
        onConfirm={handleDeleteJob}
        onCancel={() => setDeleteConfirmOpen(false)}
      />
    </PageBody>
  );
}
