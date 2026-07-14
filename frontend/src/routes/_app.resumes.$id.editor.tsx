import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useCallback } from "react";
import { useDebouncedCallback } from "use-debounce";
import { getProfile, updateProfile } from "@/lib/api/profiles";
import { Profile, Experience, Education, Skill, Project, Certification } from "@/types/profile";
import SectionCard from "@/components/custom/SectionCard";
import ArrayItem from "@/components/custom/ArrayItem";
import Input from "@/components/custom/Input";
import Textarea from "@/components/custom/Textarea";
import ValidationDisplay from "@/components/custom/ValidationDisplay";
import { validateProfile } from "@/lib/validation/profile";

export const Route = createFileRoute("/_app/resumes/$id/editor")({
  component: ResumeEditorPage,
});

function ResumeEditorPage() {
  const { id } = Route.useParams();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const data = await getProfile();
        setProfile(data);
      } catch (error) {
        console.error("Failed to load profile:", error);
      } finally {
        setLoading(false);
      }
    };
    loadProfile();
  }, []);

  const debouncedSave = useCallback(
    useDebouncedCallback(async (profileData: Profile) => {
      if (!profileData) return;
      setSaveStatus("saving");
      try {
        const validationErrors = validateProfile(profileData);
        if (Object.keys(validationErrors).length > 0) {
          setErrors(validationErrors);
          setSaveStatus("error");
          return;
        }
        setErrors({});
        const updated = await updateProfile(profileData);
        setProfile(updated);
        setSaveStatus("saved");
        setTimeout(() => setSaveStatus("idle"), 2000);
      } catch (error) {
        console.error("Failed to save profile:", error);
        setSaveStatus("error");
      }
    }, 1000),
    [],
  );

  const handleFieldChange = (field: keyof Profile, value: any) => {
    if (!profile) return;
    const updated = { ...profile, [field]: value };
    setProfile(updated);
    debouncedSave(updated);
  };

  const handleArrayChange = <T extends Experience | Education | Skill | Project | Certification>(
    field: keyof Profile,
    index: number,
    subField: keyof T,
    value: any,
  ) => {
    if (!profile) return;
    const array = [...(profile[field] as T[])];
    array[index] = { ...array[index], [subField]: value };
    const updated = { ...profile, [field]: array };
    setProfile(updated);
    debouncedSave(updated);
  };

  const handleAddItem = <T extends Experience | Education | Skill | Project | Certification>(
    field: keyof Profile,
    template: T,
  ) => {
    if (!profile) return;
    const array = [...(profile[field] as T[]), template];
    const updated = { ...profile, [field]: array };
    setProfile(updated);
    debouncedSave(updated);
  };

  const handleRemoveItem = (field: keyof Profile, index: number) => {
    if (!profile) return;
    const array = [...(profile[field] as any[])];
    array.splice(index, 1);
    const updated = { ...profile, [field]: array };
    setProfile(updated);
    debouncedSave(updated);
  };

  if (loading) return <div>Loading...</div>;
  if (!profile) return <div>Error loading profile.</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Edit Resume Profile ({id})</h1>
      <div
        className={`mb-4 ${saveStatus === "saved" ? "text-green-600" : saveStatus === "error" ? "text-red-600" : ""}`}
      >
        Status: {saveStatus}
      </div>
      {Object.keys(errors).length > 0 && <ValidationDisplay errors={errors} />}

      <SectionCard title="Personal Information" defaultOpen={true}>
        <Input
          label="First Name"
          value={profile.first_name || ""}
          onChange={(v) => handleFieldChange("first_name", v)}
        />
        <Input
          label="Last Name"
          value={profile.last_name || ""}
          onChange={(v) => handleFieldChange("last_name", v)}
        />
        <Input
          label="Headline"
          value={profile.headline || ""}
          onChange={(v) => handleFieldChange("headline", v)}
        />
        <Textarea
          label="Summary"
          value={profile.summary || ""}
          onChange={(v) => handleFieldChange("summary", v)}
        />
      </SectionCard>
      <SectionCard title="Work Experience">
        {profile.experiences.map((exp, index) => (
          <ArrayItem
            key={index}
            item={exp}
            index={index}
            onChange={(subField, value) =>
              handleArrayChange("experiences", index, subField as keyof Experience, value)
            }
            onRemove={() => handleRemoveItem("experiences", index)}
            fields={[
              { label: "Title", name: "title", required: true, maxLength: 255 },
              { label: "Company", name: "company", required: true, maxLength: 255 },
              { label: "Location", name: "location", maxLength: 255 },
              { label: "Start Date", name: "start_date", type: "date" },
              { label: "End Date", name: "end_date", type: "date" },
              { label: "Current", name: "is_current", type: "checkbox" },
              { label: "Description", name: "description", type: "textarea", rows: 3 },
            ]}
          />
        ))}
        <button
          onClick={() =>
            handleAddItem("experiences", {
              title: "",
              company: "",
              is_current: false,
            } as Experience)
          }
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Experience
        </button>
      </SectionCard>

      <SectionCard title="Education">
        {profile.educations.map((edu, index) => (
          <ArrayItem
            key={index}
            item={edu}
            index={index}
            onChange={(subField, value) =>
              handleArrayChange("educations", index, subField as keyof Education, value)
            }
            onRemove={() => handleRemoveItem("educations", index)}
            fields={[
              { label: "Institution", name: "institution", required: true, maxLength: 255 },
              { label: "Degree", name: "degree", maxLength: 255 },
              { label: "Field of Study", name: "field_of_study", maxLength: 255 },
              { label: "Start Date", name: "start_date", type: "date" },
              { label: "End Date", name: "end_date", type: "date" },
              { label: "Description", name: "description", type: "textarea", rows: 2 },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem("educations", { institution: "" } as Education)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Education
        </button>
      </SectionCard>

      <SectionCard title="Skills">
        {profile.skills.map((skill, index) => (
          <ArrayItem
            key={index}
            item={skill}
            index={index}
            onChange={(subField, value) =>
              handleArrayChange("skills", index, subField as keyof Skill, value)
            }
            onRemove={() => handleRemoveItem("skills", index)}
            fields={[
              { label: "Skill Name", name: "name", required: true, maxLength: 100 },
              { label: "Category", name: "category", maxLength: 100 },
              { label: "Proficiency", name: "proficiency", maxLength: 50 },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem("skills", { name: "" } as Skill)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Skill
        </button>
      </SectionCard>

      <SectionCard title="Projects">
        {profile.projects.map((project, index) => (
          <ArrayItem
            key={index}
            item={project}
            index={index}
            onChange={(subField, value) =>
              handleArrayChange("projects", index, subField as keyof Project, value)
            }
            onRemove={() => handleRemoveItem("projects", index)}
            fields={[
              { label: "Project Name", name: "name", required: true, maxLength: 255 },
              { label: "Description", name: "description", type: "textarea", rows: 2 },
              { label: "URL", name: "url", maxLength: 255 },
              { label: "Start Date", name: "start_date", type: "date" },
              { label: "End Date", name: "end_date", type: "date" },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem("projects", { name: "" } as Project)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Project
        </button>
      </SectionCard>

      <SectionCard title="Certifications">
        {profile.certifications.map((cert, index) => (
          <ArrayItem
            key={index}
            item={cert}
            index={index}
            onChange={(subField, value) =>
              handleArrayChange("certifications", index, subField as keyof Certification, value)
            }
            onRemove={() => handleRemoveItem("certifications", index)}
            fields={[
              { label: "Certification Name", name: "name", required: true, maxLength: 255 },
              { label: "Issuer", name: "issuer", required: true, maxLength: 255 },
              { label: "Issue Date", name: "issue_date", type: "date" },
              { label: "Expiration Date", name: "expiration_date", type: "date" },
              { label: "Credential ID", name: "credential_id", maxLength: 255 },
              { label: "Credential URL", name: "credential_url", maxLength: 255 },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem("certifications", { name: "", issuer: "" } as Certification)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Certification
        </button>
      </SectionCard>
    </div>
  );
}
