import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScorePill, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getResumes } from "@/lib/api/resumes";
import type { Resume } from "@/types/resume";

export const Route = createFileRoute("/_app/resumes/")({
  head: () => ({ meta: [{ title: "Resume versions · SiraFit" }] }),
  component: ResumeVersions,
});

function ResumeVersions() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getResumes()
      .then(setResumes)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <PageBody>
        <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
          Loading resumes...
        </div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Assets"
        title="Resume versions"
        description="Every resume you've generated. Immutable history, version-aware merging."
        actions={
          <>
            <Link
              to="/resumes/profiles"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              Manage profiles
            </Link>
            <Link
              to="/resumes/builder"
              className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90"
            >
              New resume
            </Link>
          </>
        }
      />

      {resumes.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border bg-muted/20 px-6 py-12 text-center">
          <div className="text-sm font-medium text-foreground prints">No resumes yet</div>
          <p className="mt-1 text-xs text-muted-foreground">
            Create your first resume to start tailoring for jobs.
          </p>
          <Link
            to="/resumes/builder"
            className="mt-4 inline-block rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background"
          >
            Create Resume →
          </Link>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {resumes.map((resume) => (
            <Link
              key={resume.id}
              to="/resumes/$id"
              params={{ id: resume.id }}
              className="group block rounded-lg bg-card p-4 ring-1 ring-border hover:ring-[color:var(--brand)]/40"
            >
              <div className="flex items-center justify-between">
                <Tag>{resume.is_primary ? "Primary" : "Draft"}</Tag>
                {resume.pdf_url ? (
                  <ScorePill value={100} />
                ) : (
                  <span className="font-mono text-[10px] text-muted-foreground uppercase">
                    draft
                  </span>
                )}
              </div>
              <div className="mt-3 text-sm font-semibold">{resume.title}</div>
              <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground">
                <span className="font-mono">{resume.id.slice(0, 8)}</span>
                <span className="tabular-nums">
                  {new Date(resume.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="mt-3 grid h-32 place-items-center rounded border border-border bg-muted/30">
                <div className="space-y-1">
                  <div className="h-1 w-24 bg-foreground/80" />
                  <div className="h-1 w-16 bg-muted-foreground/40" />
                  <div className="mt-2 h-1 w-28 bg-muted-foreground/30" />
                  <div className="h-1 w-20 bg-muted-foreground/30" />
                  <div className="h-1 w-24 bg-muted-foreground/30" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </PageBody>
  );
}
