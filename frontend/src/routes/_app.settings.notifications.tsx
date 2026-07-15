import { createFileRoute } from "@tanstack/react-router";
import { Panel } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useState } from "react";

const rows = [
  ["Resume generation complete", true, true],
  ["High-match job ingested (>85%)", true, false],
  ["Interview scheduled / updated", true, true],
  ["Recruiter follow-up reminders", true, true],
  ["Scraper rate-limit warnings", false, false],
  ["Sync failure (degraded mode)", true, false],
] as const;

export const Route = createFileRoute("/_app/settings/notifications")({
  head: () => ({ meta: [{ title: "Notification settings · SiraFit" }] }),
  component: NotificationsSettings,
});

function NotificationsSettings() {
  const [preferences, setPreferences] = useState(
    rows.map(([label, inApp, email]) => ({ label, inApp, email })),
  );

  const saveMutation = useMutation({
    mutationFn: async () => {
      // Mock API call
      await new Promise((resolve) => setTimeout(resolve, 500));
      return true;
    },
    onSuccess: () => {
      toast.success("Notification preferences updated");
    },
    onError: () => {
      toast.error("Failed to update notification preferences");
    },
  });

  const handleToggle = (index: number, type: "inApp" | "email") => {
    const newPrefs = [...preferences];
    newPrefs[index][type] = !newPrefs[index][type];
    setPreferences(newPrefs);
  };

  return (
    <div className="grid gap-4">
      <Panel title="Channels">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-muted/40 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5">Event</th>
              <th className="px-4 py-2.5">In-app</th>
              <th className="px-4 py-2.5">Email</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {preferences.map((pref, i) => (
              <tr key={pref.label as string}>
                <td className="px-4 py-3">{pref.label}</td>
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={pref.inApp as boolean}
                    onChange={() => handleToggle(i, "inApp")}
                    className="h-4 w-4"
                  />
                </td>
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={pref.email as boolean}
                    onChange={() => handleToggle(i, "email")}
                    className="h-4 w-4"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <div className="flex justify-end">
        <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
          {saveMutation.isPending ? "Saving..." : "Save preferences"}
        </Button>
      </div>
    </div>
  );
}
