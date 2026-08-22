import { Link, useRouter } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";

/**
 * Reusable error boundary for route layouts. Catches a render/loader crash in
 * the subtree it's attached to and shows a recoverable screen instead of
 * letting the error bubble to the root boundary (which would blank the app).
 */
export function RouteErrorBoundary({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter();
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          This section didn&apos;t load
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Something went wrong while rendering this page. You can try again or head
          back to the dashboard.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <Button
            onClick={() => {
              router.invalidate();
              reset();
            }}
          >
            Try again
          </Button>
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Go to dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
