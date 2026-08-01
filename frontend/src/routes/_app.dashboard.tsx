import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, EmptyState } from "@/components/sirafit/bits";
import { getDashboardStats } from "@/lib/api/dashboard";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard · SiraFit" }] }),
  component: Dashboard,
});

function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
  });

  return (
    <PageBody>
      <PageHeader
        eyebrow="Welcome"
        title="Dashboard"
        description="Your job search command center"
        actions={
          <Link
            to="/jobs/import"
            className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90"
          >
            Import jobs
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        {[
          ["Active Apps", stats?.active_applications ?? 0],
          ["Resumes Generated", stats?.resumes_generated ?? 0],
          ["Jobs Scored", stats?.jobs_scored ?? 0],
        ].map(([label, value]) => (
          <Panel key={label as string} className="p-4">
            <div className="text-sm text-muted-foreground">{label}</div>
            <div className="text-2xl font-bold">{value}</div>
          </Panel>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Get Started" description="Complete these steps to begin your job search">
          <div className="space-y-4 p-4">
            <Link
              to="/resumes/profiles"
              className="block rounded-lg border border-border p-4 hover:bg-muted/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Create Your Master Profile</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Build your comprehensive resume profile
                  </p>
                </div>
                <span className="text-sm text-muted-foreground">→</span>
              </div>
            </Link>

            <Link
              to="/jobs/import"
              className="block rounded-lg border border-border p-4 hover:bg-muted/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Import Jobs</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Import jobs from URLs or paste descriptions
                  </p>
                </div>
                <span className="text-sm text-muted-foreground">→</span>
              </div>
            </Link>

            <Link
              to="/match"
              className="block rounded-lg border border-border p-4 hover:bg-muted/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Match & Score Jobs</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    See how your profile matches your saved jobs
                  </p>
                </div>
                <span className="text-sm text-muted-foreground">→</span>
              </div>
            </Link>
          </div>
        </Panel>

        <Panel title="Quick Actions">
          <div className="grid gap-px bg-border sm:grid-cols-2">
            {[
              ["Import Job", "/jobs/import"],
              ["View History", "/jobs/history"],
              ["Resume Profiles", "/resumes/profiles"],
              ["Settings", "/settings"],
            ].map(([label, to]) => (
              <Link
                key={to}
                to={to}
                className="bg-card px-4 py-4 text-sm font-medium hover:bg-muted/40"
              >
                <div className="text-foreground">{label} →</div>
              </Link>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Recent Activity" className="mt-4">
        {stats?.recent_activity && stats.recent_activity.length > 0 ? (
          <ul className="divide-y divide-border">
            {stats.recent_activity.map((activity) => (
              <li key={activity.id} className="p-4 text-sm">
                <span className="font-medium">{activity.action}</span>
                <span className="text-muted-foreground ml-2">
                  {new Date(activity.created_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="No activity yet"
            body="Your recent actions and updates will appear here once you start using SiraFit."
          />
        )}
      </Panel>
    </PageBody>
  );
}
