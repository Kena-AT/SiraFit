import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, EmptyState, ScorePill } from "@/components/sirafit/bits";
import { getDashboardStats, getMarketPulse, getBriefing } from "@/lib/api/dashboard";
import { getRankedJobs, getJobs, getImportHistory } from "@/lib/api/jobs";
import { getFollowUps, getApplications, createApplication } from "@/lib/api/applications";
import { getProfile } from "@/lib/api/profiles";
import { getAIProviderKeys } from "@/lib/api/users";
import {
  timeAgo,
  WidgetSkeleton,
  WidgetError,
  StatCard,
  MomentumScore,
  FunnelChart,
  ResponseSparkline,
  NextBestActionCard,
  MarketPulseWidget,
  type NextAction,
} from "@/components/sirafit/dashboard-widgets";
import { PromptDialog, type PromptDialogConfig } from "@/components/sirafit/prompt-dialog";
import type { JobApplication } from "@/types/job";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard · SiraFit" }] }),
  component: Dashboard,
});

const CHECKLIST_KEY = "sirafit:dashboard:checklist-dismissed";

const APPLIED_PLUS = new Set(["applied", "assessment", "interview", "final_round", "offer"]);
const INTERVIEWING = new Set(["interview", "final_round"]);
const OFFERS = new Set(["offer"]);
const RESPONDED = new Set(["assessment", "interview", "final_round", "offer", "rejected"]);

const ENTITY_ROUTES: Record<string, string> = {
  job: "/jobs",
  application: "/applications",
  resume: "/resumes",
  cover_letter: "/cover-letters",
  import: "/jobs/history",
};

