import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { generateResume, getResumes, createResume, getResumeVersions } from "@/lib/api/resumes";
import { getJobs } from "@/lib/api/jobs";
import type { Job } from "@/types/job";
import type { Resume, ResumeVersion } from "@/types/resume";

export const Route = createFileRoute("/_app/resumes/builder")({
  head: () => ({ meta: [{ title: "Resume builder · SiraFit" }] }),
  component: Builder,
});

const TEMPLATES = [
  { value: "minimal", label: "Minimal" },
  { value: "technical", label: "Technical" },
  { value: "modern", label: "Modern" },
  { value: "corporate", label: "Corporate" },
  { value: "compact", label: "Compact" },
];

function Builder() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [template, setTemplate] = useState("minimal");
  const [generating, setGenerating] = useState(false);
  const [versions, setVersions] = useState<ResumeVersion[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJobs({ limit: 200 }).then((res) => setJobs(res.jobs)).catch(console.error);
    getResumes().then(async (res) => {
      if (res.length === 0) {
        const created = await createResume({
          title: "My Resume",
          content: "{}",
          is_primary: true,
        });
        setResumes([created]);
        setSelectedResume(created);
      } else {
        setResumes(res);
        setSelectedResume(res[0]);
      }
    }).catch(console.error);
  }, []);

  // Poll for version status updates when any version is processing
  useEffect(() => {
    const hasProcessing = versions.some((v) => v.status === "processing");
    if (!hasProcessing || !selectedResume) return;

    const interval = setInterval(() => {
      getResumeVersions(selectedResume.id)
        .then((updated) => {
          // Merge: keep generated versions that are already completed,
          // and update any that the API returned
          setVersions((prev) => {
            const apiMap = new Map(updated.map((v) => [v.id, v]));
            return prev.map((v) => apiMap.get(v.id) ?? v);
          });
        })
        .catch(() => {
          // Silently ignore poll failures
        });
    }, 3000);

    return () => clearInterval(interval);
  }, [versions, selectedResume]);

  const handleGenerate = async () => {
    if (!selectedJob || !selectedResume) return;
    setGenerating(true);
    setError(null);
    try {
      const version = await generateResume(selectedResume.id, {
        job_id: selectedJob.id,
        template,
      });
      setVersions((prev) => [version, ...prev]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <PageBody className="max-w-none">
      <PageHeader
        eyebrow="Assets · Builder"
        title="Tailored Resume Builder"
        description="Select a job and template, then generate a tailored resume."
        actions={
          <>
            <Button variant="outline" disabled={generating}>
              Re-validate
            </Button>
            <Button onClick={handleGenerate} disabled={!selectedJob || !selectedResume || generating}>
              {generating ? "Generating..." : "Generate Version"}
            </Button>
          </>
        }
      />

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-12">
        {/* Job Selection */}
        <Panel title="Target Job" className="lg:col-span-3" bodyClassName="p-4 space-y-4">
          <div className="text-sm text-muted-foreground">Select the job to tailor for:</div>
          <div className="space-y-2">
            {jobs.length === 0 ? (
              <div className="text-xs text-muted-foreground">No jobs imported. <Link to="/jobs/import" className="text-[color:var(--brand)] underline">Import jobs first.</Link></div>
            ) : (
              jobs.map((job) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJob(job)}
                  className={`w-full rounded-md border p-3 text-left text-sm transition-colors hover:bg-muted/40 ${
                    selectedJob?.id === job.id
                      ? "border-[color:var(--brand)] bg-[color:var(--brand)]/5"
                      : "border-border"
                  }`}
                >
                  <div className="font-medium">{job.company}</div>
                  <div className="text-xs text-muted-foreground">{job.title}</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {(job.tags || []).slice(0, 3).map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                  </div>
                </button>
              ))
            )}
          </div>
        </Panel>

        {/* Template & Settings */}
        <Panel title="Template & Settings" className="lg:col-span-4" bodyClassName="p-4 space-y-4">
          <div>
            <label className="text-[10px] font-semibold uppercase text-muted-foreground">
              Target Resume
            </label>
            <Select
              value={selectedResume?.id ?? ""}
              onValueChange={(id) => setSelectedResume(resumes.find((r) => r.id === id) ?? null)}
            >
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select a resume" />
              </SelectTrigger>
              <SelectContent>
                {resumes.map((r) => (
                  <SelectItem key={r.id} value={r.id}>
                    {r.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-[10px] font-semibold uppercase text-muted-foreground">
              Template
            </label>
            <Select value={template} onValueChange={setTemplate}>
              <SelectTrigger className="mt-2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TEMPLATES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">
              Generation Log
            </div>
            <ul className="mt-2 divide-y divide-border font-mono text-[11px]">
              {versions.length === 0 ? (
                <li className="py-2 text-muted-foreground">No generations yet.</li>
              ) : (
                versions.map((v) => (
                  <li key={v.id} className="flex gap-3 py-2">
                    <span className="text-muted-foreground">
                      {new Date(v.created_at).toLocaleTimeString()}
                    </span>
                    <span>
                      {v.status === "processing"
                        ? "Generating..."
                        : v.status === "completed"
                        ? `v${v.version_number} · Score: ${v.score ?? "N/A"}`
                        : `Failed: ${v.tailoring_notes || ""}`}
                    </span>
                  </li>
                ))
              )}
            </ul>
          </div>
        </Panel>

        {/* Preview */}
        <Panel title="Preview" className="lg:col-span-5" bodyClassName="p-6 bg-muted/30">
          {generating ? (
            <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
              <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
              Tailoring resume with AI...
            </div>
          ) : versions.length > 0 && versions[0].status === "completed" ? (
            <SafeResumePreview content={versions[0].content} />
          ) : (
            <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
              Select a job and generate to see preview.
            </div>
          )}
        </Panel>
      </div>
    </PageBody>
  );
}

function SafeResumePreview({ content }: { content: string }) {
  try {
    const data = JSON.parse(content);
    return <ResumePreview data={data} />;
  } catch {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Unable to preview — invalid resume content.
      </div>
    );
  }
}

function ResumePreview({ data }: { data: any }) {
  if (!data) return null;
  return (
    <div className="w-full max-w-md space-y-4 rounded-sm bg-card p-8 shadow-2xl ring-1 ring-border">
      <header className="border-b border-border pb-4">
        <h2 className="text-lg font-semibold tracking-tight">{data.name}</h2>
        <p className="text-xs text-muted-foreground">
          {data.email} · {data.phone} · {data.location}
        </p>
        <p className="text-xs text-muted-foreground">
          {data.linkedin} · {data.github}
        </p>
      </header>
      {data.summary && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Summary</h3>
          <p className="mt-1 text-[13px]">{data.summary}</p>
        </section>
      )}
      {data.experience?.length > 0 && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Experience</h3>
          {data.experience.map((exp: any) => (
            <div key={exp.title + exp.company} className="mt-2 space-y-1">
              <div className="flex items-baseline justify-between text-sm">
                <span className="font-semibold">
                  {exp.title} · {exp.company}
                </span>
                <span className="text-muted-foreground text-xs">{exp.period}</span>
              </div>
              <ul className="list-disc space-y-0.5 pl-5 text-[12px] leading-relaxed">
                {exp.bullets?.map((b: string) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}
      {data.skills?.length > 0 && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Skills</h3>
          <p className="mt-1 text-[12px]">{data.skills.join(" · ")}</p>
        </section>
      )}
      {data.education?.length > 0 && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Education</h3>
          {data.education.map((edu: any) => (
            <div key={edu.institution} className="flex items-baseline justify-between text-[12px]">
              <span>
                {edu.degree} · {edu.institution}
              </span>
              <span className="text-muted-foreground">{edu.period}</span>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
