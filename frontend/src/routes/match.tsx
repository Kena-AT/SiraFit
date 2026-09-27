import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { MarketingShell } from "@/components/sirafit/shell";
import { calculatePublicMatch, type PublicMatchResponse } from "@/lib/api/jobs";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  RotateCcw,
  Zap,
  Target,
  FileCheck2,
  Award,
} from "lucide-react";

export const Route = createFileRoute("/match")({
  head: () => ({
    meta: [
      { title: "Free Resume Match Score & ATS Scanner · SiraFit" },
      {
        name: "description",
        content:
          "Instant, 100% deterministic ATS resume match score. Compare your resume against any job description with zero signup, zero token fees, and actionable gap analysis.",
      },
      { property: "og:title", content: "Free Resume Match Score & ATS Scanner · SiraFit" },
      {
        property: "og:description",
        content:
          "Paste a job description and your resume for an instant ATS breakdown, matched skills, and actionable recommendations.",
      },
    ],
  }),
  component: PublicMatchPage,
});

const SAMPLE_JOB_DESCRIPTION = `Senior Full-Stack Engineer
Acme Cloud Systems — San Francisco, CA (Remote)

About the Role:
We are seeking an experienced Senior Full-Stack Engineer to build reliable distributed web services and responsive user interfaces.

Key Responsibilities:
- Design, build, and maintain high-throughput RESTful APIs using Python, FastAPI, and PostgreSQL.
- Architect modern, modular frontends in TypeScript, React, and Tailwind CSS.
- Optimize database queries, migrations, and caching with Redis and SQLAlchemy.
- Deploy and orchestrate containerized applications using Docker and AWS ECS/Kubernetes.
- Implement automated unit and integration tests with pytest and Playwright.

Requirements:
- 5+ years of software engineering experience building production systems.
- Strong proficiency in Python and modern TypeScript / JavaScript.
- Demonstrated experience with FastAPI or Django, and React or Next.js.
- Strong knowledge of PostgreSQL schema design, indexing, and query tuning.
- Hands-on experience with Docker, CI/CD pipelines (GitHub Actions), and AWS.
- Excellent communication and ability to work in agile, fast-paced teams.`;

const SAMPLE_RESUME_TEXT = `Jane Doe
jane.doe@example.com | (555) 123-4567 | San Francisco, CA | linkedin.com/in/janedoe | github.com/janedoe

Summary:
Full-Stack Software Engineer with 6 years of experience designing, scaling, and maintaining distributed web applications. Expertise in Python, TypeScript, React, PostgreSQL, and cloud deployments. Passionate about clean architecture, ATS-friendly code, and rapid iteration.

Core Skills:
- Languages: Python, TypeScript, JavaScript, SQL, HTML/CSS
- Frameworks: FastAPI, React, Node.js, Next.js, Express
- Databases & Infra: PostgreSQL, Redis, Docker, Git, Linux, GitHub Actions
- Methodologies: Agile/Scrum, CI/CD, Test-Driven Development (pytest)

Professional Experience:
Senior Software Engineer | Apex Data Labs | 2022 – Present
- Architected and deployed scalable microservices in Python and FastAPI handling 2M+ daily requests with 99.98% uptime.
- Re-architected company frontend dashboard into React and Tailwind CSS, decreasing load times by 42%.
- Optimized complex PostgreSQL queries and Redis caching, cutting average API response latency from 320ms to 45ms.
- Containerized development and production pipelines with Docker and automated testing via GitHub Actions.

Software Engineer | BitMetric Inc. | 2019 – 2022
- Developed responsive web interfaces using TypeScript and React for an enterprise analytics suite.
- Built backend ETL ingestion pipelines using Python and SQLAlchemy to ingest 500k records/day.
- Integrated automated end-to-end testing and linting, reducing regression bugs by 35%.

Education:
B.S. in Computer Science | University of California, Berkeley | 2015 – 2019`;

