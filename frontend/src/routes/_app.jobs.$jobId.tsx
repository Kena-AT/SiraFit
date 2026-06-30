import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag, EmptyState } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getJob } from "@/lib/api/jobs";
import type { Job } from "@/types/job";

export const Route = createFileRoute("/_app/jobs/$jobId")({
  head: () => ({ meta: [{ title: "Job details · SiraFit" }] }),
  component: JobDetails,
});

function JobDetails() {
  const { jobId } = Route.useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const formatSalary = (job: Job) => {
    if (!job.salary_min && !job.salary_max) return "Salary not specified";
    const currency = job.currency || "$";
    if (job.salary_min && job.salary_max) {
      return `${currency}${job.salary_min.toLocaleString()} – ${currency}${job.salary_max.toLocaleString()}`;
    }
    if (job.salary_max) return `Up to ${currency}${job.salary_max.toLocaleString()}`;
    return `${currency}${job.salary_min.toLocaleString()}+`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
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
          action={<Link to="/jobs" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background">Back to jobs</Link>}
        />
      </PageBody>
    );
  }

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
            <Link to="/jobs" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">
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
            <Link to="/resumes/builder" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">
              Tailor resume
            </Link>
            <Link to="/cover-letters/builder" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">
              Apply
            </Link>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Panel title="Job description">
            <div className="space-y-4 p-5">
              {job.description ? (
                <div className="whitespace-pre-wrap text-sm text-foreground/90">{job.description}</div>
              ) : (
                <p className="text-sm text-muted-foreground">No description available</p>
              )}
              
              {job.tags && job.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 border-t border-border pt-4">
                  <div className="w-full font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Extracted tags
                  </div>
                  {job.tags.map((t) => (<Tag key={t}>{t}</Tag>))}
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
                  <div className="mt-1"><Tag>{job.source}</Tag></div>
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

        <div className="space-y-4">
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
              <Button className="w-full" variant="outline">
                Save to pipeline
              </Button>
              <Button className="w-full" variant="outline">
                Generate match score
              </Button>
              <Button className="w-full" variant="outline">
                Export details
              </Button>
            </div>
          </Panel>

          <Panel title="Application history">
            <div className="p-4 text-xs text-muted-foreground">
              No application record for this job yet.
            </div>
          </Panel>
        </div>
      </div>
    </PageBody>
  );
}