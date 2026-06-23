// Static mock data used across SiraFit screens. No backend wired.
export type Job = {
  id: string;
  company: string;
  role: string;
  location: string;
  remote: "Remote" | "Hybrid" | "On-site";
  source: "Lever" | "Greenhouse" | "Ashby" | "Workday";
  match: number;
  salary: string;
  scrapedAt: string;
  tags: string[];
  status?: "new" | "saved" | "seen" | "applied";
  description?: string;
  responsibilities?: string[];
  required?: string[];
  preferred?: string[];
};

export const jobs: Job[] = [
  { id: "j-001", company: "Stripe", role: "Software Engineer, Infrastructure", location: "San Francisco, CA", remote: "Hybrid", source: "Greenhouse", match: 94, salary: "$180k–$220k", scrapedAt: "2h ago", tags: ["Go", "Kubernetes", "PostgreSQL", "gRPC"], status: "new",
    description: "Build core payment infrastructure powering global commerce. Work on high-throughput services that process billions of requests with strict latency SLAs.",
    responsibilities: ["Design distributed services in Go", "Improve database performance at scale", "Own production reliability for tier-1 systems"],
    required: ["3+ years backend experience", "Distributed systems fundamentals", "Strong CS fundamentals"],
    preferred: ["Experience with Kubernetes", "Payments domain", "Performance tuning"] },
  { id: "j-002", company: "Linear", role: "Junior Fullstack Developer", location: "Remote", remote: "Remote", source: "Ashby", match: 89, salary: "$130k–$165k", scrapedAt: "5h ago", tags: ["TypeScript", "React", "Node.js", "Postgres"], status: "new",
    description: "Help build the issue tracker engineering teams actually enjoy using. Ship end-to-end features in a small, opinionated team.",
    responsibilities: ["Ship product features end-to-end", "Collaborate on API design", "Maintain product quality bar"],
    required: ["1+ year shipping production TypeScript", "Care for craft and detail"],
    preferred: ["Prior startup experience", "Open source contributions"] },
  { id: "j-003", company: "Anthropic", role: "Backend Systems Engineer", location: "San Francisco, CA", remote: "Hybrid", source: "Greenhouse", match: 91, salary: "$200k+", scrapedAt: "2d ago", tags: ["Python", "Distributed Systems", "GPU Infra"], status: "saved" },
  { id: "j-004", company: "Vercel", role: "Frontend Engineer", location: "Remote", remote: "Remote", source: "Ashby", match: 72, salary: "$150k–$190k", scrapedAt: "1d ago", tags: ["React", "Next.js", "Edge Runtime"] },
  { id: "j-005", company: "Retool", role: "Product Engineer (New Grad)", location: "New York, NY", remote: "Hybrid", source: "Lever", match: 68, salary: "$140k–$170k", scrapedAt: "2d ago", tags: ["React", "TypeScript", "Postgres"] },
  { id: "j-006", company: "Supabase", role: "DevRel Engineer", location: "Remote", remote: "Remote", source: "Ashby", match: 82, salary: "$130k–$170k", scrapedAt: "3h ago", tags: ["Postgres", "Edge Functions", "Writing"] },
  { id: "j-007", company: "PostHog", role: "Full Stack Engineer", location: "Remote", remote: "Remote", source: "Lever", match: 84, salary: "$140k–$180k", scrapedAt: "7h ago", tags: ["Django", "React", "ClickHouse"], status: "applied" },
  { id: "j-008", company: "Resend", role: "Software Engineer", location: "Remote", remote: "Remote", source: "Ashby", match: 77, salary: "$140k–$175k", scrapedAt: "12h ago", tags: ["TypeScript", "AWS", "Email Infra"] },
  { id: "j-009", company: "Cloudflare", role: "Systems Engineer, Workers", location: "Austin, TX", remote: "Hybrid", source: "Greenhouse", match: 86, salary: "$170k–$210k", scrapedAt: "1d ago", tags: ["Rust", "V8 Isolates", "Edge"] },
  { id: "j-010", company: "PlanetScale", role: "Database Reliability Engineer", location: "Remote", remote: "Remote", source: "Lever", match: 79, salary: "$160k–$200k", scrapedAt: "2d ago", tags: ["MySQL", "Vitess", "Go"] },
  { id: "j-011", company: "Postman", role: "Core API Engineer", location: "Boston, MA", remote: "Hybrid", source: "Greenhouse", match: 64, salary: "$135k–$170k", scrapedAt: "3d ago", tags: ["Node.js", "OpenAPI"] },
  { id: "j-012", company: "Sentry", role: "Frontend Engineer, SDK", location: "Vienna, AT", remote: "Remote", source: "Lever", match: 73, salary: "€85k–€115k", scrapedAt: "4d ago", tags: ["TypeScript", "Browser APIs"] },
];