function humanizeAction(action: string): string {
  const words = (action || "")
    .replace(/[_\-.]+/g, " ")
    .trim()
    .split(/\s+/);
  return words.map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

function entityId(details?: Record<string, unknown> | null): string | null {
  if (!details) return null;
  for (const key of ["entity_id", "application_id", "job_id", "resume_id", "id"]) {
    const v = details[key];
    if (typeof v === "string" && v.length > 0) return v;
  }
  return null;
}

function daysSince(iso: string | undefined | null): number {
  if (!iso) return Infinity;
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
}

function Dashboard() {
  const queryClient = useQueryClient();
  const [quickLogOpen, setQuickLogOpen] = useState(false);

  // --- Core queries -------------------------------------------------------
  const statsQ = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    staleTime: 30_000,
  });
  const appsQ = useQuery({
    queryKey: ["applications"],
    queryFn: getApplications,
    staleTime: 60_000,
  });
  const followupsQ = useQuery({
    queryKey: ["followups-dashboard"],
    queryFn: () => getFollowUps(true, 0, 25),
    staleTime: 60_000,
  });
  const rankedQ = useQuery({
    queryKey: ["ranked-top"],
    queryFn: () => getRankedJobs({ limit: 5 }),
    staleTime: 120_000,
  });
  const profileQ = useQuery({
    queryKey: ["profile", "me"],
    queryFn: getProfile,
    staleTime: 60_000,
  });
  const importsQ = useQuery({
    queryKey: ["import-history-dash"],
    queryFn: () => getImportHistory(0, 20),
    staleTime: 60_000,
  });
  const pulseQ = useQuery({
    queryKey: ["market-pulse"],
    queryFn: getMarketPulse,
    staleTime: 600_000,
    retry: false,
  });

  // Check whether the user has any AI key configured before firing the
  // briefing endpoint. Without a key it always returns 503, so gating here
  // avoids the wasted round-trip and the noisy error log every page load.
  const aiKeysQ = useQuery({
    queryKey: ["ai-keys-status"],
    queryFn: getAIProviderKeys,
    staleTime: 300_000,
    retry: false,
  });
  const hasAiKey = aiKeysQ.data && Object.values(aiKeysQ.data).some((v) => v === true);

  const briefingQ = useQuery({
    queryKey: ["ai-briefing"],
    queryFn: getBriefing,
    staleTime: 600_000,
    retry: false,
    // Only fire once we know a key is configured — avoids a guaranteed 503
    // on every dashboard load when the user hasn't set up an AI provider.
    enabled: hasAiKey === true,
  });

  // --- Derived intelligence ----------------------------------------------
  const apps: JobApplication[] = appsQ.data ?? [];

  const now = Date.now();
  const inWindow = (iso: string | undefined, startDays: number, endDays: number) => {
    if (!iso) return false;
    const ageDays = (now - new Date(iso).getTime()) / 86_400_000;
    return ageDays >= startDays && ageDays < endDays;
  };

  const apps7 = apps.filter((a) => inWindow(a.created_at, 0, 7)).length;
  const appsPrev = apps.filter((a) => inWindow(a.created_at, 7, 14)).length;

  const importRecords = importsQ.data ?? [];
  const imports7 = importRecords.filter((r) => inWindow(r.created_at, 0, 7)).length;
  const importsPrev = importRecords.filter((r) => inWindow(r.created_at, 7, 14)).length;
  const latestImportAge = importRecords.length ? daysSince(importRecords[0].created_at) : Infinity;

  const allFollowups = followupsQ.data ?? [];
  const overdueFollowups = allFollowups.filter(
    (f) => f.follow_up_at && new Date(f.follow_up_at).getTime() < now,
  );
  const upcomingFollowups = allFollowups
    .filter((f) => f.follow_up_at && new Date(f.follow_up_at).getTime() >= now)
    .sort((a, b) => new Date(a.follow_up_at).getTime() - new Date(b.follow_up_at).getTime())
    .slice(0, 5);
  const punctuality =
    allFollowups.length === 0 ? 1 : 1 - overdueFollowups.length / allFollowups.length;

  const p = profileQ.data;
  const completeness = (() => {
    if (!p) return 0;
    let score = 0;
    const headerFilled = [p.first_name, p.last_name, p.headline, p.email, p.location].filter(
      Boolean,
    ).length;
    score += (headerFilled / 5) * 0.3;
    if ((p.experiences?.length ?? 0) > 0) score += 0.2;
    if ((p.educations?.length ?? 0) > 0) score += 0.1;
    if ((p.skills?.length ?? 0) >= 5) score += 0.15;
    else score += ((p.skills?.length ?? 0) / 5) * 0.15;
    if ((p.projects?.length ?? 0) > 0) score += 0.15;
    if ((p.certifications?.length ?? 0) > 0) score += 0.1;
    return Math.round(score * 100);
  })();

  const hasInterviewProgress = apps.some((a) => INTERVIEWING.has(a.status) || OFFERS.has(a.status));

  const momentumOf = (appsW: number, importsW: number) => {
    const s =
      Math.min(appsW / 5, 1) * 30 +
      punctuality * 25 +
      Math.min(importsW / 3, 1) * 15 +
      (completeness / 100) * 20 +
      (hasInterviewProgress ? 10 : 0);
    return Math.round(s);
  };
  const momentum = momentumOf(apps7, imports7);
  const momentumDelta = momentum - momentumOf(appsPrev, importsPrev);

  const funnel = [
    { label: "Jobs imported", value: statsQ.data?.total_jobs ?? 0 },
    { label: "Applied", value: apps.filter((a) => APPLIED_PLUS.has(a.status)).length },
    { label: "Interviewing", value: apps.filter((a) => INTERVIEWING.has(a.status)).length },
    { label: "Offers", value: apps.filter((a) => OFFERS.has(a.status)).length },
  ];

  // Weekly buckets for the response-rate sparkline (8 weeks).
  const WEEKS = 8;
  const sentBuckets = Array.from({ length: WEEKS }, () => 0);
  const respBuckets = Array.from({ length: WEEKS }, () => 0);
  for (const a of apps) {
    const sentAgeD = (now - new Date(a.created_at).getTime()) / 86_400_000;
    const wk = Math.floor(sentAgeD / 7);
    if (wk >= 0 && wk < WEEKS) sentBuckets[WEEKS - 1 - wk] += 1;
    if (RESPONDED.has(a.status)) {
      const respAgeD = (now - new Date(a.updated_at).getTime()) / 86_400_000;
      const rwk = Math.floor(respAgeD / 7);
      if (rwk >= 0 && rwk < WEEKS) respBuckets[WEEKS - 1 - rwk] += 1;
    }
  }

  // Profile skills are needed by the Next Best Action rule engine below.
  const profileSkills = new Set(
    (profileQ.data?.skills ?? []).map((s) => (s.name || "").toLowerCase()).filter(Boolean),
  );

  // Next Best Action rule engine (priority order matters).
  const nextAction: NextAction | null = (() => {
    if (overdueFollowups.length > 0) {
      const f = overdueFollowups[0];
      return {
        kind: "followup",
        title: `Follow up with ${f.company}`,
        body: `${f.job_title} — reminder was due ${timeAgo(f.follow_up_at)}. ${
          overdueFollowups.length > 1 ? `${overdueFollowups.length - 1} more also overdue.` : ""
        }`,
        cta: "Open follow-ups",
        to: "/applications/followups",
      };
    }
    const ranked = (rankedQ.data?.jobs ?? []) as {
      job: { id: string; title: string; company: string };
      match_score: { score: number } | null;
    }[];
    const topHigh = ranked.find((r) => (r.match_score?.score ?? 0) >= 85);
    if (topHigh) {
      return {
        kind: "review",
        title: `${topHigh.job.company} scores ${topHigh.match_score!.score}%`,
        body: "This strong match hasn't been turned into an application yet — review it now.",
        cta: "Review job",
        to: `/jobs/${topHigh.job.id}`,
      };
    }
    const missingSkill = (pulseQ.data?.top_tags ?? []).find(
      (t) => !profileSkills.has(t.tag.toLowerCase()),
    );
    if (missingSkill) {
      return {
        kind: "skill",
        title: `Add "${missingSkill.tag}" to your profile`,
        body: `It appears in ${missingSkill.pct}% of your saved jobs but is missing from your skills.`,
        cta: "Edit profile",
        to: "/resumes/profile-editor",
      };
    }
    if (latestImportAge > 7) {
      return {
        kind: "cadence",
        title: "No fresh jobs lately",
        body:
          latestImportAge === Infinity
            ? "You haven't imported anything yet — import a job posting to kick off scoring."
            : `Last import was ${latestImportAge} days ago. Fresh jobs keep your matches relevant.`,
        cta: "Import jobs",
        to: "/jobs/import",
      };
    }
    return {
      kind: "clear",
      title: "You're all caught up",
      body: "No overdue tasks. Explore your ranked matches to keep momentum going.",
      cta: "View rankings",
      to: "/ranking",
    };
  })();

  // Checklist state
  const profileReady = !!p && (completeness >= 40 || (p.experiences?.length ?? 0) > 0);
  const jobsImported = (statsQ.data?.total_jobs ?? 0) > 0;
  const resumeGenerated = (statsQ.data?.resumes_generated ?? 0) > 0;
  const doneCount = [profileReady, jobsImported, resumeGenerated].filter(Boolean).length;
  const allDone = doneCount === 3;
  const checklistHidden =
    typeof window !== "undefined" && localStorage.getItem(CHECKLIST_KEY) === "1" && allDone;
  const steps = [
    {
      done: profileReady,
      label: "Create your master profile",
      body: "Build your comprehensive resume profile",
      to: "/resumes/profiles",
    },
    {
      done: jobsImported,
      label: "Import jobs",
      body: "Import jobs from URLs or paste descriptions",
      to: "/jobs/import",
    },
    {
      done: resumeGenerated,
      label: "Generate your first tailored resume",
      body: "Tailor a resume against one of your matched jobs",
      to: "/resumes/builder",
    },
  ];

  // Quick-log application ---------------------------------------------------
  const [dialogCfg, setDialogCfg] = useState<
    (PromptDialogConfig & { resolve: (v: Record<string, string> | null) => void }) | null
  >(null);
  const ask = (config: PromptDialogConfig): Promise<Record<string, string> | null> =>
    new Promise((resolve) => setDialogCfg({ ...config, resolve }));

  const handleQuickLog = async () => {
    try {
      const res = await getJobs({ limit: 30 });
      const jobs: { id: string; title: string; company: string }[] = res.jobs ?? [];
      if (jobs.length === 0) {
        toast.info("Import some jobs first — applications attach to imported jobs.");
        return;
      }
      const values = await ask({
        title: "Log an application",
        description:
          "Pick the job you just applied to. You can refine status, notes, and follow-ups later.",
        confirmLabel: "Log application",
        fields: [
          {
            key: "jobId",
            label: "Job",
            required: true,
            type: "select",
            options: jobs.map((j) => ({ value: j.id, label: `${j.title} — ${j.company}` })),
          },
          {
            key: "status",
            label: "Current status",
            type: "select",
            options: ["applied", "screening", "interview"],
            defaultValue: "applied",
          },
        ],
      });
      if (!values) return;
      const chosen = jobs.find((j) => j.id === values.jobId);
      await createApplication(values.jobId, values.status);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      toast.success(
        `Logged application: ${chosen ? `${chosen.title} at ${chosen.company}` : "done"} ✓`,
      );
    } catch (e: any) {
      toast.error(`Failed to log application: ${e.message}`);
    }
  };

  const statsLoading =
    statsQ.isLoading || appsQ.isLoading || followupsQ.isLoading || profileQ.isLoading;

  return (
    <PageBody>
      <PageHeader
        eyebrow="Welcome back"
        title="Dashboard"
        description="Your job search command center."
        actions={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleQuickLog}
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              + Log application
            </button>
            <Link
              to="/jobs/import"
              className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90"
            >
              Import jobs
            </Link>
          </div>
        }
      />

      {/* AI daily briefing (#5) — falls back silently to Next Best Action */}
      {briefingQ.data?.briefing ? (
        <Panel title={`AI briefing · ${briefingQ.data.date}`}>
          <ul className="space-y-1.5 p-4 text-sm">
            {briefingQ.data.briefing
              .split("\n")
              .filter((l) => l.trim())
              .map((line, i) => (
                <li key={i}>{line.replace(/^•\s*/, "• ")}</li>
              ))}
          </ul>
        </Panel>
      ) : null}

      {/* Next Best Action (#1) */}
      {nextAction ? <NextBestActionCard action={nextAction} /> : null}

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statsLoading && !statsQ.data ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-border bg-card p-4">
              <WidgetSkeleton rows={1} />
            </div>
          ))
        ) : (
          <>
            <StatCard
              label="Active applications"
              value={statsQ.data?.active_applications ?? 0}
              to="/applications"
            />
            <StatCard label="Jobs imported" value={statsQ.data?.total_jobs ?? 0} to="/jobs" />
            <StatCard
              label="Resumes generated"
              value={statsQ.data?.resumes_generated ?? 0}
              to="/resumes"
            />
            <StatCard
              label="Follow-ups · next 7d"
              value={statsQ.data?.upcoming_followups_count ?? 0}
              to="/applications/followups"
              hint={overdueFollowups.length > 0 ? `${overdueFollowups.length} overdue` : undefined}
            />
          </>
        )}
      </div>

      {/* Momentum + Funnel + Sparkline */}
      <div className="grid gap-4 lg:grid-cols-3">
        <MomentumScore score={momentum} delta={momentumDelta} />
        <FunnelChart stages={funnel} />
        <ResponseSparkline sent={sentBuckets} responded={respBuckets} />
      </div>

      {/* Top matches + Follow-ups */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Top job matches" description="Your highest-scoring opportunities right now.">
          {rankedQ.isLoading ? (
            <WidgetSkeleton rows={5} />
          ) : rankedQ.error ? (
            <WidgetError message="Failed to load ranked jobs" onRetry={() => rankedQ.refetch()} />
          ) : (rankedQ.data?.jobs ?? []).length === 0 ? (
            <EmptyState
              title="No matches yet"
              body="Import jobs and run analysis to see rankings."
            />
          ) : (
            <ul className="divide-y divide-border">
              {((rankedQ.data.jobs ?? []) as any[]).slice(0, 5).map((r) => (
                <li key={r.job.id}>
                  <Link
                    to="/jobs/$jobId"
                    params={{ jobId: r.job.id }}
                    className="flex items-center justify-between px-4 py-3 text-sm hover:bg-muted/40"
                  >
                    <span className="min-w-0">
                      <span className="block truncate font-medium">{r.job.title}</span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {r.job.company}
                      </span>
                    </span>
                    {r.match_score ? (
                      <ScorePill value={r.match_score.score} />
                    ) : (
                      <span className="text-[11px] text-muted-foreground">unscored</span>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <div className="border-t border-border px-4 py-2 text-right">
            <Link to="/ranking" className="text-xs text-[color:var(--brand)] hover:underline">
              View full ranking →
            </Link>
          </div>
        </Panel>

        <Panel
          title="Upcoming follow-ups"
          description="Reminders due soon — overdue ones are flagged."
        >
          {followupsQ.isLoading ? (
            <WidgetSkeleton rows={4} />
          ) : upcomingFollowups.length === 0 ? (
            <EmptyState
              title="Nothing scheduled"
              body="Set follow-up reminders from any application."
            />
          ) : (
            <ul className="divide-y divide-border">
              {upcomingFollowups.map((f) => (
                <li key={f.application_id}>
                  <Link
                    to="/applications/$id"
                    params={{ id: f.application_id }}
                    className="flex items-center justify-between px-4 py-3 text-sm hover:bg-muted/40"
                  >
                    <span className="min-w-0">
                      <span className="block truncate font-medium">{f.job_title}</span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {f.company}
                      </span>
                    </span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {new Date(f.follow_up_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <div className="border-t border-border px-4 py-2 text-right">
            <Link
              to="/applications/followups"
              className="text-xs text-[color:var(--brand)] hover:underline"
            >
              Follow-up center →
            </Link>
          </div>
        </Panel>
      </div>

      {/* Market pulse + Onboarding checklist */}
      <div className="grid gap-4 lg:grid-cols-2">
        <MarketPulseWidget
          totalAnalyzed={pulseQ.data?.total_jobs_analyzed ?? 0}
          tags={(pulseQ.data?.top_tags ?? []).slice(0, 8)}
          profileSkills={profileSkills}
        />

        {!checklistHidden && !allDone ? (
          <Panel
            title={`Get started · ${doneCount} of 3 complete`}
            description="Complete these steps to unlock SiraFit's full value."
          >
            <div className="mx-4 mt-3 h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-[color:var(--brand)] transition-all"
                style={{ width: `${(doneCount / 3) * 100}%` }}
              />
            </div>
            <div className="space-y-3 p-4 pt-4">
              {steps.map((s) => (
                <Link
                  key={s.label}
                  to={s.to}
                  className="block rounded-lg border border-border p-4 transition-colors hover:bg-muted/40"
                >
                  <div className="flex items-center justify-between">
                    <div className="min-w-0">
                      <h3 className="font-medium">
                        {s.done ? "✓ " : ""}
                        {s.label}
                      </h3>
                      <p className="mt-1 text-sm text-muted-foreground">{s.body}</p>
                    </div>
                    <span className="ml-3 shrink-0 text-sm text-muted-foreground">→</span>
                  </div>
                </Link>
              ))}
            </div>
          </Panel>
        ) : null}
      </div>

      {/* Recent activity */}
      <Panel title="Recent activity" className="mt-0">
        {statsLoading && !statsQ.data ? (
          <WidgetSkeleton rows={4} />
        ) : !statsQ.data?.recent_activity?.length ? (
          <EmptyState
            title="No activity yet"
            body="Your recent actions will appear here once you start using SiraFit."
          />
        ) : (
          <ul className="divide-y divide-border">
            {statsQ.data.recent_activity.map((activity) => {
              const base = activity.entity_type ? ENTITY_ROUTES[activity.entity_type] : undefined;
              const id = entityId(activity.details);
              const to = base ? (id ? `${base}/${id}` : base) : undefined;
              const count =
                activity.details && typeof activity.details.count === "number"
                  ? ` (${activity.details.count})`
                  : "";
              return (
                <li key={activity.id} className="px-4 py-3 text-sm">
                  {to ? (
                    <Link to={to} className="font-medium hover:underline">
                      {humanizeAction(activity.action)}
                      {count}
                    </Link>
                  ) : (
                    <span className="font-medium">
                      {humanizeAction(activity.action)}
                      {count}
                    </span>
                  )}
                  <span className="ml-2 text-muted-foreground">{timeAgo(activity.created_at)}</span>
                </li>
              );
            })}
          </ul>
        )}
      </Panel>

      {dialogCfg && (
        <PromptDialog
          config={dialogCfg}
          resolve={(v) => {
            dialogCfg.resolve(v);
            setDialogCfg(null);
          }}
        />
      )}
    </PageBody>
  );
}
