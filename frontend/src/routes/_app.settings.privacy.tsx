import { createFileRoute } from "@tanstack/react-router";
import { Panel } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/settings/privacy")({
  head: () => ({ meta: [{ title: "Data & privacy · SiraFit" }] }),
  component: PrivacySettings,
});

function PrivacySettings() {
  const exportMutation = useMutation({
    mutationFn: async () => {
      // Mock API call
      await new Promise((resolve) => setTimeout(resolve, 1500));
      return true;
    },
    onSuccess: () => {
      toast.success("Your data export has been queued. You will receive an email shortly.");
    },
    onError: () => {
      toast.error("Failed to generate export");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      // Mock API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return true;
    },
    onSuccess: () => {
      toast.success("Account deleted successfully");
      // In reality, this would log the user out and redirect
    },
    onError: () => {
      toast.error("Failed to delete account");
    },
  });

  const handleDelete = () => {
    if (
      window.confirm(
        "Are you sure you want to permanently delete your account? This action cannot be undone.",
      )
    ) {
      deleteMutation.mutate();
    }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Export your data">
        <div className="space-y-3 p-4 text-sm">
          <p>
            Download a JSON archive of every job, application, resume, and event in your account.
          </p>
          <Button onClick={() => exportMutation.mutate()} disabled={exportMutation.isPending}>
            {exportMutation.isPending ? "Generating..." : "Generate export"}
          </Button>
        </div>
      </Panel>
      <Panel title="Retention">
        <div className="space-y-3 p-4 text-sm">
          <div className="flex items-center justify-between">
            <span>Raw HTML</span>
            <span className="font-mono text-muted-foreground">30 days</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Event log (cloud)</span>
            <span className="font-mono text-muted-foreground">365 days</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Event log (local)</span>
            <span className="font-mono text-muted-foreground">forever</span>
          </div>
        </div>
      </Panel>
      <Panel title="Danger zone" className="lg:col-span-2">
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm border border-red-500/20 rounded-lg">
          <div>
            Permanently delete your account, cloud projections, and local agent registration.
          </div>
          <Button variant="destructive" onClick={handleDelete} disabled={deleteMutation.isPending}>
            {deleteMutation.isPending ? "Deleting..." : "Delete account"}
          </Button>
        </div>
      </Panel>
    </div>
  );
}
