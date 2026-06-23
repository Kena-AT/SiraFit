import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getProfile } from "@/lib/api/profiles";
import { Profile } from "@/types/profile";

export const Route = createFileRoute("/_app/resumes/profiles")({
  head: () => ({ meta: [{ title: "Resume profiles · SiraFit" }] }),
  component: ResumeProfilesPage,
});

function ResumeProfilesPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageBody>
      <PageHeader
        eyebrow="Assets"
        title="Resume profiles"
        description="The canonical source of truth for your career data. Tailored resumes are derived from these."
        actions={
          <Link
            to="/resumes/profile-editor"
            className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90"
          >
            New profile
          </Link>
        }
      />
      <div className="grid gap-3 md:grid-cols-3">
        {loading ? (
          <div>Loading profiles...</div>
        ) : profile ? (
          <div key={profile.id} className="rounded-lg bg-card p-5 ring-1 ring-border">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">
                {profile.first_name} {profile.last_name}
              </div>
              <span className="rounded bg-[color:var(--brand)]/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-widest text-[color:var(--brand)]">
                Active
              </span>
            </div>
            <div className="mt-3 text-[11px] text-muted-foreground">
              {profile.headline || "Master Profile"}
            </div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-[color:var(--brand)]" style={{ width: `100%` }} />
            </div>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {profile.skills?.slice(0, 3).map((s) => (
                <Tag key={s.id}>{s.name}</Tag>
              )) || <Tag>No skills added</Tag>}
            </div>
            <div className="mt-4 flex items-center justify-between">
              <Link
                to="/resumes/$id/editor"
                params={{ id: profile.id }}
                className="text-xs font-medium text-[color:var(--brand)] hover:underline"
              >
                Edit →
              </Link>
              <Button variant="ghost" size="sm">
                Duplicate
              </Button>
            </div>
          </div>
        ) : (
          <div className="rounded-lg bg-card p-5 ring-1 ring-border text-sm text-muted-foreground">
            No profile found. Create one to get started.
          </div>
        )}
      </div>
    </PageBody>
  );
}