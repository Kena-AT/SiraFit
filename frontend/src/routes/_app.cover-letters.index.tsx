import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";
import { getCoverLetters, deleteCoverLetter } from "@/lib/api/cover-letters";
import type { CoverLetter } from "@/types/cover-letter";

export const Route = createFileRoute("/_app/cover-letters/")({
  head: () => ({ meta: [{ title: "Cover letters · SiraFit" }] }),
  component: CoverLettersPage,
});

function CoverLettersPage() {
  const [letters, setLetters] = useState<CoverLetter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCoverLetters()
      .then(setLetters)
      .catch((e) => setError(e.message || "Failed to load cover letters"))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this cover letter?")) return;
    try {
      await deleteCoverLetter(id);
      setLetters((prev) => prev.filter((l) => l.id !== id));
    } catch (e: any) {
      setError(e.message || "Failed to delete");
    }
  };

  if (loading) {
    return (
      <PageBody>
        <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
          Loading cover letters...
        </div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Assets"
        title="Cover letters"
        description="Concise, role-aware letters generated from your master profile."
        actions={
          <Link
            to="/cover-letters/builder"
            className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90"
          >
            New letter
          </Link>
        }
      />

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {letters.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border bg-muted/20 px-6 py-12 text-center">
          <div className="text-sm font-medium text-foreground">No cover letters yet</div>
          <p className="mt-1 text-xs text-muted-foreground">
            Generate your first cover letter tailored to a job.
          </p>
          <Link
            to="/cover-letters/builder"
            className="mt-4 inline-block rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background"
          >
            Generate Cover Letter →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {letters.map((letter) => (
            <div
              key={letter.id}
              className="flex items-center justify-between rounded-lg border border-border bg-card p-4 hover:border-[color:var(--brand)]/30 transition-colors"
            >
              <div className="min-w-0">
                <div className="text-sm font-semibold truncate">{letter.title}</div>
                <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                  <Tag>{letter.status}</Tag>
                  <span>{letter.body.split(" ").length} words</span>
                  <span>{new Date(letter.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Link
                  to={`/cover-letters/builder?edit=${letter.id}`}
                  className="text-xs font-medium text-[color:var(--brand)] hover:underline"
                >
                  Open →
                </Link>
                <button
                  onClick={() => handleDelete(letter.id)}
                  className="text-xs text-muted-foreground hover:text-destructive transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </PageBody>
  );
}
