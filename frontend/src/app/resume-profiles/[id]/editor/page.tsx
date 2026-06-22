'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useDebouncedCallback } from 'use-debounce';
import { useAuth } from '@/contexts/AuthContext';
import { getProfile, updateProfile } from '@/lib/api/profiles';
import { Profile, Experience, Education, Skill, Project, Certification } from '@/types/profile';
import SectionCard from '@/components/SectionCard';
import ArrayItem from '@/components/ArrayItem';
import Input from '@/components/Input';
import Textarea from '@/components/Textarea';
import ValidationDisplay from '@/components/ValidationDisplay';
import { validateProfile } from '@/lib/validation/profile';

export default function ProfileEditorPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load profile on mount
  useEffect(() => {
    if (!token) return;
    
    const loadProfile = async () => {
      try {
        const data = await getProfile(token);
        setProfile(data);
      } catch (error) {
        console.error('Failed to load profile:', error);
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, [token]);

  // Debounced save function using use-debounce
  const debouncedSave = useCallback(
    useDebouncedCallback(async (profileData: Profile) => {
      if (!token || !profileData) return;
      
      setSaving(true);
      setSaveStatus('saving');
      
      try {
        const validationErrors = validateProfile(profileData);
        if (Object.keys(validationErrors).length > 0) {
          setErrors(validationErrors);
          setSaveStatus('error');
          return;
        }
        
        setErrors({});
        const updated = await updateProfile(token, profileData);
        setProfile(updated);
        setSaveStatus('saved');
        
        // Reset to idle after 2 seconds
        setTimeout(() => setSaveStatus('idle'), 2000);
      } catch (error) {
        console.error('Failed to save profile:', error);
        setSaveStatus('error');
      } finally {
        setSaving(false);
      }
    }, 1000), // 1 second debounce
    [token]
  );

  // Handle profile field changes
  const handleFieldChange = (field: keyof Profile, value: any) => {
    if (!profile) return;
    
    const updated = { ...profile, [field]: value };
    setProfile(updated);
    debouncedSave(updated);
  };

  // Handle array item changes (experiences, educations, etc.)
  const handleArrayChange = <T extends Experience | Education | Skill | Project | Certification>(
    field: keyof Profile,
    index: number,
    subField: keyof T,
    value: any
  ) => {
    if (!profile) return;
    
    const array = [...(profile[field] as T[])];
    array[index] = { ...array[index], [subField]: value };
    
    const updated = { ...profile, [field]: array };
    setProfile(updated);
    debouncedSave(updated);
  };

  // Add new array item
  const handleAddItem = <T extends Experience | Education | Skill | Project | Certification>(
    field: keyof Profile,
    template: T
  ) => {
    if (!profile) return;
    
    const array = [...(profile[field] as T[]), template];
    const updated = { ...profile, [field]: array };
    setProfile(updated);
    debouncedSave(updated);
  };

  // Remove array item
  const handleRemoveItem = (field: keyof Profile, index: number) => {
    if (!profile) return;
    
    const array = [...(profile[field] as any[])];
    array.splice(index, 1);
    
    const updated = { ...profile, [field]: array };
    setProfile(updated);
    debouncedSave(updated);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-text-primary mb-6">Create Profile</h1>
        <div className="bg-background-secondary border border-border rounded-lg p-6">
          <p className="text-text-secondary">Creating new profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-text-primary">Edit Resume Profile</h1>
        <div className="flex items-center gap-3">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            saveStatus === 'idle' ? 'bg-gray-100 text-gray-600' :
            saveStatus === 'saving' ? 'bg-yellow-100 text-yellow-800' :
            saveStatus === 'saved' ? 'bg-green-100 text-green-800' :
            'bg-red-100 text-red-800'
          }`}>
            {saveStatus === 'idle' ? 'Ready' :
             saveStatus === 'saving' ? 'Saving...' :
             saveStatus === 'saved' ? 'Saved' :
             'Error saving'}
          </div>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 border border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
          >
            Back
          </button>
        </div>
      </div>

      {Object.keys(errors).length > 0 && (
        <ValidationDisplay errors={errors} />
      )}

      {/* Personal Information Section */}
      <SectionCard title="Personal Information" defaultOpen={true}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="First Name"
            value={profile.first_name || ''}
            onChange={(value) => handleFieldChange('first_name', value)}
            maxLength={255}
            placeholder="John"
          />
          <Input
            label="Last Name"
            value={profile.last_name || ''}
            onChange={(value) => handleFieldChange('last_name', value)}
            maxLength={255}
            placeholder="Doe"
          />
          <div className="md:col-span-2">
            <Input
              label="Headline"
              value={profile.headline || ''}
              onChange={(value) => handleFieldChange('headline', value)}
              maxLength={255}
              placeholder="Software Engineer"
            />
          </div>
          <div className="md:col-span-2">
            <Textarea
              label="Summary"
              value={profile.summary || ''}
              onChange={(value) => handleFieldChange('summary', value)}
              rows={4}
              placeholder="Brief summary about your professional background and career goals..."
            />
          </div>
        </div>
      </SectionCard>

      {/* Contact Information Section */}
      <SectionCard title="Contact Information">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Email"
            type="email"
            value={profile.email || ''}
            onChange={(value) => handleFieldChange('email', value)}
            maxLength={255}
            placeholder="john.doe@example.com"
          />
          <Input
            label="Phone"
            value={profile.phone || ''}
            onChange={(value) => handleFieldChange('phone', value)}
            maxLength={50}
            placeholder="+1 (555) 123-4567"
          />
          <Input
            label="Location"
            value={profile.location || ''}
            onChange={(value) => handleFieldChange('location', value)}
            maxLength={255}
            placeholder="San Francisco, CA"
          />
          <Input
            label="Website"
            value={profile.website || ''}
            onChange={(value) => handleFieldChange('website', value)}
            maxLength={255}
            placeholder="https://portfolio.com"
          />
          <Input
            label="LinkedIn"
            value={profile.linkedin || ''}
            onChange={(value) => handleFieldChange('linkedin', value)}
            maxLength={255}
            placeholder="https://linkedin.com/in/johndoe"
          />
          <Input
            label="GitHub"
            value={profile.github || ''}
            onChange={(value) => handleFieldChange('github', value)}
            maxLength={255}
            placeholder="https://github.com/johndoe"
          />
        </div>
      </SectionCard>

      {/* Work Experience Section */}
      <SectionCard title="Work Experience">
        {profile.experiences.map((exp, index) => (
          <ArrayItem
            key={index}
            item={exp}
            index={index}
            onChange={(subField, value) => handleArrayChange('experiences', index, subField as keyof Experience, value)}
            onRemove={() => handleRemoveItem('experiences', index)}
            fields={[
              { label: 'Title', name: 'title', required: true, maxLength: 255 },
              { label: 'Company', name: 'company', required: true, maxLength: 255 },
              { label: 'Location', name: 'location', maxLength: 255 },
              { label: 'Start Date', name: 'start_date', type: 'date' },
              { label: 'End Date', name: 'end_date', type: 'date' },
              { label: 'Current', name: 'is_current', type: 'checkbox' },
              { label: 'Description', name: 'description', type: 'textarea', rows: 3 },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem('experiences', {
            title: '',
            company: '',
            is_current: false,
          } as Experience)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Experience
        </button>
      </SectionCard>

      {/* Education Section */}
      <SectionCard title="Education">
        {profile.educations.map((edu, index) => (
          <ArrayItem
            key={index}
            item={edu}
            index={index}
            onChange={(subField, value) => handleArrayChange('educations', index, subField as keyof Education, value)}
            onRemove={() => handleRemoveItem('educations', index)}
            fields={[
              { label: 'Institution', name: 'institution', required: true, maxLength: 255 },
              { label: 'Degree', name: 'degree', maxLength: 255 },
              { label: 'Field of Study', name: 'field_of_study', maxLength: 255 },
              { label: 'Start Date', name: 'start_date', type: 'date' },
              { label: 'End Date', name: 'end_date', type: 'date' },
              { label: 'Description', name: 'description', type: 'textarea', rows: 2 },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem('educations', {
            institution: '',
          } as Education)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Education
        </button>
      </SectionCard>

      {/* Skills Section */}
      <SectionCard title="Skills">
        {profile.skills.map((skill, index) => (
          <ArrayItem
            key={index}
            item={skill}
            index={index}
            onChange={(subField, value) => handleArrayChange('skills', index, subField as keyof Skill, value)}
            onRemove={() => handleRemoveItem('skills', index)}
            fields={[
              { label: 'Skill Name', name: 'name', required: true, maxLength: 100 },
              { label: 'Category', name: 'category', maxLength: 100 },
              { label: 'Proficiency', name: 'proficiency', maxLength: 50 },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem('skills', {
            name: '',
          } as Skill)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Skill
        </button>
      </SectionCard>

      {/* Projects Section */}
      <SectionCard title="Projects">
        {profile.projects.map((project, index) => (
          <ArrayItem
            key={index}
            item={project}
            index={index}
            onChange={(subField, value) => handleArrayChange('projects', index, subField as keyof Project, value)}
            onRemove={() => handleRemoveItem('projects', index)}
            fields={[
              { label: 'Project Name', name: 'name', required: true, maxLength: 255 },
              { label: 'Description', name: 'description', type: 'textarea', rows: 2 },
              { label: 'URL', name: 'url', maxLength: 255 },
              { label: 'Start Date', name: 'start_date', type: 'date' },
              { label: 'End Date', name: 'end_date', type: 'date' },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem('projects', {
            name: '',
          } as Project)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Project
        </button>
      </SectionCard>

      {/* Certifications Section */}
      <SectionCard title="Certifications">
        {profile.certifications.map((cert, index) => (
          <ArrayItem
            key={index}
            item={cert}
            index={index}
            onChange={(subField, value) => handleArrayChange('certifications', index, subField as keyof Certification, value)}
            onRemove={() => handleRemoveItem('certifications', index)}
            fields={[
              { label: 'Certification Name', name: 'name', required: true, maxLength: 255 },
              { label: 'Issuer', name: 'issuer', required: true, maxLength: 255 },
              { label: 'Issue Date', name: 'issue_date', type: 'date' },
              { label: 'Expiration Date', name: 'expiration_date', type: 'date' },
              { label: 'Credential ID', name: 'credential_id', maxLength: 255 },
              { label: 'Credential URL', name: 'credential_url', maxLength: 255 },
            ]}
          />
        ))}
        <button
          onClick={() => handleAddItem('certifications', {
            name: '',
            issuer: '',
          } as Certification)}
          className="mt-4 px-4 py-2 border border-dashed border-border rounded-md text-text-secondary hover:bg-background-secondary transition-colors"
        >
          + Add Certification
        </button>
      </SectionCard>
    </div>
  );
}
