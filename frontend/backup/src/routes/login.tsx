import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/sirafit/shell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Log in · SiraFit" }] }),
  component: () => (
    <AuthShell title="Welcome back" subtitle="Log in to your SiraFit dashboard." footer={<>No account? <Link to="/register" className="font-medium text-foreground hover:underline">Create one</Link>.</>}>
      <form className="space-y-4">
        <div className="space-y-1.5"><Label htmlFor="email">Email</Label><Input id="email" type="email" placeholder="alex@rivera.dev" /></div>
        <div className="space-y-1.5"><div className="flex items-center justify-between"><Label htmlFor="pwd">Password</Label><Link to="/forgot-password" className="text-[11px] text-muted-foreground hover:text-foreground">Forgot?</Link></div><Input id="pwd" type="password" placeholder="••••••••" /></div>
        <Button asChild className="w-full"><Link to="/dashboard">Log in</Link></Button>
        <div className="text-center text-[11px] text-muted-foreground">Protected by device-based auth tokens.</div>
      </form>
    </AuthShell>
  ),
});