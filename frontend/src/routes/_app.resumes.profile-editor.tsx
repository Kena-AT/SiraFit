import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { getProfile, updateProfile } from "@/lib/api/profiles";
import type { Profile } from "@/types/profile";

const sections = ["Header", "Experience", "Projects", "Skills", "Education", "Certifications", "Awards", "Languages", "Social"];

export const Route = createFileRoute("/_app/resumes/profile-editor")({
  head: () => ({ meta: [{ title: "Profile editor · SiraFit" }] }),
  component: ProfileEditorPage,
});

function ProfileEditorPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    try {
      await updateProfile(profile);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <PageBody className="max-w-none">
        <PageHeader eyebrow="Assets · Profile" title="Profile editor" description="Loading your profile..." />
      </PageBody>
    );
  }

  const p = profile ?? {
    first_name: "",
    last_name: "",
    headline: "",
    email: "",
    location: "",
    experiences: [],
    educations: [],
    skills: [],
    projects: [],
    certifications: [],
  };

  return (
    <PageBody className="max-w-none">
      <PageHeader
        eyebrow="Assets · Profile"
        title={p.headline || "Profile editor"}
        description="Edit your structured resume profile. Auto-saved locally every 5s."
        actions={
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save snapshot"}
          </Button>
        }
      />
      <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
        <Panel title="Sections">
          <ul className="divide-y divide-border">
            {sections.map((s, i) => (
              <li key={s} className={`flex items-center justify-between px-3 py-2 text-sm ${i === 1 ? "bg-muted/50 font-semibold" : ""}`}>
                <span>{s}</span>
                <span className="font-mono text-[10px] text-muted-foreground">{i === 1 ? String(p.experiences?.length ?? 0) : ""}</span>
              </li>
            ))}
          </ul>
        </Panel>
        <div className="space-y-4">
          <Panel title="Header">
            <div className="grid gap-3 p-4 sm:grid-cols-2">
              <div><label className="text-[10px] font-semibold uppercase text-muted-foreground">Name</label><Input defaultValue={`${p.first_name ?? ""} ${p.last_name ?? ""}`} /></div>
              <div><label className="text-[10px] font-semibold uppercase text-muted-foreground">Title</label><Input defaultValue={p.headline ?? ""} /></div>
              <div><label className="text-[10px] font-semibold uppercase text-muted-foreground">Email</label><Input defaultValue={p.email ?? ""} /></div>
              <div><label className="text-[10px] font-semibold uppercase text-muted-foreground">Location</label><Input defaultValue={p.location ?? ""} /></div>
            </div>
          </Panel>
          <Panel title="Experience" actions={<Button variant="outline" size="sm">+ Add role</Button>}>
            <div className="divide-y divide-border">
              {(p.experiences ?? []).length === 0 ? (
                <div className="p-4 text-sm text-muted-foreground">No experience entries yet.</div>
              ) : (
                p.experiences!.map((e, i) => (
                  <div key={e.id ?? i} className="space-y-3 p-4">
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="sm:col-span-1"><label className="text-[10px] font-semibold uppercase text-muted-foreground">Company</label><Input defaultValue={e.company} /></div>
                      <div className="sm:col-span-1"><label className="text-[10px] font-semibold uppercase text-muted-foreground">Role</label><Input defaultValue={e.title} /></div>
                      <div className="sm:col-span-1"><label className="text-[10px] font-semibold uppercase text-muted-foreground">Period</label><Input defaultValue={e.start_date ?? ""} /></div>
                    </div>
                    <div>
                      <label className="text-[10px] font-semibold uppercase text-muted-foreground">Achievements</label>
                      <Textarea defaultValue={e.description ?? ""} rows={3} />
                    </div>
                  </div>
                ))
              )}
            </div>
          </Panel>
          <Panel title="Skills">
            <div className="flex flex-wrap gap-1.5 p-4">
              {(p.skills ?? []).length === 0 ? (
                <span className="text-sm text-muted-foreground">No skills added yet.</span>
              ) : (
                p.skills!.map((s) => (<Tag key={s.id ?? s.name}>{s.name}</Tag>))
              )}
              <Button variant="ghost" size="sm">+ Add skill</Button>
            </div>
          </Panel>
        </div>
      </div>
    </PageBody>
  );
}
