import { createFileRoute, Link } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { getProfile } from '@/lib/api/profiles';
import { Profile } from '@/types/profile';

export const Route = createFileRoute('/_app/resumes/')({
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

  if (loading) return <div>Loading...</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Resume Profiles</h1>
        {profile?.id && (
          <Link
            to="/_app/resumes/$id/editor"
            params={{ id: profile.id }}
            className="bg-brand text-white px-4 py-2 rounded-md"
          >
            Edit Profile
          </Link>
        )}
      </div>

      {profile ? (
        <div className="bg-white border rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold">{profile.first_name || 'Your'} {profile.last_name || 'Name'}</h2>
          <p className="text-gray-600 mb-4">{profile.headline || 'No headline set'}</p>
          <Link
            to="/_app/resumes/$id/editor"
            params={{ id: profile.id || 'me' }}
            className="text-brand font-medium"
          >
            Open Profile Editor
          </Link>
        </div>
      ) : (
        <p>No profile found.</p>
      )}
    </div>
  );
}
