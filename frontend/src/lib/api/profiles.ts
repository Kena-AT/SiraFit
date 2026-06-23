import { Profile } from '@/types/profile';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getProfile(): Promise<Profile> {
  const response = await fetch(`${API_BASE_URL}/api/v1/profiles/me`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch profile');
  }

  return response.json();
}

export async function updateProfile(profile: Profile): Promise<Profile> {
  const response = await fetch(`${API_BASE_URL}/api/v1/profiles/me`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(profile),
  });

  if (!response.ok) {
    throw new Error('Failed to update profile');
  }

  return response.json();
}
