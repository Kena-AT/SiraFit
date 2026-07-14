export const jobs = [
  {
    id: "JOB-1234",
    company: "Acme Corp",
    role: "Senior Frontend Engineer",
    match: 92,
    salary: "$150k - $180k",
    source: "LinkedIn",
    tags: ["React", "TypeScript", "Tailwind"],
    scrapedAt: "2026-06-30T10:00:00Z",
    status: "Applied",
    location: "San Francisco, CA",
    remote: "Hybrid",
    description: "We are looking for a senior frontend engineer...",
    responsibilities: ["Build UI components", "Optimize performance"],
    required: ["5+ years React", "TypeScript expertise"],
    preferred: ["Next.js", "GraphQL"],
  },
  {
    id: "JOB-5678",
    company: "TechFlow",
    role: "Full Stack Developer",
    match: 85,
    salary: "$130k - $160k",
    source: "Lever",
    tags: ["Node.js", "React", "PostgreSQL"],
    scrapedAt: "2026-06-29T14:30:00Z",
    status: "Saved",
    location: "New York, NY",
    remote: "Remote",
    description: "Join our core product team...",
    responsibilities: ["Develop full stack features", "Database design"],
    required: ["3+ years Node.js", "React experience"],
    preferred: ["AWS", "Docker"],
  },
];

export function getJob(id: string) {
  return jobs.find((j) => j.id === id) || jobs[0];
}
