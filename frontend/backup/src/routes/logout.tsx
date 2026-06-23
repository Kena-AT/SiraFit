import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/sirafit/shell";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/logout")({
  head: () => ({ meta: [{ title: "Logged out · SiraFit" }] }),
  component: () => (
    <AuthShell title="You're logged out" subtitle="Your local agent continues running until you stop it.">
      <div className="space-y-3">
        <Button asChild className="w-full"><Link to="/login">Log back in</Link></Button>
        <Button variant="outline" asChild className="w-full"><Link to="/">Back to home</Link></Button>
      </div>
    </AuthShell>
  ),
});