function getScoreColor(score: number): {
  text: string;
  stroke: string;
  bg: string;
  border: string;
} {
  if (score >= 80) {
    return {
      text: "text-emerald-500 dark:text-emerald-400",
      stroke: "#10b981",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
    };
  }
  if (score >= 60) {
    return {
      text: "text-blue-500 dark:text-blue-400",
      stroke: "#3b82f6",
      bg: "bg-blue-500/10",
      border: "border-blue-500/30",
    };
  }
  if (score >= 40) {
    return {
      text: "text-amber-500 dark:text-amber-400",
      stroke: "#f59e0b",
      bg: "bg-amber-500/10",
      border: "border-amber-500/30",
    };
  }
  return {
    text: "text-rose-500 dark:text-rose-400",
    stroke: "#f43f5e",
    bg: "bg-rose-500/10",
    border: "border-rose-500/30",
  };
}

export function PublicMatchPage() {
  const [jobDescription, setJobDescription] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<PublicMatchResponse | null>(null);

  const handleLoadSample = () => {
    setJobDescription(SAMPLE_JOB_DESCRIPTION);
    setResumeText(SAMPLE_RESUME_TEXT);
    toast.success("Loaded sample job and resume");
  };

  const handleClear = () => {
    setJobDescription("");
    setResumeText("");
    setResult(null);
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobDescription.trim()) {
      toast.error("Please enter or paste a job description");
      return;
    }
    if (!resumeText.trim()) {
      toast.error("Please enter or paste your resume text");
      return;
    }

    setIsSubmitting(true);
    try {
      const data = await calculatePublicMatch({
        job_description: jobDescription,
        resume_text: resumeText,
      });
      setResult(data);
      toast.success("Match analysis complete!");
      setTimeout(() => {
        document.getElementById("match-results")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to calculate match score";
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const score = result ? result.overall_score : 0;
  const scoreColors = result ? getScoreColor(score) : null;
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = result
    ? circumference - (score / 100) * circumference
    : circumference;

  return (
    <MarketingShell>
      <div className="relative mx-auto max-w-5xl px-4 py-12 md:py-16">
        {/* Header Hero */}
        <div className="text-center">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-brand/10 px-3.5 py-1 text-xs font-semibold text-brand ring-1 ring-brand/30">
            <Zap className="h-3.5 w-3.5" />
            100% Deterministic ATS Scanner · Zero Hallucinations · Free Forever
          </div>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            Free Resume Match Score
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-balance text-sm text-muted-foreground md:text-base">
            Compare your resume against any target job description. Get an instant, transparent
            breakdown of keyword coverage, ATS section readiness, and missing skills.
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleLoadSample}
              className="gap-2 text-xs"
            >
              <Sparkles className="h-3.5 w-3.5 text-brand" />
              Load Sample Data
            </Button>
            {(jobDescription || resumeText || result) && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleClear}
                className="gap-1.5 text-xs text-muted-foreground"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Clear
              </Button>
            )}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleAnalyze} className="mt-10 space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Job Description */}
            <div className="rounded-xl border border-border bg-card p-5 shadow-xs transition-shadow hover:shadow-md">
              <div className="flex items-center justify-between pb-3">
                <label
                  htmlFor="job_description"
                  className="flex items-center gap-2 text-sm font-semibold text-foreground"
                >
                  <Target className="h-4 w-4 text-blue-500" />
                  Target Job Description
                </label>
                <span className="text-[11px] font-mono text-muted-foreground">
                  {jobDescription.length.toLocaleString()} chars
                </span>
              </div>
              <Textarea
                id="job_description"
                placeholder="Paste the full job posting here (responsibilities, requirements, qualifications, title)..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="min-h-[260px] font-mono text-xs leading-relaxed resize-y"
              />
            </div>

            {/* Resume Text */}
            <div className="rounded-xl border border-border bg-card p-5 shadow-xs transition-shadow hover:shadow-md">
              <div className="flex items-center justify-between pb-3">
                <label
                  htmlFor="resume_text"
                  className="flex items-center gap-2 text-sm font-semibold text-foreground"
                >
                  <FileCheck2 className="h-4 w-4 text-emerald-500" />
                  Your Resume Text / Markdown
                </label>
                <span className="text-[11px] font-mono text-muted-foreground">
                  {resumeText.length.toLocaleString()} chars
                </span>
              </div>
              <Textarea
                id="resume_text"
                placeholder="Paste your current resume content here (summary, skills, work experience, education)..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                className="min-h-[260px] font-mono text-xs leading-relaxed resize-y"
              />
            </div>
          </div>

          <div className="flex justify-center pt-2">
            <Button
              type="submit"
              size="lg"
              disabled={isSubmitting || !jobDescription.trim() || !resumeText.trim()}
              className="px-8 font-semibold shadow-md transition-all hover:scale-[1.02]"
            >
              {isSubmitting ? (
                <>
                  <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-foreground" />
                  Scoring Match...
                </>
              ) : (
                <>
                  Calculate Free Match Score
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </form>

        {/* Results Section */}
        {result && scoreColors && (
          <div id="match-results" className="mt-12 space-y-8 animate-in fade-in duration-300">
            {/* Top Score Banner */}
            <div
              className={`rounded-2xl border ${scoreColors.border} ${scoreColors.bg} p-6 md:p-8`}
            >
              <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
                <div className="flex items-center gap-6">
                  {/* Gauge */}
                  <div className="relative flex h-32 w-32 items-center justify-center">
                    <svg className="h-32 w-32 -rotate-90 transform" viewBox="0 0 120 120">
                      <circle
                        cx="60"
                        cy="60"
                        r={radius}
                        stroke="currentColor"
                        strokeWidth="10"
                        fill="transparent"
                        className="text-border/60"
                      />
                      <circle
                        cx="60"
                        cy="60"
                        r={radius}
                        stroke={scoreColors.stroke}
                        strokeWidth="10"
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        fill="transparent"
                        className="transition-all duration-1000 ease-out"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span
                        className={`text-3xl font-bold font-mono tracking-tight ${scoreColors.text}`}
                      >
                        {result.overall_score}%
                      </span>
                      <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                        Match
                      </span>
                    </div>
                  </div>

                  <div>
                    <div className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wider bg-background/80 ring-1 ring-border">
                      <Award className="h-3.5 w-3.5" />
                      {result.verdict}
                    </div>
                    <h2 className="mt-2 text-xl font-bold text-foreground md:text-2xl">
                      {result.overall_score >= 80
                        ? "High Match Alignment"
                        : result.overall_score >= 60
                          ? "Moderate Match Alignment"
                          : result.overall_score >= 40
                            ? "Fair Match - Optimization Recommended"
                            : "Low Match - Significant Keyword Gaps"}
                    </h2>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {result.summary}
                    </p>
                  </div>
                </div>

                <div className="w-full max-w-xs space-y-3 rounded-xl bg-background/90 p-4 ring-1 ring-border">
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Breakdown Dimensions
                  </div>
                  <div className="space-y-2 text-xs">
                    <div>
                      <div className="flex justify-between font-medium">
                        <span>Skills Overlap (45%)</span>
                        <span className="font-mono">{result.breakdown.skills}%</span>
                      </div>
                      <div className="mt-1 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${result.breakdown.skills}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between font-medium">
                        <span>Title Alignment (20%)</span>
                        <span className="font-mono">{result.breakdown.title_alignment}%</span>
                      </div>
                      <div className="mt-1 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${result.breakdown.title_alignment}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between font-medium">
                        <span>Experience Level (20%)</span>
                        <span className="font-mono">{result.breakdown.experience_level}%</span>
                      </div>
                      <div className="mt-1 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-purple-500 rounded-full"
                          style={{ width: `${result.breakdown.experience_level}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between font-medium">
                        <span>ATS Formatting (15%)</span>
                        <span className="font-mono">{result.breakdown.ats_formatting}%</span>
                      </div>
                      <div className="mt-1 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-amber-500 rounded-full"
                          style={{ width: `${result.breakdown.ats_formatting}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Skills Comparison */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Matched Skills */}
              <div className="rounded-xl border border-border bg-card p-5">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div className="flex items-center gap-2 font-semibold text-foreground text-sm">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    Matched Skills ({result.matching_skills.length})
                  </div>
                  <span className="text-[11px] text-muted-foreground">Found in both</span>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {result.matching_skills.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic">
                      No matching skills detected.
                    </p>
                  ) : (
                    result.matching_skills.map((skill: string) => (
                      <span
                        key={skill}
                        className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/20"
                      >
                        ✓ {skill}
                      </span>
                    ))
                  )}
                </div>
              </div>

              {/* Missing Skills */}
              <div className="rounded-xl border border-border bg-card p-5">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div className="flex items-center gap-2 font-semibold text-foreground text-sm">
                    <AlertCircle className="h-4 w-4 text-rose-500" />
                    Missing Keywords ({result.missing_skills.length})
                  </div>
                  <span className="text-[11px] text-muted-foreground">Found in job only</span>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {result.missing_skills.length === 0 ? (
                    <p className="text-xs text-emerald-500 font-medium">
                      All detected skills covered!
                    </p>
                  ) : (
                    result.missing_skills.map((skill: string) => (
                      <span
                        key={skill}
                        className="inline-flex items-center gap-1 rounded-md bg-rose-500/10 px-2.5 py-1 text-xs font-medium text-rose-600 dark:text-rose-400 ring-1 ring-rose-500/20"
                      >
                        + {skill}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Actionable Recommendations */}
            <div className="rounded-xl border border-border bg-card p-5">
              <h3 className="font-semibold text-foreground text-sm flex items-center gap-2 pb-3 border-b border-border">
                <Sparkles className="h-4 w-4 text-amber-500" />
                Actionable Optimization Recommendations
              </h3>
              <ul className="mt-4 space-y-2 text-xs">
                {result.recommendations.map((rec: string, idx: number) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2.5 rounded-lg bg-muted/30 p-2.5 leading-relaxed"
                  >
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand/10 text-[10px] font-bold text-brand">
                      {idx + 1}
                    </span>
                    <span className="text-muted-foreground">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* PLG Conversion Call to Action */}
            <div className="relative overflow-hidden rounded-2xl border border-brand/30 bg-gradient-to-br from-brand/10 via-background to-blue-500/10 p-8 text-center shadow-lg">
              <div className="mx-auto max-w-xl">
                <div className="inline-flex items-center gap-1.5 rounded-full bg-brand/20 px-3 py-1 text-xs font-semibold text-brand">
                  <Sparkles className="h-3.5 w-3.5" />
                  Tailor with Local or Cloud AI
                </div>
                <h3 className="mt-4 text-2xl font-bold tracking-tight text-foreground md:text-3xl">
                  Want to tailor this resume in 1-click?
                </h3>
                <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
                  SiraFit automatically injects your missing keywords, quantifies your bullet
                  points, and generates tailored PDF / JSON-Resume variants using your own API key
                  (Claude, GPT-4o, Gemini, or Ollama).
                </p>

                <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
                  <Link
                    to="/register"
                    className="inline-flex items-center gap-2 rounded-lg bg-foreground px-6 py-3 text-sm font-semibold text-background shadow-md transition-all hover:bg-foreground/90 hover:scale-105"
                  >
                    Create Free Account
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    to="/login"
                    className="inline-flex items-center rounded-lg bg-card px-6 py-3 text-sm font-semibold text-foreground ring-1 ring-border transition-all hover:bg-muted"
                  >
                    Sign In
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MarketingShell>
  );
}
