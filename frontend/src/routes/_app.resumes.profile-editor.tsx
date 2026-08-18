import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { getProfile, updateProfile } from "@/lib/api/profiles";
import type { Profile } from "@/types/profile";

const sections = [
  "Header",
  "Experience",
  "Projects",
  "Skills",
  "Education",
  "Certifications",
  "Awards",
  "Languages",
  "Social",
];

export const Route = createFileRoute("/_app/resumes/profile-editor")({
  head: () => ({ meta: [{ title: "Profile editor · SiraFit" }] }),
  component: ProfileEditorPage,
});

function ProfileEditorPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    setSaveStatus(null);
    try {
      const updated = await updateProfile(profile);
      setProfile(updated);
      setSaveStatus("Saved successfully ✓");
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (e: any) {
      setSaveStatus("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <PageBody className="max-w-none">
        <PageHeader
          eyebrow="Assets · Profile"
          title="Profile editor"
          description="Loading your profile..."
        />
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

  const updateField = (field: keyof Profile, val: string) => {
    if (!profile) return;
    setProfile({ ...profile, [field]: val });
  };

  const updateExperience = (index: number, field: keyof Profile["experiences"][0], val: string) => {
    if (!profile) return;
    const exps = [...(profile.experiences ?? [])];
    exps[index] = { ...exps[index], [field]: val };
    setProfile({ ...profile, experiences: exps });
  };

  const addExperience = () => {
    if (!profile) return;
    const exps = [
      ...(profile.experiences ?? []),
      { title: "", company: "", description: "", start_date: "", is_current: false },
    ];
    setProfile({ ...profile, experiences: exps });
  };

  const addSkill = () => {
    if (!profile) return;
    const name = prompt("Enter skill name:");
    if (!name) return;
    const skills = [...(profile.skills ?? []), { name, category: "General" }];
    setProfile({ ...profile, skills });
  };

  return (
    <PageBody className="max-w-none">
      <PageHeader
        eyebrow="Assets · Profile"
        title={p.headline || "Profile editor"}
        description={saveStatus || "Edit your structured resume profile. Changes persist when saved."}
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
              <li
                key={s}
                className={`flex items-center justify-between px-3 py-2 text-sm ${i === 1 ? "bg-muted/50 font-semibold" : ""}`}
              >
                <span>{s}</span>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {i === 1 ? String(p.experiences?.length ?? 0) : ""}
                </span>
              </li>
            ))}
          </ul>
        </Panel>
        <div className="space-y-4">
          <Panel title="Header">
            <div className="grid gap-3 p-4 sm:grid-cols-2">
              <div>
                <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                  First Name
                </label>
                <Input
                  value={p.first_name ?? ""}
                  onChange={(e) => updateField("first_name", e.target.value)}
                />
              </div>
              <div>
                <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                  Last Name
                </label>
                <Input
                  value={p.last_name ?? ""}
                  onChange={(e) => updateField("last_name", e.target.value)}
                />
              </div>
              <div>
                <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                  Title / Headline
                </label>
                <Input
                  value={p.headline ?? ""}
                  onChange={(e) => updateField("headline", e.target.value)}
                />
              </div>
              <div>
                <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                  Email
                </label>
                <Input
                  value={p.email ?? ""}
                  onChange={(e) => updateField("email", e.target.value)}
                />
              </div>
              <div>
                <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                  Location
                </label>
                <Input
                  value={p.location ?? ""}
                  onChange={(e) => updateField("location", e.target.value)}
                />
              </div>
            </div>
          </Panel>
          <Panel
            title="Experience"
            actions={
              <Button variant="outline" size="sm" onClick={addExperience}>
                + Add role
              </Button>
            }
          >
            <div className="divide-y divide-border">
              {(p.experiences ?? []).length === 0 ? (
                <div className="p-4 text-sm text-muted-foreground">No experience entries yet.</div>
              ) : (
                p.experiences!.map((e, i) => (
                  <div key={e.id ?? i} className="space-y-3 p-4">
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="sm:col-span-1">
                        <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                          Company
                        </label>
                        <Input
                          value={e.company ?? ""}
                          onChange={(ev) => updateExperience(i, "company", ev.target.value)}
                        />
                      </div>
                      <div className="sm:col-span-1">
                        <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                          Role
                        </label>
                        <Input
                          value={e.title ?? ""}
                          onChange={(ev) => updateExperience(i, "title", ev.target.value)}
                        />
                      </div>
                      <div className="sm:col-span-1">
                        <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                          Period
                        </label>
                        <Input
                          value={e.start_date ?? ""}
                          onChange={(ev) => updateExperience(i, "start_date", ev.target.value)}
                          placeholder="e.g. 2021 – Present"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                        Achievements
                      </label>
                      <Textarea
                        value={e.description ?? ""}
                        onChange={(ev) => updateExperience(i, "description", ev.target.value)}
                        rows={3}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </Panel>
          <Panel
            title="Skills"
            actions={
              <Button variant="outline" size="sm" onClick={addSkill}>
                + Add skill
              </Button>
            }
          >
            <div className="flex flex-wrap gap-1.5 p-4">
              {(p.skills ?? []).length === 0 ? (
                <span className="text-sm text-muted-foreground">No skills added yet.</span>
              ) : (
                p.skills!.map((s) => <Tag key={s.id ?? s.name}>{s.name}</Tag>)
              )}
            </div>
          </Panel>
        </div>
      </div>
    </PageBody>
  );
}