export const applicationsByStatus: Record<string, { jobId: string; sub?: string; date?: string; meta?: string; flag?: "warm" | "cold" }[]> = {
  Saved: [
    { jobId: "j-006", date: "3d" },
    { jobId: "j-011", date: "5d" },
    { jobId: "j-008", date: "1w" },
  ],
  Preparing: [
    { jobId: "j-003", date: "2d", meta: "Resume tailoring 82%" },
  ],
  Applied: [
    { jobId: "j-001", date: "2d", meta: "Awaiting reply" },
    { jobId: "j-007", date: "4d", meta: "Recruiter assigned" },
    { jobId: "j-009", date: "6d" },
  ],
  Assessment: [
    { jobId: "j-010", date: "1d", meta: "Take-home due Fri", flag: "warm" },
  ],
  Interview: [
    { jobId: "j-002", date: "Thu", meta: "Recruiter call · 10:00", flag: "warm" },
  ],
  "Final round": [],
  Offer: [],
  Rejected: [
    { jobId: "j-005", date: "1w", meta: "Resume screen" },
  ],
};

export const followUps = [
  { id: "f1", who: "Sarah Chen (Linear)", what: "Send thank-you note after intro call", when: "Today, 17:00" },
  { id: "f2", who: "Recruiter @ Stripe", what: "Check status of application", when: "Tomorrow" },
  { id: "f3", who: "PostHog", what: "Respond to assessment email", when: "In 2 days" },
  { id: "f4", who: "PlanetScale", what: "Submit take-home", when: "Fri 23:59" },
];

export const notifications = [
  { id: "n1", title: "Resume generated", body: "Tailored resume for Stripe – Infra Engineer is ready.", time: "12m", kind: "success" as const },
  { id: "n2", title: "Interview scheduled", body: "Linear recruiter call confirmed for Thursday 10:00.", time: "1h", kind: "info" as const },
  { id: "n3", title: "Scraper rate-limited", body: "Greenhouse polling throttled. Retrying in 4m.", time: "3h", kind: "warning" as const },
  { id: "n4", title: "Sync batch #412 sent", body: "238 events synced to cloud successfully.", time: "5h", kind: "muted" as const },
  { id: "n5", title: "Match recomputed", body: "54 jobs rescored after profile update.", time: "1d", kind: "muted" as const },
];

export const eventLog = [
  { t: "09:14", e: "AI generation complete: Resume_v2.1 for Stripe", kind: "success" },
  { t: "09:12", e: "Job scraped: Ashby/Linear_Eng", kind: "info" },
  { t: "08:45", e: "Local Agent sync batch #412 sent", kind: "muted" },
  { t: "08:20", e: "Deterministic re-scoring run: 54 jobs", kind: "info" },
  { t: "07:58", e: "Quarantine: malformed Greenhouse posting (jp-1129)", kind: "warning" },
  { t: "07:30", e: "Scrape cycle started: 12 ATS sources", kind: "muted" },
];

export const skillMatrix = [
  { skill: "TypeScript", you: 85, market: 92 },
  { skill: "React", you: 90, market: 88 },
  { skill: "Node.js", you: 78, market: 80 },
  { skill: "Python", you: 65, market: 72 },
  { skill: "Go", you: 40, market: 58 },
  { skill: "Kubernetes", you: 35, market: 64 },
  { skill: "PostgreSQL", you: 70, market: 75 },
  { skill: "AWS", you: 55, market: 78 },
];

