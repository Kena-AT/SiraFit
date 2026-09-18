import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScorePill } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  getResume,
  getResumeVersions,
  getResumeDiff,
  revertResumeVersion,
  getExportUrl,
} from "@/lib/api/resumes";
import type { Resume, ResumeVersion, ResumeDiffResponse } from "@/types/resume";
import { VersionCard } from "@/components/sirafit/resume/VersionCard";
import { DiffViewer } from "@/components/sirafit/resume/DiffViewer";

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

  // Compare & Diff state
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [diffModalOpen, setDiffModalOpen] = useState(false);
  const [diffLoading, setDiffLoading] = useState(false);
  const [diffError, setDiffError] = useState<string | null>(null);
  const [diffData, setDiffData] = useState<ResumeDiffResponse | null>(null);

  // Revert confirmation state
  const [revertModalOpen, setRevertModalOpen] = useState(false);
  const [targetVersionForRevert, setTargetVersionForRevert] = useState<ResumeVersion | null>(null);
  const [isReverting, setIsReverting] = useState(false);

  const fetchVersions = async () => {
    try {
      const versionsData = await getResumeVersions(id);
      setVersions(versionsData);
      if (versionsData.length > 0 && !selectedVersion) {
        setSelectedVersion(versionsData[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

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

  const toggleCompareSelection = (versionId: string) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(versionId)) {
        return prev.filter((i) => i !== versionId);
      }
      if (prev.length >= 2) {
        // Replace second selection
        return [prev[0], versionId];
      }
      return [...prev, versionId];
    });
  };

  const handleOpenDiff = async () => {
    if (selectedForCompare.length !== 2) return;
    setDiffModalOpen(true);
    setDiffLoading(true);
    setDiffError(null);

    // Sort so earlier version is vA and later is vB
    const v1 = versions.find((v) => v.id === selectedForCompare[0]);
    const v2 = versions.find((v) => v.id === selectedForCompare[1]);
    if (!v1 || !v2) return;

    const [vA, vB] = v1.version_number <= v2.version_number ? [v1, v2] : [v2, v1];

    try {
      const data = await getResumeDiff(id, vA.id, vB.id);
      setDiffData(data);
    } catch (err: any) {
      setDiffError(err?.message || "Failed to compare versions");
    } finally {
      setDiffLoading(false);
    }
  };

  const handleRevertConfirm = async () => {
    if (!targetVersionForRevert) return;
    setIsReverting(true);
    try {
      const newVersion = await revertResumeVersion(id, targetVersionForRevert.id);
      setRevertModalOpen(false);
      setTargetVersionForRevert(null);
      await fetchVersions();
      setSelectedVersion(newVersion);
    } catch (err) {
      console.error("Revert failed:", err);
    } finally {
      setIsReverting(false);
    }
  };

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
        description={`${versions.length} version${versions.length !== 1 ? "s" : ""} · Last updated ${new Date(resume.updated_at).toLocaleDateString()}`}
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

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
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
          <Panel
            title="Version History"
            actions={
              <Button
                size="sm"
                variant={selectedForCompare.length === 2 ? "default" : "outline"}
                className="h-7 text-xs"
                disabled={selectedForCompare.length !== 2}
                onClick={handleOpenDiff}
              >
                Compare ({selectedForCompare.length}/2)
              </Button>
            }
          >
            <div className="p-3 space-y-3">
              {selectedForCompare.length > 0 && selectedForCompare.length < 2 && (
                <div className="text-[11px] text-muted-foreground bg-muted/40 p-2 rounded border border-border/60">
                  Select 1 more version to compare side-by-side differences.
                </div>
              )}

              <div className="space-y-2.5 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
                {versions.map((v) => (
                  <VersionCard
                    key={v.id}
                    version={v}
                    isActive={selectedVersion?.id === v.id}
                    isSelectedForCompare={selectedForCompare.includes(v.id)}
                    onSelect={() => setSelectedVersion(v)}
                    onToggleCompare={() => toggleCompareSelection(v.id)}
                    onRevertClick={() => {
                      setTargetVersionForRevert(v);
                      setRevertModalOpen(true);
                    }}
                    isReverting={isReverting}
                  />
                ))}
              </div>
            </div>
          </Panel>
        </div>
      </div>

      {/* Diff Viewer Modal */}
      <Dialog open={diffModalOpen} onOpenChange={setDiffModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden p-6">
          <DialogHeader>
            <DialogTitle>Compare Resume Versions</DialogTitle>
            <DialogDescription>
              Side-by-side semantic differences between selected snapshots.
            </DialogDescription>
          </DialogHeader>
          <DiffViewer
            diff={diffData}
            isLoading={diffLoading}
            error={diffError}
            onClose={() => setDiffModalOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Revert Confirmation Modal */}
      <Dialog open={revertModalOpen} onOpenChange={setRevertModalOpen}>
        <DialogContent className="max-w-md p-6">
          <DialogHeader>
            <DialogTitle>Revert to Version v{targetVersionForRevert?.version_number}</DialogTitle>
            <DialogDescription className="pt-2 text-sm leading-relaxed text-foreground/90">
              This will create a <strong>new immutable version</strong> using this resume's exact
              content. The existing version history will remain intact and will never be modified or
              overwritten.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => {
                setRevertModalOpen(false);
                setTargetVersionForRevert(null);
              }}
              disabled={isReverting}
            >
              Cancel
            </Button>
            <Button onClick={handleRevertConfirm} disabled={isReverting}>
              {isReverting ? "Creating new version..." : "Confirm Revert"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
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
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Summary</h3>
          <p className="mt-1 text-[13px] leading-relaxed">{data.summary}</p>
        </section>
      )}

      {data.experience && data.experience.length > 0 && (
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
              {exp.location && <div className="text-xs text-muted-foreground">{exp.location}</div>}
              <ul className="list-disc space-y-0.5 pl-5 text-[12px] leading-relaxed">
                {exp.bullets.map((b, j) => (
                  <li key={j}>{b}</li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      {data.projects && data.projects.length > 0 && (
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

      {data.skills && data.skills.length > 0 && (
        <section>
          <h3 className="font-mono text-[10px] font-semibold uppercase tracking-widest">Skills</h3>
          <p className="mt-1 text-[12px]">{data.skills.join(" · ")}</p>
        </section>
      )}

      {data.education && data.education.length > 0 && (
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
              Generated with {version.template || "default"} template · v{version.version_number} (
              {version.source_type})
            </span>
            {version.score && <ScorePill value={version.score} />}
          </div>
        </footer>
      )}
    </div>
  );
}
