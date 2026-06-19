"use client";

import { useEffect, useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { getProfile, updateProfile } from '@/lib/api/profiles';
import { Profile } from '@/types/profile';
import { useRouter } from 'next/navigation';

const experienceSchema = z.object({
  id: z.string().optional(),
  title: z.string().min(1, "Title is required"),
  company: z.string().min(1, "Company is required"),
  location: z.string().nullable().optional(),
  start_date: z.string().nullable().optional(),
  end_date: z.string().nullable().optional(),
  is_current: z.boolean().default(false),
  description: z.string().nullable().optional(),
});

const educationSchema = z.object({
  id: z.string().optional(),
  institution: z.string().min(1, "Institution is required"),
  degree: z.string().nullable().optional(),
  field_of_study: z.string().nullable().optional(),
  start_date: z.string().nullable().optional(),
  end_date: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
});

const skillSchema = z.object({
  id: z.string().optional(),
  name: z.string().min(1, "Skill name is required"),
  category: z.string().nullable().optional(),
  proficiency: z.string().nullable().optional(),
});

const projectSchema = z.object({
  id: z.string().optional(),
  name: z.string().min(1, "Project name is required"),
  description: z.string().nullable().optional(),
  url: z.string().nullable().optional(),
  start_date: z.string().nullable().optional(),
  end_date: z.string().nullable().optional(),
});

const certificationSchema = z.object({
  id: z.string().optional(),
  name: z.string().min(1, "Certification name is required"),
  issuer: z.string().min(1, "Issuer is required"),
  issue_date: z.string().nullable().optional(),
  expiration_date: z.string().nullable().optional(),
  credential_id: z.string().nullable().optional(),
  credential_url: z.string().nullable().optional(),
});

const profileSchema = z.object({
  id: z.string().optional(),
  first_name: z.string().nullable().optional(),
  last_name: z.string().nullable().optional(),
  headline: z.string().nullable().optional(),
  summary: z.string().nullable().optional(),
  email: z.string().email("Invalid email").nullable().optional().or(z.literal("")),
  phone: z.string().nullable().optional(),
  location: z.string().nullable().optional(),
  website: z.string().url("Invalid URL").nullable().optional().or(z.literal("")),
  linkedin: z.string().url("Invalid URL").nullable().optional().or(z.literal("")),
  github: z.string().url("Invalid URL").nullable().optional().or(z.literal("")),
  experiences: z.array(experienceSchema),
  educations: z.array(educationSchema),
  skills: z.array(skillSchema),
  projects: z.array(projectSchema),
  certifications: z.array(certificationSchema),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

const Input = (props: React.InputHTMLAttributes<HTMLInputElement>) => (
  <input {...props}
    className={`mt-1 block w-full rounded-md border border-border bg-background-primary px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand transition-colors ${props.className || ''}`}
  />
);

const Textarea = (props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) => (
  <textarea {...props}
    className={`mt-1 block w-full rounded-md border border-border bg-background-primary px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand transition-colors resize-y ${props.className || ''}`}
  />
);

const SectionCard = ({ title, children, onAdd, addLabel }: { title: string; children: React.ReactNode; onAdd?: () => void; addLabel?: string }) => (
  <section className="bg-background-secondary border border-border rounded-lg overflow-hidden">
    <div className="px-6 py-4 border-b border-border flex items-center justify-between">
      <h2 className="text-base font-semibold text-text-primary">{title}</h2>
      {onAdd && addLabel && (
        <button type="button" onClick={onAdd}
          className="text-sm text-brand hover:text-brand/80 font-medium transition-colors"
        >
          + {addLabel}
        </button>
      )}
    </div>
    <div className="p-6">
      {children}
    </div>
  </section>
);

const ArrayItem = ({ children, onRemove }: { children: React.ReactNode; onRemove: () => void }) => (
  <div className="p-5 border border-border-light rounded-lg bg-background-muted/50 relative group">
    <button type="button" onClick={onRemove}
      className="absolute top-3 right-3 text-text-muted hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
      </svg>
    </button>
    {children}
  </div>
);

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { experiences: [], educations: [], skills: [], projects: [], certifications: [] },
  });

  const { register, control, watch, reset, formState: { errors } } = form;

  const experiencesArray = useFieldArray({ control, name: "experiences" });
  const educationsArray = useFieldArray({ control, name: "educations" });
  const skillsArray = useFieldArray({ control, name: "skills" });
  const projectsArray = useFieldArray({ control, name: "projects" });
  const certificationsArray = useFieldArray({ control, name: "certifications" });

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) { router.push('/login'); return; }
        const data = await getProfile(token);
        reset({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          headline: data.headline || "",
          summary: data.summary || "",
          email: data.email || "",
          phone: data.phone || "",
          location: data.location || "",
          website: data.website || "",
          linkedin: data.linkedin || "",
          github: data.github || "",
          experiences: data.experiences || [],
          educations: data.educations || [],
          skills: data.skills || [],
          projects: data.projects || [],
          certifications: data.certifications || [],
        });
      } catch (err) { console.error('Failed to load profile', err); }
      finally { setLoading(false); }
    };
    fetchProfile();
  }, [reset, router]);

  useEffect(() => {
    const subscription = watch((value) => {
      const timeoutId = setTimeout(async () => {
        try {
          const isValid = await form.trigger();
          if (isValid) {
            setSaving(true);
            const token = localStorage.getItem('token');
            if (token) {
              await updateProfile(token, form.getValues() as Profile);
              setLastSaved(new Date());
            }
          }
        } catch (error) { console.error("Autosave failed", error); }
        finally { setSaving(false); }
      }, 1500);
      return () => clearTimeout(timeoutId);
    });
    return () => subscription.unsubscribe();
  }, [watch, form]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="w-10 h-10 border-4 border-brand border-t-transparent rounded-full animate-spin"/>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Resume Profile</h1>
          <p className="text-sm text-text-secondary mt-1">Your profile data is used to tailor resumes and score job matches</p>
        </div>
        <div className="flex items-center text-sm text-text-muted">
          {saving ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin w-4 h-4 text-brand" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/>
                <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="4" strokeLinecap="round" className="opacity-75"/>
              </svg>
              Saving...
            </span>
          ) : lastSaved ? (
            <span className="flex items-center gap-1.5 text-green-600">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
              Saved at {lastSaved.toLocaleTimeString()}
            </span>
          ) : (
            <span>All changes saved automatically</span>
          )}
        </div>
      </div>

      <form className="space-y-8">
        {/* Personal Information */}
        <SectionCard title="Personal Information">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary">First Name</label>
              <Input type="text" {...register("first_name")} />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary">Last Name</label>
              <Input type="text" {...register("last_name")} />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-primary">Headline</label>
              <Input type="text" {...register("headline")} placeholder="e.g. Senior Software Engineer" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-primary">Summary</label>
              <Textarea {...register("summary")} rows={4}/>
            </div>
          </div>
        </SectionCard>

        {/* Contact Information */}
        <SectionCard title="Contact Information">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary">Email</label>
              <Input type="email" {...register("email")} />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary">Phone</label>
              <Input type="tel" {...register("phone")} />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary">Location</label>
              <Input type="text" {...register("location")} placeholder="City, State" />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary">LinkedIn</label>
              <Input type="url" {...register("linkedin")} />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary">GitHub</label>
              <Input type="url" {...register("github")} />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary">Personal Website</label>
              <Input type="url" {...register("website")} />
            </div>
          </div>
        </SectionCard>

        {/* Experience */}
        <SectionCard title="Experience" onAdd={() => experiencesArray.append({ title: '', company: '', is_current: false })} addLabel="Add Experience">
          <div className="space-y-4">
            {experiencesArray.fields.map((field, index) => (
              <ArrayItem key={field.id} onRemove={() => experiencesArray.remove(index)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Job Title *</label>
                    <Input type="text" {...register(`experiences.${index}.title`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Company *</label>
                    <Input type="text" {...register(`experiences.${index}.company`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Location</label>
                    <Input type="text" {...register(`experiences.${index}.location`)} />
                  </div>
                  <div className="flex items-center gap-4 pt-2">
                    <label className="flex items-center gap-2 text-sm font-medium text-text-primary">
                      <input type="checkbox" {...register(`experiences.${index}.is_current`)}
                        className="accent-brand rounded border-border"/>
                      Current Role
                    </label>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Start Date</label>
                    <Input type="date" {...register(`experiences.${index}.start_date`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">End Date</label>
                    <Input type="date" {...register(`experiences.${index}.end_date`)} disabled={watch(`experiences.${index}.is_current`)} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-text-primary">Description</label>
                    <Textarea {...register(`experiences.${index}.description`)} rows={3}/>
                  </div>
                </div>
              </ArrayItem>
            ))}
            {experiencesArray.fields.length === 0 && (
              <p className="text-sm text-text-muted text-center py-6">No experience added yet.</p>
            )}
          </div>
        </SectionCard>

        {/* Education */}
        <SectionCard title="Education" onAdd={() => educationsArray.append({ institution: '' })} addLabel="Add Education">
          <div className="space-y-4">
            {educationsArray.fields.map((field, index) => (
              <ArrayItem key={field.id} onRemove={() => educationsArray.remove(index)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-text-primary">Institution *</label>
                    <Input type="text" {...register(`educations.${index}.institution`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Degree</label>
                    <Input type="text" {...register(`educations.${index}.degree`)} placeholder="e.g. B.S." />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Field of Study</label>
                    <Input type="text" {...register(`educations.${index}.field_of_study`)} placeholder="e.g. Computer Science" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Start Date</label>
                    <Input type="date" {...register(`educations.${index}.start_date`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">End Date (Expected)</label>
                    <Input type="date" {...register(`educations.${index}.end_date`)} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-text-primary">Description</label>
                    <Textarea {...register(`educations.${index}.description`)} rows={3}/>
                  </div>
                </div>
              </ArrayItem>
            ))}
            {educationsArray.fields.length === 0 && (
              <p className="text-sm text-text-muted text-center py-6">No education added yet.</p>
            )}
          </div>
        </SectionCard>

        {/* Skills */}
        <SectionCard title="Skills" onAdd={() => skillsArray.append({ name: '' })} addLabel="Add Skill">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {skillsArray.fields.map((field, index) => (
              <div key={field.id} className="flex items-center gap-2 group">
                <Input type="text" {...register(`skills.${index}.name`)} placeholder="Skill name" className="flex-1"/>
                <div className="flex-1">
                  <select {...register(`skills.${index}.proficiency`)}
                    className="w-full rounded-md border border-border bg-background-primary px-3 py-2.5 text-sm text-text-primary focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand transition-colors">
                    <option value="">Level</option>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                    <option value="expert">Expert</option>
                  </select>
                </div>
                <button type="button" onClick={() => skillsArray.remove(index)}
                  className="text-text-muted hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity p-1">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            ))}
            {skillsArray.fields.length === 0 && (
              <p className="text-sm text-text-muted text-center py-6 col-span-2">No skills added yet.</p>
            )}
          </div>
        </SectionCard>

        {/* Projects */}
        <SectionCard title="Projects" onAdd={() => projectsArray.append({ name: '' })} addLabel="Add Project">
          <div className="space-y-4">
            {projectsArray.fields.map((field, index) => (
              <ArrayItem key={field.id} onRemove={() => projectsArray.remove(index)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-text-primary">Project Name *</label>
                    <Input type="text" {...register(`projects.${index}.name`)} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-text-primary">Description</label>
                    <Textarea {...register(`projects.${index}.description`)} rows={3}/>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">URL</label>
                    <Input type="url" {...register(`projects.${index}.url`)} placeholder="https://" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Start Date</label>
                    <Input type="date" {...register(`projects.${index}.start_date`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">End Date</label>
                    <Input type="date" {...register(`projects.${index}.end_date`)} />
                  </div>
                </div>
              </ArrayItem>
            ))}
            {projectsArray.fields.length === 0 && (
              <p className="text-sm text-text-muted text-center py-6">No projects added yet.</p>
            )}
          </div>
        </SectionCard>

        {/* Certifications */}
        <SectionCard title="Certifications" onAdd={() => certificationsArray.append({ name: '', issuer: '' })} addLabel="Add Certification">
          <div className="space-y-4">
            {certificationsArray.fields.map((field, index) => (
              <ArrayItem key={field.id} onRemove={() => certificationsArray.remove(index)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Certification Name *</label>
                    <Input type="text" {...register(`certifications.${index}.name`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Issuer *</label>
                    <Input type="text" {...register(`certifications.${index}.issuer`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Issue Date</label>
                    <Input type="date" {...register(`certifications.${index}.issue_date`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Expiration Date</label>
                    <Input type="date" {...register(`certifications.${index}.expiration_date`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Credential ID</label>
                    <Input type="text" {...register(`certifications.${index}.credential_id`)} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary">Credential URL</label>
                    <Input type="url" {...register(`certifications.${index}.credential_url`)} placeholder="https://" />
                  </div>
                </div>
              </ArrayItem>
            ))}
            {certificationsArray.fields.length === 0 && (
              <p className="text-sm text-text-muted text-center py-6">No certifications added yet.</p>
            )}
          </div>
        </SectionCard>
      </form>
    </div>
  );
}
