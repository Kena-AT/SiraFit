import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/sirafit/shell";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/verify-email")({
  head: () => ({ meta: [{ title: "Verify email · SiraFit" }] }),
  component: () => (
    <AuthShell title="Verify your email" subtitle="We sent a 6-digit code to your inbox." footer={<>Didn't get it? <button className="font-medium text-foreground hover:underline">Resend</button></>}>
      <div className="space-y-4">
        <div className="flex justify-between gap-2">
          {[0,1,2,3,4,5].map((i) => (<input key={i} maxLength={1} className="h-12 w-10 rounded-md border border-input bg-background text-center font-mono text-lg outline-hidden focus:border-[color:var(--brand)]" />))}
        </div>
        <Button asChild className="w-full"><Link to="/dashboard">Verify and continue</Link></Button>
      </div>
    </AuthShell>
  ),
});