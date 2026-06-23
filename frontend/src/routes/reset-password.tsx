import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/sirafit/shell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/reset-password")({
  head: () => ({ meta: [{ title: "Set new password · SiraFit" }] }),
  component: () => (
    <AuthShell title="Set a new password" subtitle="Use 12+ characters with at least one number." footer={<Link to="/login" className="font-medium text-foreground hover:underline">Back to login</Link>}>
      <form className="space-y-4">
        <div className="space-y-1.5"><Label htmlFor="p1">New password</Label><Input id="p1" type="password" /></div>
        <div className="space-y-1.5"><Label htmlFor="p2">Confirm password</Label><Input id="p2" type="password" /></div>
        <Button asChild className="w-full"><Link to="/login">Update password</Link></Button>
      </form>
    </AuthShell>
  ),
});