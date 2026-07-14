import { createFileRoute, useSearch } from "@tanstack/react-router";
import { useState, useEffect, useRef } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getCoverLetter,
  createCoverLetter,
  updateCoverLetter,
  generateCoverLetter,
  regenerateCoverLetter,
  exportCoverLetterPdf,
} from "@/lib/api/cover-letters";
import { getJobs } from "@/lib/api/jobs";
import type { CoverLetter } from "@/types/cover-letter";
import type { Job } from "@/types/job";

export const Route = createFileRoute("/_app/cover-letters/builder")({
  head: () => ({ meta: [{ title: "Cover letter builder · SiraFit" }] }),
  component: Builder,
  validateSearch: (search: Record<string, unknown>) => ({
    edit: search.edit as string | undefined,
  }),
});

const TONES = [
  { value: "matching", label: "Match job tone" },
  { value: "conversational", label: "Conversational" },
  { value: "formal", label: "Formal" },
];

const TEMPLATES = [
  { value: "classic", label: "Classic" },
  { value: "modern", label: "Modern" },
  { value: "compact", label: "Compact" },
];

function wordCount(text: string) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function Builder() {
  const { edit: editId } = useSearch({ from: "/_app/cover-letters/builder" });

  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [tone, setTone] = useState("matching");
  const [template, setTemplate] = useState("classic");
  const [body, setBody] = useState("");
  const [title, setTitle] = useState("");
  const [letter, setLetter] = useState<CoverLetter | null>(null);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<"idle" | "saved" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load jobs and existing letter (if editing)
  useEffect(() => {
    getJobs({ limit: 200 })
      .then((res) => setJobs(res.jobs))
      .catch(console.error);

    if (editId) {
      getCoverLetter(editId)
        .then((existing) => {
          setLetter(existing);
          setBody(existing.body);
          setTitle(existing.title);
          setTone(existing.tone || "matching");
          setTemplate(existing.template || "classic");
          // Pre-select the job if we have one
          if (existing.job_id) {
            getJobs({ limit: 200 }).then((res) => {
              const found = res.jobs.find((j: Job) => j.id === existing.job_id);
              if (found) setSelectedJob(found);
            });
          }
        })
        .catch(console.error);
    }
  }, [editId]);

  const handleGenerate = async () => {
    if (!selectedJob) {
      setError("Select a job first");
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      let result: { cover_letter_id: string; status: string; message: string };
      if (letter) {
        result = await regenerateCoverLetter(letter.id, {
          job_id: selectedJob.id,
          tone,
          template,
        });
      } else {
        result = await generateCoverLetter({ job_id: selectedJob.id, tone, template });
      }
      // Fetch the full letter to get body
      const updated = await getCoverLetter(result.cover_letter_id);
      setLetter(updated);
      setBody(updated.body);
      setTitle(updated.title);
      setStatus("saved");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!body.trim()) return;
    setSaving(true);
    setError(null);
    try {
      if (letter) {
        const updated = await updateCoverLetter(letter.id, { body, title, tone, template });
        setLetter(updated);
      } else {
        const created = await createCoverLetter({
          title: title || `Cover letter — ${new Date().toLocaleDateString()}`,
          body,
          tone,
          template,
          job_id: selectedJob?.id,
        });
        setLetter(created);
        setTitle(created.title);
      }
      setStatus("saved");
      setTimeout(() => setStatus("idle"), 2500);
    } catch (e: any) {
      setError(e.message);
      setStatus("error");
    } finally {
      setSaving(false);
    }
  };

  // Auto-save with debounce when body changes (only if letter already exists)
  useEffect(() => {
    if (!letter || !body) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    setStatus("idle");
    saveTimer.current = setTimeout(() => {
      updateCoverLetter(letter.id, { body, tone, template })
        .then((updated) => {
          setLetter(updated);
          setStatus("saved");
          setTimeout(() => setStatus("idle"), 2000);
        })
        .catch(() => setStatus("error"));
    }, 1500);
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, [body, tone, template]);

  const handleExportPdf = () => {
    if (!letter) return;
    const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
    window.open(`${API_BASE_URL}${exportCoverLetterPdf(letter.id)}`, "_blank");
  };

  const paragraphs = body.split(/\n\n+/).filter(Boolean);

  return (
    <PageBody className="max-w-none">
      <PageHeader
        eyebrow="Assets · Builder"
        title={title || "Cover letter builder"}
        description={
          letter
            ? `Auto-saved · ${wordCount(body)} words`
            : "Generate from profile + job, then edit freely"
        }
        actions={
          <>
            {letter && (
              <Button variant="outline" onClick={handleExportPdf} disabled={!letter}>
                Export PDF
              </Button>
            )}
            <Button variant="outline" onClick={handleSave} disabled={saving || !body.trim()}>
              {saving ? "Saving…" : status === "saved" ? "Saved ✓" : "Save"}
            </Button>
            <Button onClick={handleGenerate} disabled={generating || !selectedJob}>
              {generating ? "Generating…" : letter ? "Re-generate" : "Generate"}
            </Button>
          </>
        }
      />

      {error && (
        <div className="rounded-md bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[260px_1fr_1fr]">
        {/* Controls */}
        <div className="space-y-4">
          <Panel title="Job" bodyClassName="p-3 space-y-2">
            <div className="max-h-64 overflow-y-auto space-y-1.5">
              {jobs.length === 0 ? (
                <p className="text-xs text-muted-foreground px-1">No jobs imported yet.</p>
              ) : (
                jobs.map((j) => (
                  <button
                    key={j.id}
                    onClick={() => setSelectedJob(j)}
                    className={`w-full rounded border p-2.5 text-left text-xs transition-colors hover:bg-muted/40 ${
                      selectedJob?.id === j.id
                        ? "border-[color:var(--brand)] bg-[color:var(--brand)]/5 font-medium"
                        : "border-border"
                    }`}
                  >
                    <div className="font-medium">{j.company}</div>
                    <div className="text-muted-foreground truncate">{j.title}</div>
                  </button>
                ))
              )}
            </div>
          </Panel>

          <Panel title="Options" bodyClassName="p-3 space-y-3">
            <div>
              <label className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                Tone
              </label>
              <Select value={tone} onValueChange={setTone}>
                <SelectTrigger className="mt-1 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TONES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                Template
              </label>
              <Select value={template} onValueChange={setTemplate}>
                <SelectTrigger className="mt-1 h-8 text-xs">
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
            {selectedJob && (
              <div className="rounded-md bg-muted/30 p-2 text-[11px]">
                <div className="font-medium">{selectedJob.company}</div>
                <div className="text-muted-foreground">{selectedJob.title}</div>
                {selectedJob.location && (
                  <div className="text-muted-foreground">{selectedJob.location}</div>
                )}
              </div>
            )}
          </Panel>
        </div>

        {/* Editor */}
        <Panel
          title="Draft"
          actions={
            <span className="font-mono text-[10px] text-muted-foreground">
              {wordCount(body)} words
            </span>
          }
        >
          {generating ? (
            <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
              <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
              Generating with AI…
            </div>
          ) : (
            <Textarea
              className="min-h-[480px] rounded-none border-0 border-border bg-card font-[inherit] text-sm leading-relaxed"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder={
                selectedJob
                  ? 'Click "Generate" to create a tailored letter, or start writing…'
                  : "Select a job first, then generate or write your letter…"
              }
            />
          )}
        </Panel>

        {/* Preview */}
        <Panel title="Preview" bodyClassName="bg-muted/30 p-6">
          <div className="space-y-3 rounded-sm bg-card p-8 text-[13px] leading-relaxed shadow-2xl ring-1 ring-border min-h-[480px]">
            {paragraphs.length === 0 ? (
              <p className="text-muted-foreground text-xs">Preview will appear here as you type…</p>
            ) : (
              paragraphs.map((para, i) => <p key={i}>{para}</p>)
            )}
          </div>
        </Panel>
      </div>
    </PageBody>
  );
}
