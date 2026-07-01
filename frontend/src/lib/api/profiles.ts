import { Profile } from '@/types/profile';
import { apiFetch } from './client';

export async function getProfile(): Promise<Profile> {
  const response = await apiFetch('/api/v1/profiles/me');
  if (!response.ok) {
    throw new Error('Failed to fetch profile');
  }
  return response.json();
}

export async function updateProfile(profile: Profile): Promise<Profile> {
  const response = await apiFetch('/api/v1/profiles/me', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  });
  if (!response.ok) {
    throw new Error('Failed to update profile');
  }
  return response.json();
}
