import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, EmptyState } from "@/components/sirafit/bits";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard · SiraFit" }] }),
  component: Dashboard,
});

function Dashboard() {
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

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Get Started" description="Complete these steps to begin your job search">
          <div className="space-y-4 p-4">
            <Link 
              to="/resume-profiles" 
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

            <div className="rounded-lg border border-dashed border-border p-4 opacity-50">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Match & Score Jobs</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Coming in Sprint 4
                  </p>
                </div>
                <span className="text-sm text-muted-foreground">🔜</span>
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="Quick Actions">
          <div className="grid gap-px bg-border sm:grid-cols-2">
            {[
              ["Import Job", "/jobs/import"],
              ["View History", "/jobs/history"],
              ["Resume Profiles", "/resume-profiles"],
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

      <Panel title="Recent Activity">
        <EmptyState
          title="No activity yet"
          body="Your recent actions and updates will appear here once you start using SiraFit."
        />
      </Panel>
    </PageBody>
  );
}