export const profile = {
  name: "Alex Rivera",
  title: "Junior Software Engineer",
  email: "alex@rivera.dev",
  location: "San Francisco, CA",
  github: "github.com/arivera",
  experience: [
    { company: "Cloud Scale Labs", role: "Software Engineer Intern", period: "Jun 2024 – Present", bullets: ["Built distributed ingestion pipeline in Go and Kafka, reducing p99 latency by 40%.", "Implemented Kubernetes auto-scaling policies for tier-1 services.", "Owned migration of analytics pipeline to ClickHouse."] },
    { company: "Arcade Systems", role: "Junior Developer", period: "Jan 2023 – May 2024", bullets: ["Shipped 12 customer-facing features in a React/Node monorepo.", "Reduced bundle size 28% via route-level code splitting."] },
  ],
  projects: [
    { name: "Distributed Scraper", desc: "Horizontally-scalable web scraping framework in Go with Redis-backed work queue.", tags: ["Go", "Redis", "Docker"] },
    { name: "Resume Parser", desc: "Open-source structured resume parser with schema validation.", tags: ["TypeScript", "Zod"] },
  ],
  skills: ["TypeScript", "React", "Node.js", "PostgreSQL", "Go", "Docker", "Redis", "AWS"],
  education: [{ school: "UC Berkeley", degree: "B.S. Computer Science", period: "2020 – 2024" }],
};

export function getJob(id: string): Job {
  return jobs.find((j) => j.id === id) ?? jobs[0];
}

export const resumeVersions = [
  { id: "rv-12", name: "Stripe – Infra Engineer", template: "Technical", createdAt: "2h ago", score: 94 },
  { id: "rv-11", name: "Linear – Fullstack", template: "Modern", createdAt: "1d ago", score: 89 },
  { id: "rv-10", name: "Anthropic – Backend", template: "Technical", createdAt: "2d ago", score: 91 },
  { id: "rv-09", name: "Vercel – Frontend", template: "Minimal", createdAt: "3d ago", score: 72 },
  { id: "rv-08", name: "Generic – Fullstack Master", template: "Technical", createdAt: "1w ago", score: null as number | null },
];

export const coverLetters = [
  { id: "cl-04", job: "Stripe – Infra Engineer", createdAt: "2h ago", words: 218 },
  { id: "cl-03", job: "Linear – Fullstack", createdAt: "1d ago", words: 194 },
  { id: "cl-02", job: "Anthropic – Backend", createdAt: "2d ago", words: 232 },
];

export const importHistory = [
  { id: "ih-19", source: "Greenhouse / boards-api", count: 142, ok: 138, fail: 4, when: "12m ago", status: "completed" as const },
  { id: "ih-18", source: "Lever / postings", count: 87, ok: 87, fail: 0, when: "2h ago", status: "completed" as const },
  { id: "ih-17", source: "Ashby / job_board.list", count: 54, ok: 50, fail: 4, when: "5h ago", status: "completed" as const },
  { id: "ih-16", source: "Manual paste – 1 URL", count: 1, ok: 1, fail: 0, when: "1d ago", status: "completed" as const },
  { id: "ih-15", source: "Greenhouse / boards-api", count: 138, ok: 0, fail: 138, when: "2d ago", status: "failed" as const },
];

export const marketRoles = [
  { role: "Backend Engineer", demand: 92, postings: 1820, change: "+6%" },
  { role: "Frontend Engineer", demand: 88, postings: 1540, change: "+2%" },
  { role: "DevOps / SRE", demand: 81, postings: 980, change: "+11%" },
  { role: "Data Engineer", demand: 76, postings: 740, change: "+4%" },
  { role: "ML Engineer", demand: 71, postings: 620, change: "+18%" },
  { role: "Mobile Engineer", demand: 58, postings: 410, change: "-3%" },
];