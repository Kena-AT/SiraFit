import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { getProfile, updateProfile, polishBullet } from "@/lib/api/profiles";
import { parseGithubUsername, fetchGithubRepos } from "@/lib/api/github";
import {
  PromptDialog,
  type PromptDialogConfig,
} from "@/components/sirafit/prompt-dialog";
import type { Profile, Experience, Education, Skill, Project, Certification } from "@/types/profile";
import { Sparkles, Trash2, Plus, Check } from "lucide-react";

export const Route = createFileRoute("/_app/resumes/profile-editor")({
  head: () => ({ meta: [{ title: "Profile editor · SiraFit" }] }),
  component: ProfileEditorPage,
});

const SECTIONS = [
  { id: "header", label: "Header & Summary" },
  { id: "experience", label: "Experience" },
  { id: "education", label: "Education" },
  { id: "projects", label: "Projects" },
  { id: "skills", label: "Skills" },
  { id: "certifications", label: "Certifications" },
];

function ProfileEditorPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeSection, setActiveSection] = useState("header");
  const [polishingIndex, setPolishingIndex] = useState<number | null>(null);
  const [importingGithub, setImportingGithub] = useState(false);
  const [promptDialog, setPromptDialog] = useState<
    (PromptDialogConfig & { resolve: (v: Record<string, string> | null) => void }) | null
  >(null);

  // Promise-based in-app replacement for window.prompt().
  const ask = (config: PromptDialogConfig): Promise<Record<string, string> | null> =>
    new Promise((resolve) => setPromptDialog({ ...config, resolve }));

  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    getProfile()
      .then((data) => setProfile(data))
      .catch((err) => toast.error(`Failed to load profile: ${err.message}`))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    try {
      const updated = await updateProfile(profile);
      setProfile(updated);
      toast.success("Profile saved successfully ✓");
    } catch (e: any) {
      toast.error(`Failed to save profile: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    sectionRefs.current[id]?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  if (loading) {
    return (
      <PageBody className="max-w-none">
        <PageHeader
          eyebrow="Assets · Profile"
          title="Profile editor"
          description="Loading your master career profile..."
        />
      </PageBody>
    );
  }

  const p = profile ?? {
    first_name: "",
    last_name: "",
    headline: "",
    summary: "",
    email: "",
    phone: "",
    location: "",
    website: "",
    linkedin: "",
    github: "",
    experiences: [],
    educations: [],
    skills: [],
    projects: [],
    certifications: [],
  };

  // --- Field Updaters ---
  const updateField = (field: keyof Profile, val: string) => {
    if (!profile) return;
    setProfile({ ...profile, [field]: val });
  };

  // Experience
  const updateExperience = (index: number, field: keyof Experience, val: any) => {
    if (!profile) return;
    const exps = [...(profile.experiences ?? [])];
    exps[index] = { ...exps[index], [field]: val };
    setProfile({ ...profile, experiences: exps });
  };
  const addExperience = () => {
    if (!profile) return;
    setProfile({
      ...profile,
      experiences: [
        { title: "", company: "", location: "", start_date: "", end_date: "", is_current: false, description: "" },
        ...(profile.experiences ?? []),
      ],
    });
  };
  const removeExperience = (index: number) => {
    if (!profile) return;
    const exps = [...profile.experiences];
    exps.splice(index, 1);
    setProfile({ ...profile, experiences: exps });
  };

  // AI STAR bullet polisher — real backend call through the multi-provider
  // fallback chain (Settings → AI key or env keys).
  const handleStarPolish = async (index: number) => {
    const desc = profile?.experiences?.[index]?.description;
    if (!desc || !desc.trim()) {
      toast.error("Please enter a bullet point or description to polish first.");
      return;
    }
    setPolishingIndex(index);
    try {
      const polished = await polishBullet(desc);
      updateExperience(index, "description", polished);
      toast.success("Achievements optimized using STAR method!");
    } catch (e: any) {
      toast.error(`Polish failed: ${e.message}`);
    } finally {
      setPolishingIndex(null);
    }
  };

  // Education
  const updateEducation = (index: number, field: keyof Education, val: any) => {
    if (!profile) return;
    const edus = [...(profile.educations ?? [])];
    edus[index] = { ...edus[index], [field]: val };
    setProfile({ ...profile, educations: edus });
  };
  const addEducation = () => {
    if (!profile) return;
    setProfile({
      ...profile,
      educations: [
        { institution: "", degree: "", field_of_study: "", start_date: "", end_date: "", description: "" },
        ...(profile.educations ?? []),
      ],
    });
  };
  const removeEducation = (index: number) => {
    if (!profile) return;
    const edus = [...profile.educations];
    edus.splice(index, 1);
    setProfile({ ...profile, educations: edus });
  };

  // Projects
  const updateProject = (index: number, field: keyof Project, val: any) => {
    if (!profile) return;
    const projs = [...(profile.projects ?? [])];
    projs[index] = { ...projs[index], [field]: val };
    setProfile({ ...profile, projects: projs });
  };
  const addProject = () => {
    if (!profile) return;
    setProfile({
      ...profile,
      projects: [
        { name: "", description: "", url: "", start_date: "", end_date: "" },
        ...(profile.projects ?? []),
      ],
    });
  };
  const removeProject = (index: number) => {
    if (!profile) return;
    const projs = [...profile.projects];
    projs.splice(index, 1);
    setProfile({ ...profile, projects: projs });
  };

  // Skills
  const addSkill = async () => {
    const values = await ask({
      title: "Add skill",
      fields: [
        {
          key: "name",
          label: "Skill name",
          placeholder: "e.g. TypeScript, Kubernetes, Python",
          required: true,
        },
        {
          key: "category",
          label: "Category",
          placeholder: "e.g. Languages, Frameworks, Tools — defaults to General",
        },
      ],
      confirmLabel: "Add skill",
    });
    if (!values) return; // cancelled
    const name = values.name.trim();
    if (!name || !profile) return;
    const category = values.category.trim() || "General";
    setProfile({ ...profile, skills: [...(profile.skills ?? []), { name, category }] });
  };
  const removeSkill = (index: number) => {
    if (!profile) return;
    const skills = [...profile.skills];
    skills.splice(index, 1);
    setProfile({ ...profile, skills });
  };

  // Certifications
  const updateCert = (index: number, field: keyof Certification, val: any) => {
    if (!profile) return;
    const certs = [...(profile.certifications ?? [])];
    certs[index] = { ...certs[index], [field]: val };
    setProfile({ ...profile, certifications: certs });
  };
  const addCert = () => {
    if (!profile) return;
    setProfile({
      ...profile,
      certifications: [
        { name: "", issuer: "", issue_date: "", expiration_date: "", credential_url: "" },
        ...(profile.certifications ?? []),
      ],
    });
  };
  const removeCert = (index: number) => {
    if (!profile) return;
    const certs = [...profile.certifications];
    certs.splice(index, 1);
    setProfile({ ...profile, certifications: certs });
  };

  // GitHub importer — pulls the user's top public non-fork repos into the
  // Projects section. Uses the GitHub URL from the Header field, or prompts
  // for a username. Nothing is persisted until "Save snapshot".
  const handleGithubImport = async () => {
    if (!profile) return;
    const stored = (profile.github ?? "").trim();
    let username = parseGithubUsername(stored);
    if (!username && stored) {
      toast.error("That doesn't look like a valid GitHub URL or username.");
      return;
    }
    if (!username) {
      const values = await ask({
        title: "Import from GitHub",
        description:
          "Enter your GitHub username to import your top public repositories as projects. You can review everything before saving.",
        fields: [
          {
            key: "username",
            label: "GitHub username",
            placeholder: "e.g. torvalds",
            required: true,
          },
        ],
        confirmLabel: "Import",
      });
      if (!values) return; // cancelled
      username = parseGithubUsername(values.username ?? "");
      if (!username) {
        toast.error("That doesn't look like a valid GitHub username.");
        return;
      }
    }
    setImportingGithub(true);
    try {
      const repos = await fetchGithubRepos(username);
      const existingKeys = new Set(
        (profile.projects ?? []).flatMap((p) =>
          [p.url, p.name].filter(Boolean).map((v) => v!.toLowerCase()),
        ),
      );
      const fresh = repos.slice(0, 8)
        .filter(
          (r) =>
            !existingKeys.has(r.html_url.toLowerCase()) &&
            !existingKeys.has(r.name.toLowerCase()),
        )
        .map((r) => ({
          name: r.name,
          description:
            r.description || (r.language ? `${r.language} project` : "GitHub project"),
          url: r.html_url,
          start_date: r.created_at ? r.created_at.slice(0, 10) : "",
          end_date: "",
        }));
      if (fresh.length === 0) {
        toast.info("All of your top repositories are already in Projects.");
        return;
      }
      setProfile((prev) =>
        prev ? { ...prev, projects: [...(prev.projects ?? []), ...fresh] } : prev,
      );
      setActiveSection("projects");
      sectionRefs.current["projects"]?.scrollIntoView({ behavior: "smooth", block: "start" });
      toast.success(
        `Imported ${fresh.length} project${fresh.length === 1 ? "" : "s"} from GitHub — review them and hit Save snapshot.`,
      );
    } catch (e: any) {
      toast.error(`GitHub import failed: ${e.message}`);
    } finally {
      setImportingGithub(false);
    }
  };

  return (
    <PageBody className="max-w-none">
      <PageHeader
        eyebrow="Assets · Master Profile"
        title={p.headline || `${p.first_name || "My"} Master Career Profile`}
        description="Edit your structured resume profile. All AI tailoring draws directly from these verified master entries."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleGithubImport} disabled={importingGithub}>
              {importingGithub ? "Importing..." : "Import from GitHub"}
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : "Save snapshot"}
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[240px_1fr] items-start">
        {/* Sidebar Navigation — opaque + layered under the TopBar so content
            scrolls beneath it instead of showing through */}
        <div className="sticky top-16 z-10 rounded-lg bg-background">
          <Panel title="Profile sections">
            <ul className="divide-y divide-border text-sm">
              {SECTIONS.map((s) => {
                const count =
                  s.id === "experience"
                    ? p.experiences?.length
                    : s.id === "education"
                    ? p.educations?.length
                    : s.id === "projects"
                    ? p.projects?.length
                    : s.id === "skills"
                    ? p.skills?.length
                    : s.id === "certifications"
                    ? p.certifications?.length
                    : null;

                return (
                  <li key={s.id}>
                    <button
                      type="button"
                      onClick={() => scrollToSection(s.id)}
                      className={`flex w-full items-center justify-between px-3 py-2.5 text-left transition-colors ${
                        activeSection === s.id
                          ? "bg-muted font-semibold text-foreground border-l-2 border-foreground"
                          : "text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                      }`}
                    >
                      <span>{s.label}</span>
                      {count !== null && count !== undefined ? (
                        <span className="font-mono text-[10px] bg-background px-1.5 py-0.5 rounded border border-border">
                          {count}
                        </span>
                      ) : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          </Panel>
        </div>

        {/* Main Content Panels */}
        <div className="min-w-0 space-y-6">
          {/* Header & Summary */}
          <div ref={(el) => { sectionRefs.current["header"] = el; }} className="scroll-mt-16">
            <Panel title="Header & Summary" description="Personal information and professional summary statement.">
              <div className="grid gap-4 p-4 sm:grid-cols-2">
                <div>
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">First Name</label>
                  <Input value={p.first_name ?? ""} onChange={(e) => updateField("first_name", e.target.value)} />
                </div>
                <div>
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">Last Name</label>
                  <Input value={p.last_name ?? ""} onChange={(e) => updateField("last_name", e.target.value)} />
                </div>
                <div className="sm:col-span-2">
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">Professional Headline</label>
                  <Input value={p.headline ?? ""} onChange={(e) => updateField("headline", e.target.value)} placeholder="e.g. Senior Full Stack Engineer · Distributed Systems" />
                </div>
                <div className="sm:col-span-2">
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">Professional Summary</label>
                  <Textarea value={p.summary ?? ""} onChange={(e) => updateField("summary", e.target.value)} rows={4} placeholder="High-level career overview, core engineering strengths, and scale achieved..." />
                </div>
                <div>
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">Email</label>
                  <Input value={p.email ?? ""} onChange={(e) => updateField("email", e.target.value)} />
                </div>
                <div>
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">Phone</label>
                  <Input value={p.phone ?? ""} onChange={(e) => updateField("phone", e.target.value)} />
                </div>
                <div>
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">Location</label>
                  <Input value={p.location ?? ""} onChange={(e) => updateField("location", e.target.value)} placeholder="San Francisco, CA" />
                </div>
                <div>
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">GitHub URL</label>
                  <Input value={p.github ?? ""} onChange={(e) => updateField("github", e.target.value)} placeholder="https://github.com/username" />
                </div>
                <div>
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">LinkedIn URL</label>
                  <Input value={p.linkedin ?? ""} onChange={(e) => updateField("linkedin", e.target.value)} placeholder="https://linkedin.com/in/username" />
                </div>
                <div>
                  <label className="text-[10px] font-semibold uppercase text-muted-foreground">Portfolio / Website</label>
                  <Input value={p.website ?? ""} onChange={(e) => updateField("website", e.target.value)} placeholder="https://yourportfolio.dev" />
                </div>
              </div>
            </Panel>
          </div>

          {/* Experience */}
          <div ref={(el) => { sectionRefs.current["experience"] = el; }} className="scroll-mt-16">
            <Panel
              title="Experience"
              description="Work history, internships, and research roles."
              actions={
                <Button variant="outline" size="sm" onClick={addExperience}>
                  <Plus className="mr-1 h-3.5 w-3.5" /> Add role
                </Button>
              }
            >
              <div className="divide-y divide-border">
                {(p.experiences ?? []).length === 0 ? (
                  <div className="p-6 text-center text-sm text-muted-foreground">No experience entries added yet. Click "+ Add role" to begin.</div>
                ) : (
                  p.experiences!.map((e, i) => (
                    <div key={e.id ?? i} className="space-y-4 p-4 relative group">
                      <div className="absolute right-4 top-4">
                        <Button variant="ghost" size="sm" onClick={() => removeExperience(i)} className="text-muted-foreground hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-3 pr-10">
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Company</label>
                          <Input value={e.company ?? ""} onChange={(ev) => updateExperience(i, "company", ev.target.value)} placeholder="Acme Corp" />
                        </div>
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Role Title</label>
                          <Input value={e.title ?? ""} onChange={(ev) => updateExperience(i, "title", ev.target.value)} placeholder="Senior Software Engineer" />
                        </div>
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Period</label>
                          <Input value={e.start_date ?? ""} onChange={(ev) => updateExperience(i, "start_date", ev.target.value)} placeholder="2021 – Present" />
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Achievements & Impact</label>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs text-[color:var(--brand)] gap-1 px-2"
                            onClick={() => handleStarPolish(i)}
                            disabled={polishingIndex === i}
                          >
                            <Sparkles className="h-3.5 w-3.5" />
                            {polishingIndex === i ? "Polishing..." : "✨ STAR Polish"}
                          </Button>
                        </div>
                        <Textarea
                          value={e.description ?? ""}
                          onChange={(ev) => updateExperience(i, "description", ev.target.value)}
                          rows={4}
                          placeholder="• Reduced database query latency by 45% using Redis caching...&#10;• Mentored 4 junior engineers..."
                        />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Panel>
          </div>

          {/* Education */}
          <div ref={(el) => { sectionRefs.current["education"] = el; }} className="scroll-mt-16">
            <Panel
              title="Education"
              description="Degrees, universities, and academic credentials."
              actions={
                <Button variant="outline" size="sm" onClick={addEducation}>
                  <Plus className="mr-1 h-3.5 w-3.5" /> Add education
                </Button>
              }
            >
              <div className="divide-y divide-border">
                {(p.educations ?? []).length === 0 ? (
                  <div className="p-6 text-center text-sm text-muted-foreground">No education entries added yet.</div>
                ) : (
                  p.educations!.map((ed, i) => (
                    <div key={ed.id ?? i} className="space-y-3 p-4 relative group">
                      <div className="absolute right-4 top-4">
                        <Button variant="ghost" size="sm" onClick={() => removeEducation(i)} className="text-muted-foreground hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-3 pr-10">
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Institution</label>
                          <Input value={ed.institution ?? ""} onChange={(ev) => updateEducation(i, "institution", ev.target.value)} placeholder="Stanford University" />
                        </div>
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Degree / Major</label>
                          <Input value={ed.degree ?? ""} onChange={(ev) => updateEducation(i, "degree", ev.target.value)} placeholder="B.S. Computer Science" />
                        </div>
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Graduation Period</label>
                          <Input value={ed.end_date ?? ""} onChange={(ev) => updateEducation(i, "end_date", ev.target.value)} placeholder="2017 – 2021" />
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Panel>
          </div>

          {/* Projects */}
          <div ref={(el) => { sectionRefs.current["projects"] = el; }} className="scroll-mt-16">
            <Panel
              title="Projects"
              description="Notable open-source contributions, side projects, and systems built."
              actions={
                <Button variant="outline" size="sm" onClick={addProject}>
                  <Plus className="mr-1 h-3.5 w-3.5" /> Add project
                </Button>
              }
            >
              <div className="divide-y divide-border">
                {(p.projects ?? []).length === 0 ? (
                  <div className="p-6 text-center text-sm text-muted-foreground">No projects added yet.</div>
                ) : (
                  p.projects!.map((pr, i) => (
                    <div key={pr.id ?? i} className="space-y-3 p-4 relative group">
                      <div className="absolute right-4 top-4">
                        <Button variant="ghost" size="sm" onClick={() => removeProject(i)} className="text-muted-foreground hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2 pr-10">
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Project Name</label>
                          <Input value={pr.name ?? ""} onChange={(ev) => updateProject(i, "name", ev.target.value)} placeholder="Distributed Task Queue" />
                        </div>
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">URL / Repo</label>
                          <Input value={pr.url ?? ""} onChange={(ev) => updateProject(i, "url", ev.target.value)} placeholder="https://github.com/user/repo" />
                        </div>
                      </div>
                      <div>
                        <label className="text-[10px] font-semibold uppercase text-muted-foreground">Description & Tech Stack</label>
                        <Textarea value={pr.description ?? ""} onChange={(ev) => updateProject(i, "description", ev.target.value)} rows={2} placeholder="Built with Python, Redis, and WebSockets. Handles 10k jobs/sec." />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Panel>
          </div>

          {/* Skills */}
          <div ref={(el) => { sectionRefs.current["skills"] = el; }} className="scroll-mt-16">
            <Panel
              title="Skills"
              description="Technical proficiencies, frameworks, and tools."
              actions={
                <Button variant="outline" size="sm" onClick={addSkill}>
                  <Plus className="mr-1 h-3.5 w-3.5" /> Add skill
                </Button>
              }
            >
              <div className="flex flex-wrap gap-2 p-4">
                {(p.skills ?? []).length === 0 ? (
                  <span className="text-sm text-muted-foreground">No skills added yet.</span>
                ) : (
                  p.skills!.map((s, i) => (
                    <div key={s.id ?? s.name} className="inline-flex items-center gap-1 rounded bg-muted px-2 py-1 font-mono text-xs text-foreground">
                      <span>{s.name}</span>
                      {s.category && <span className="text-[10px] text-muted-foreground">({s.category})</span>}
                      <button type="button" onClick={() => removeSkill(i)} className="ml-1 text-muted-foreground hover:text-destructive font-bold">
                        ×
                      </button>
                    </div>
                  ))
                )}
              </div>
            </Panel>
          </div>

          {/* Certifications */}
          <div ref={(el) => { sectionRefs.current["certifications"] = el; }} className="scroll-mt-16">
            <Panel
              title="Certifications"
              description="Industry certifications and credentials."
              actions={
                <Button variant="outline" size="sm" onClick={addCert}>
                  <Plus className="mr-1 h-3.5 w-3.5" /> Add certification
                </Button>
              }
            >
              <div className="divide-y divide-border">
                {(p.certifications ?? []).length === 0 ? (
                  <div className="p-6 text-center text-sm text-muted-foreground">No certifications added yet.</div>
                ) : (
                  p.certifications!.map((c, i) => (
                    <div key={c.id ?? i} className="space-y-3 p-4 relative group">
                      <div className="absolute right-4 top-4">
                        <Button variant="ghost" size="sm" onClick={() => removeCert(i)} className="text-muted-foreground hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2 pr-10">
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Certification Name</label>
                          <Input value={c.name ?? ""} onChange={(ev) => updateCert(i, "name", ev.target.value)} placeholder="AWS Certified Solutions Architect" />
                        </div>
                        <div>
                          <label className="text-[10px] font-semibold uppercase text-muted-foreground">Issuer</label>
                          <Input value={c.issuer ?? ""} onChange={(ev) => updateCert(i, "issuer", ev.target.value)} placeholder="Amazon Web Services" />
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Panel>
          </div>
        </div>
      </div>
      {promptDialog && (
        <PromptDialog
          config={promptDialog}
          resolve={(v) => {
            promptDialog.resolve(v);
            setPromptDialog(null);
          }}
        />
      )}
    </PageBody>
  );
}
