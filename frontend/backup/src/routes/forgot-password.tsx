import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/sirafit/shell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({ meta: [{ title: "Reset password · SiraFit" }] }),
  component: () => (
    <AuthShell title="Reset your password" subtitle="We'll email a one-time reset link." footer={<Link to="/login" className="font-medium text-foreground hover:underline">Back to login</Link>}>
      <form className="space-y-4">
        <div className="space-y-1.5"><Label htmlFor="e">Email</Label><Input id="e" type="email" placeholder="you@email.com" /></div>
        <Button asChild className="w-full"><Link to="/reset-password">Send reset link</Link></Button>
      </form>
    </AuthShell>
  ),
});