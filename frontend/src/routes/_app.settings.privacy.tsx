import { createFileRoute } from "@tanstack/react-router";
import { Panel } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { exportUserData, deleteAccount } from "@/lib/api/users";
import { apiFetch } from "@/lib/api/client";
import { TwoFactorStatus, TwoFactorSetup } from "@/components/auth/TwoFactorAuth";
import { useState } from "react";

export const Route = createFileRoute("/_app/settings/privacy")({
  head: () => ({ meta: [{ title: "Data & privacy · SiraFit" }] }),
  component: PrivacySettings,
});

function PrivacySettings() {
  const [show2FASetup, setShow2FASetup] = useState(false);

  // Fetch 2FA status
  const { data: twoFAStatus, refetch: refetch2FA } = useQuery({
    queryKey: ["2fa-status"],
    queryFn: async () => {
      const response = await apiFetch("/api/v1/auth/2fa/status", {
        method: "POST",
      });
      if (!response.ok) return { enabled: false };
      return response.json();
    },
  });

  const disable2FAMutation = useMutation({
    mutationFn: async (password: string) => {
      const response = await apiFetch("/api/v1/auth/2fa/disable", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to disable 2FA");
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success("2FA has been disabled");
      refetch2FA();
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });

  const handleDisable2FA = () => {
    const password = window.prompt("Enter your password to disable 2FA:");
    if (password) {
      disable2FAMutation.mutate(password);
    }
  };

  const exportMutation = useMutation({
    mutationFn: async () => {
      const data = await exportUserData();
      // Trigger download of the exported data
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "sirafit-data-export.json";
      a.click();
      URL.revokeObjectURL(url);
      return true;
    },
    onSuccess: () => {
      toast.success("Your data export has been generated and downloaded.");
    },
    onError: () => {
      toast.error("Failed to generate export");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await deleteAccount();
      return true;
    },
    onSuccess: () => {
      toast.success("Account deleted successfully");
      // Log the user out and redirect to login
      window.location.href = "/login";
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
      <Panel title="Security">
        <div className="p-4">
          {show2FASetup ? (
            <TwoFactorSetup
              onComplete={() => {
                setShow2FASetup(false);
                refetch2FA();
              }}
              onCancel={() => setShow2FASetup(false)}
            />
          ) : (
            <TwoFactorStatus
              enabled={twoFAStatus?.enabled ?? false}
              recoveryCodesRemaining={twoFAStatus?.recovery_codes_remaining}
              onSetup={() => setShow2FASetup(true)}
              onDisable={handleDisable2FA}
            />
          )}
        </div>
      </Panel>
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
