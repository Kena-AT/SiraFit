'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getProfile } from '@/lib/api/profiles';
import { Profile } from '@/types/profile';

export default function ResumeProfilesPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-primary">Resume Profiles</h1>
        {profile?.id && (
          <Link
            href={`/dashboard/resumes/${profile.id}/editor`}
            className="bg-brand text-white px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Edit Profile
          </Link>
        )}
      </div>

      {profile ? (
        <div className="bg-background-secondary border border-border rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-2">
            {profile.first_name || 'Your'} {profile.last_name || 'Name'}
          </h2>
          <p className="text-text-secondary mb-4">{profile.headline || 'No headline set'}</p>

          <div className="flex flex-wrap gap-4 text-sm text-text-secondary mb-4">
            {profile.email && <span>{profile.email}</span>}
            {profile.location && <span>{profile.location}</span>}
          </div>

          {profile.experiences && profile.experiences.length > 0 && (
            <p className="text-sm text-text-secondary mb-2">
              {profile.experiences.length} work experience{profile.experiences.length !== 1 ? 's' : ''}
            </p>
          )}
          {profile.educations && profile.educations.length > 0 && (
            <p className="text-sm text-text-secondary mb-2">
              {profile.educations.length} education entr{profile.educations.length !== 1 ? 'ies' : 'y'}
            </p>
          )}
          {profile.skills && profile.skills.length > 0 && (
            <p className="text-sm text-text-secondary mb-4">
              {profile.skills.length} skill{profile.skills.length !== 1 ? 's' : ''}
            </p>
          )}

          <Link
            href={`/dashboard/resumes/${profile.id}/editor`}
            className="inline-block bg-brand text-white py-2 px-4 rounded-md hover:opacity-90 transition-opacity"
          >
            Open Profile Editor
          </Link>
        </div>
      ) : (
        <div className="bg-background-secondary border border-border rounded-lg p-6 shadow-sm text-center">
          <p className="text-text-secondary mb-4">No profile found. One will be created when you open the editor.</p>
          <Link
            href="/dashboard/resumes/new/editor"
            className="inline-block bg-brand text-white py-2 px-4 rounded-md hover:opacity-90 transition-opacity"
          >
            Create Profile
          </Link>
        </div>
      )}
    </div>
  );
}
