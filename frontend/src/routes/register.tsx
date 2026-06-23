import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/sirafit/shell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/register")({
  head: () => ({ meta: [{ title: "Create account · SiraFit" }] }),
  component: () => (
    <AuthShell title="Create your account" subtitle="One device per account. Bring your own Gemini key." footer={<>Have an account? <Link to="/login" className="font-medium text-foreground hover:underline">Log in</Link>.</>}>
      <form className="space-y-4">
        <div className="space-y-1.5"><Label htmlFor="n">Name</Label><Input id="n" placeholder="Alex Rivera" /></div>
        <div className="space-y-1.5"><Label htmlFor="e">Email</Label><Input id="e" type="email" placeholder="alex@rivera.dev" /></div>
        <div className="space-y-1.5"><Label htmlFor="p">Password</Label><Input id="p" type="password" placeholder="At least 12 characters" /></div>
        <Button asChild className="w-full"><Link to="/verify-email">Create account</Link></Button>
      </form>
    </AuthShell>
  ),
});