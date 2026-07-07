import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScorePill, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getResume, getResumeVersions } from "@/lib/api/resumes";
import { getExportUrl } from "@/lib/api/resumes";
import type { Resume, ResumeVersion } from "@/types/resume";

export const Route = createFileRoute("/_app/resumes/$id")({
  head: () => ({ meta: [{ title: "Resume preview · SiraFit" }] }),
  component: ResumePreviewPage,
});

interface TailoredResumeData {
  name: string;
  email: string;
  phone: string | null;
  location: string | null;
  linkedin: string | null;
  github: string | null;
  website: string | null;
  summary: string;
  experience: Array<{
    title: string;
    company: string;
    location: string | null;
    period: string;
    bullets: string[];
  }>;
  projects: Array<{
    name: string;
    description: string;
    url: string | null;
  }>;
  skills: string[];
  education: Array<{
    institution: string;
    degree: string;
    field_of_study: string | null;
    period: string;
  }>;
}

function ResumePreviewPage() {
  const { id } = Route.useParams();
  const [resume, setResume] = useState<Resume | null>(null);
  const [versions, setVersions] = useState<ResumeVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<ResumeVersion | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [resumeData, versionsData] = await Promise.all([
          getResume(id),
          getResumeVersions(id),
        ]);
        setResume(resumeData);
        setVersions(versionsData);
        if (versionsData.length > 0) {
          setSelectedVersion(versionsData[0]);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const parsedContent = (() => {
    if (!selectedVersion?.content) return null;
    try {
      return JSON.parse(selectedVersion.content) as TailoredResumeData;
    } catch {
      return null;
    }
  })();

  if (loading) {
    return (
      <PageBody>
        <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
          Loading resume...
        </div>
      </PageBody>
    );
  }

  if (!resume) {
    return (
      <PageBody>
        <div className="rounded-lg border border-dashed border-border bg-muted/20 px-6 py-12 text-center">
          <div className="text-sm font-medium text-foreground">Resume not found</div>
          <Link
            to="/resumes"
            className="mt-4 inline-block rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background"
          >
            Back to Resumes →
          </Link>
        </div>
      </PageBody>
    );
  }

  return (
    <PageBody className="max-w-none">
      <PageHeader
        eyebrow={`Resume · ${id.slice(0, 8)}`}
        title={resume.title}
        description={`${versions.length} version${versions.length !== 1 ? 's' : ''} · Last updated ${new Date(resume.updated_at).toLocaleDateString()}`}
        actions={
          <>
            <Button
              variant="outline"
              disabled={!selectedVersion}
              onClick={() => {
                if (!selectedVersion) return;
                window.open(getExportUrl(id, selectedVersion.id, "docx"), "_blank");
              }}
            >
              Download DOCX
            </Button>
            <Button
              variant="outline"
              disabled={!selectedVersion}
              onClick={() => {
                if (!selectedVersion) return;
                window.open(getExportUrl(id, selectedVersion.id, "pdf"), "_blank");
              }}
            >
              Download PDF
            </Button>
            <Button
              disabled={!selectedVersion}
              onClick={() => {
                if (!selectedVersion) return;
                window.open(getExportUrl(id, selectedVersion.id, "html"), "_blank");
              }}
            >
              Export HTML
            </Button>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        {/* Preview */}
        <Panel bodyClassName="bg-muted/30 p-8 grid place-items-center">
          {parsedContent ? (
            <ResumePreview data={parsedContent} version={selectedVersion} />
          ) : (
            <div className="text-sm text-muted-foreground">
              No content available for this version.
            </div>
          )}
        </Panel>

        {/* Sidebar */}
        <div className="space-y-4">
          <Panel title="ATS Readiness">
            <div className="space-y-3 p-4 text-sm">
              <div className="flex items-center justify-between">
                <span>Overall score</span>
                {selectedVersion?.score !== null && selectedVersion?.score !== undefined ? (
                  <ScorePill value={selectedVersion.score} />
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span>Status</span>
                <Tag>{selectedVersion?.status || "unknown"}</Tag>
              </div>
              <div className="flex items-center justify-between">
                <span>Template</span>
                <span className="text-muted-foreground">{selectedVersion?.template || "default"}</span>
              </div>
            </div>
          </Panel>

          <Panel title="Versions">
            <ul className="divide-y divide-border text-sm">
              {versions.map((v) => (
                <li
                  key={v.id}
                  className={`flex cursor-pointer items-center justify-between px-3 py-2 hover:bg-muted/30 ${
                    selectedVersion?.id === v.id ? "bg-muted/30" : ""
                  }`}
                  onClick={() => setSelectedVersion(v)}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs">v{v.version_number}</span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(v.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <Tag>{v.status}</Tag>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>
    </PageBody>
  );
}

function ResumePreview({
  data,
  version,
}: {
  data: TailoredResumeData;
  version: ResumeVersion | null;
}) {
  return (
    <div className="w-full max-w-2xl space-y-5 rounded-sm bg-card p-12 shadow-2xl ring-1 ring-border">
      <header className="border-b border-border pb-4">
        <h2 className="text-2xl font-semibold tracking-tight">{data.name}</h2>
        <div className="mt-1 flex flex-wrap gap-x-2 text-xs text-muted-foreground">
          <span>{data.email}</span>
          {data.phone && <span>· {data.phone}</span>}
          {data.location && <span>· {data.location}</span>}
        </div>
        <div className="mt-1 flex flex-wrap gap-x-2 text-xs text-muted-foreground">
          {data.linkedin && <span>{data.linkedin}</span>}
          {data.github && <span>· {data.github}</span>}
        </div>
      </header>

      {data.summary && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">
            Summary
          </h3>
          <p className="mt-1 text-[13px] leading-relaxed">{data.summary}</p>
        </section>
      )}

      {data.experience.length > 0 && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">
            Experience
          </h3>
          {data.experience.map((exp, i) => (
            <div key={i} className="mt-3 space-y-1">
              <div className="flex items-baseline justify-between text-sm">
                <span className="font-semibold">
                  {exp.title} · {exp.company}
                </span>
                <span className="text-muted-foreground text-xs">{exp.period}</span>
              </div>
              {exp.location && (
                <div className="text-xs text-muted-foreground">{exp.location}</div>
              )}
              <ul className="list-disc space-y-0.5 pl-5 text-[12px] leading-relaxed">
                {exp.bullets.map((b, j) => (
                  <li key={j}>{b}</li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      {data.projects.length > 0 && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">
            Projects
          </h3>
          {data.projects.map((p, i) => (
            <div key={i} className="mt-2 text-[12px]">
              <div className="font-semibold">{p.name}</div>
              <div className="text-foreground/80">{p.description}</div>
              {p.url && (
                <a
                  href={p.url}
                  className="text-[color:var(--brand)] hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {p.url}
                </a>
              )}
            </div>
          ))}
        </section>
      )}

      {data.skills.length > 0 && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Skills</h3>
          <p className="mt-1 text-[12px]">{data.skills.join(" · ")}</p>
        </section>
      )}

      {data.education.length > 0 && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">
            Education
          </h3>
          {data.education.map((edu, i) => (
            <div key={i} className="flex items-baseline justify-between text-[12px]">
              <span>
                {edu.degree} · {edu.institution}
              </span>
              <span className="text-muted-foreground">{edu.period}</span>
            </div>
          ))}
        </section>
      )}

      {version && (
        <footer className="border-t border-border pt-4 text-[10px] text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>
              Generated with {version.template || "default"} template · v{version.version_number}
            </span>
            {version.score && <ScorePill value={version.score} />}
          </div>
        </footer>
      )}
    </div>
  );
}
