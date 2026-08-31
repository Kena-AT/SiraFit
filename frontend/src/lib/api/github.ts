/**
 * Minimal GitHub REST API client for importing public repositories as
 * resume Projects. Browser-direct (GitHub's API allows CORS); unauthenticated
 * requests are rate-limited to 60/hour per IP, which is plenty for this flow.
 */

export interface GithubRepo {
  id: number;
  name: string;
  full_name: string;
  html_url: string;
  description: string | null;
  fork: boolean;
  stargazers_count: number;
  language: string | null;
  created_at: string;
  updated_at: string;
}

/** Extract a GitHub username from a bare username or any github.com URL. */
export function parseGithubUsername(input: string): string | null {
  const value = (input || "").trim();
  if (!value) return null;
  // Matches the first path segment of github.com/<user>, tolerating www,
  // http(s), trailing slashes, and deeper paths like /<user>/<repo>.
  const urlMatch = value.match(
    /github\.com\/([A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38})/i,
  );
  if (urlMatch) return urlMatch[1];
  if (/^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$/.test(value)) {
    return value;
  }
  return null;
}

/**
 * Fetch a user's public repos, forks excluded, sorted by stars (desc).
 * Throws with user-friendly messages for the common failure modes.
 */
export async function fetchGithubRepos(username: string): Promise<GithubRepo[]> {
  const res = await fetch(
    `https://api.github.com/users/${encodeURIComponent(username)}/repos?per_page=100&sort=updated`,
    { headers: { Accept: "application/vnd.github+json" } },
  );
  if (res.status === 404) {
    throw new Error(`GitHub user "${username}" not found`);
  }
  if (res.status === 403 || res.status === 429) {
    throw new Error(
      "GitHub API rate limit reached — try again in a few minutes",
    );
  }
  if (!res.ok) {
    throw new Error(`GitHub request failed (${res.status})`);
  }
  const repos: GithubRepo[] = await res.json();
  return repos
    .filter((r) => !r.fork)
    .sort((a, b) => b.stargazers_count - a.stargazers_count);
}
