'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { getProfile } from '@/lib/api/profiles';
import { Profile } from '@/types/profile';

export default function ResumeProfilesPage() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    getProfile(token)
      .then(setProfile)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-text-primary mb-6">Resume Profiles</h1>
      {profile ? (
        <div className="bg-background-secondary border border-border rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-2">
            {profile.first_name || ''} {profile.last_name || ''}
          </h2>
          <p className="text-text-secondary mb-4">{profile.headline}</p>
          <Link
            href={`/dashboard/resumes/${profile.id || 'me'}/editor`}
            className="inline-block bg-brand text-white py-2 px-4 rounded-md hover:opacity-90 transition-opacity"
          >
            Edit Profile
          </Link>
        </div>
      ) : (
        <p className="text-text-secondary">No profile found.</p>
      )}
    </div>
  );
}