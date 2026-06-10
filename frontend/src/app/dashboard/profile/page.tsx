"use client";

import { useEffect, useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { getProfile, updateProfile } from '@/lib/api/profiles';
import { Profile } from '@/types/profile';
import { Plus, Trash2, Loader2, CheckCircle2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

// --- Zod Schemas ---
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

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      experiences: [],
      educations: [],
      skills: [],
      projects: [],
      certifications: [],
    },
  });

  const { register, control, watch, reset, handleSubmit } = form;

  // Field Arrays
  const experiencesArray = useFieldArray({ control, name: "experiences" });
  const educationsArray = useFieldArray({ control, name: "educations" });
  const skillsArray = useFieldArray({ control, name: "skills" });
  const projectsArray = useFieldArray({ control, name: "projects" });
  const certificationsArray = useFieldArray({ control, name: "certifications" });

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          router.push('/login');
          return;
        }
        const data = await getProfile(token);
        
        // ensure nulls are correctly mapped
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
      } catch (err) {
        console.error('Failed to load profile', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [reset, router]);

  // Autosave logic
  useEffect(() => {
    const subscription = watch((value) => {
      // Debounce the save
      const timeoutId = setTimeout(async () => {
        try {
          const isValid = await form.trigger(); // Trigger validation
          if (isValid) {
            setSaving(true);
            const token = localStorage.getItem('token');
            if (token) {
               // We assert as any here because of partial types in watch payload
              await updateProfile(token, form.getValues() as Profile);
              setLastSaved(new Date());
            }
          }
        } catch (error) {
          console.error("Autosave failed", error);
        } finally {
          setSaving(false);
        }
      }, 1500); // 1.5 seconds debounce

      return () => clearTimeout(timeoutId);
    });
    return () => subscription.unsubscribe();
  }, [watch, form]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Resume Profile</h1>
        <div className="flex items-center text-sm text-slate-500">
          {saving ? (
            <span className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Saving...</span>
          ) : lastSaved ? (
            <span className="flex items-center gap-2 text-green-600"><CheckCircle2 className="w-4 h-4" /> Saved at {lastSaved.toLocaleTimeString()}</span>
          ) : (
             <span>All changes saved automatically</span>
          )}
        </div>
      </div>

      <form className="space-y-12">
        {/* Personal Information */}
        <section className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-xl font-semibold mb-4 text-slate-800">Personal Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">First Name</label>
              <input type="text" {...register("first_name")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Last Name</label>
              <input type="text" {...register("last_name")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700">Headline</label>
              <input type="text" {...register("headline")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" placeholder="e.g. Senior Software Engineer" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700">Summary</label>
              <textarea {...register("summary")} rows={4} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"></textarea>
            </div>
          </div>
        </section>

        {/* Contact Information */}
        <section className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-xl font-semibold mb-4 text-slate-800">Contact Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Email</label>
              <input type="email" {...register("email")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Phone</label>
              <input type="tel" {...register("phone")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Location</label>
              <input type="text" {...register("location")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" placeholder="City, State" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">LinkedIn</label>
              <input type="url" {...register("linkedin")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">GitHub</label>
              <input type="url" {...register("github")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Personal Website</label>
              <input type="url" {...register("website")} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
            </div>
          </div>
        </section>

        {/* Experience Section */}
        <section className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-slate-800">Experience</h2>
            <button
              type="button"
              onClick={() => experiencesArray.append({ title: '', company: '', is_current: false })}
              className="text-sm flex items-center text-purple-600 hover:text-purple-700 font-medium"
            >
              <Plus className="w-4 h-4 mr-1" /> Add Experience
            </button>
          </div>
          <div className="space-y-6">
            {experiencesArray.fields.map((field, index) => (
              <div key={field.id} className="p-4 border border-slate-100 rounded-lg bg-slate-50/50 relative">
                <button
                  type="button"
                  onClick={() => experiencesArray.remove(index)}
                  className="absolute top-4 right-4 text-slate-400 hover:text-red-500"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Job Title *</label>
                    <input type="text" {...register(`experiences.${index}.title`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Company *</label>
                    <input type="text" {...register(`experiences.${index}.company`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Location</label>
                    <input type="text" {...register(`experiences.${index}.location`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  </div>
                  <div className="flex items-center space-x-4 mt-6">
                    <label className="flex items-center text-sm font-medium text-slate-700">
                      <input type="checkbox" {...register(`experiences.${index}.is_current`)} className="mr-2 rounded border-slate-300 text-purple-600" />
                      Current Role
                    </label>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Start Date</label>
                    <input type="date" {...register(`experiences.${index}.start_date`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">End Date</label>
                    <input type="date" {...register(`experiences.${index}.end_date`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" disabled={watch(`experiences.${index}.is_current`)} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-slate-700">Description</label>
                    <textarea {...register(`experiences.${index}.description`)} rows={4} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"></textarea>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Education Section */}
        <section className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-slate-800">Education</h2>
            <button
              type="button"
              onClick={() => educationsArray.append({ institution: '' })}
              className="text-sm flex items-center text-purple-600 hover:text-purple-700 font-medium"
            >
              <Plus className="w-4 h-4 mr-1" /> Add Education
            </button>
          </div>
          <div className="space-y-6">
            {educationsArray.fields.map((field, index) => (
              <div key={field.id} className="p-4 border border-slate-100 rounded-lg bg-slate-50/50 relative">
                <button
                  type="button"
                  onClick={() => educationsArray.remove(index)}
                  className="absolute top-4 right-4 text-slate-400 hover:text-red-500"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-slate-700">Institution *</label>
                    <input type="text" {...register(`educations.${index}.institution`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Degree</label>
                    <input type="text" {...register(`educations.${index}.degree`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="e.g. B.S." />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Field of Study</label>
                    <input type="text" {...register(`educations.${index}.field_of_study`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="e.g. Computer Science" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Start Date</label>
                    <input type="date" {...register(`educations.${index}.start_date`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">End Date (Expected)</label>
                    <input type="date" {...register(`educations.${index}.end_date`)} className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Skills Section */}
        <section className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-slate-800">Skills</h2>
            <button
              type="button"
              onClick={() => skillsArray.append({ name: '' })}
              className="text-sm flex items-center text-purple-600 hover:text-purple-700 font-medium"
            >
              <Plus className="w-4 h-4 mr-1" /> Add Skill
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {skillsArray.fields.map((field, index) => (
              <div key={field.id} className="flex items-center space-x-2">
                <input type="text" {...register(`skills.${index}.name`)} placeholder="Skill name" className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" />
                <button type="button" onClick={() => skillsArray.remove(index)} className="text-slate-400 hover:text-red-500">
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        </section>

      </form>
    </div>
  );
}
