import { createFileRoute } from "@tanstack/react-router";
import { Panel } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useState, useEffect } from "react";
import {
  getNotificationPreferences,
  updateNotificationPreferences,
  type NotificationPreferences,
} from "@/lib/api/users";

interface PrefRow {
  id: string;
  label: string;
  emailKey: keyof NotificationPreferences;
  inAppEnabled: boolean;
}

const rows: PrefRow[] = [
  { id: "resume_gen", label: "Resume generation complete", emailKey: "email_new_opportunities", inAppEnabled: true },
  { id: "high_match", label: "High-match job ingested (>85%)", emailKey: "email_job_matches", inAppEnabled: false },
  { id: "interview", label: "Interview scheduled / updated", emailKey: "email_new_opportunities", inAppEnabled: true },
  { id: "followup", label: "Recruiter follow-up reminders", emailKey: "email_new_opportunities", inAppEnabled: true },
  { id: "scraper_warn", label: "Scraper rate-limit warnings", emailKey: "email_new_opportunities", inAppEnabled: false },
  { id: "sync_fail", label: "Sync failure (degraded mode)", emailKey: "email_new_opportunities", inAppEnabled: true },
];

export const Route = createFileRoute("/_app/settings/notifications")({
  head: () => ({ meta: [{ title: "Notification settings · SiraFit" }] }),
  component: NotificationsSettings,
});

function NotificationsSettings() {
  const queryClient = useQueryClient();

  const { data: prefs, isLoading } = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: getNotificationPreferences,
  });

  const saveMutation = useMutation({
    mutationFn: async (updatedPrefs: Partial<NotificationPreferences>) => {
      return updateNotificationPreferences(updatedPrefs);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
      toast.success("Notification preferences updated");
    },
    onError: (error) => {
      toast.error(`Failed to update preferences: ${error.message}`);
    },
  });

  const [localPrefs, setLocalPrefs] = useState<NotificationPreferences | null>(null);

  useEffect(() => {
    if (prefs) setLocalPrefs(prefs);
  }, [prefs]);

  const handleToggle = (emailKey: keyof NotificationPreferences) => {
    if (!localPrefs) return;
    const newPrefs = { ...localPrefs, [emailKey]: !localPrefs[emailKey] };
    setLocalPrefs(newPrefs);
    saveMutation.mutate({ [emailKey]: newPrefs[emailKey] });
  };

  if (isLoading || !localPrefs) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Loading notification preferences...
      </div>
    );
  }

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
            {rows.map((row) => (
              <tr key={row.id}>
                <td className="px-4 py-3">{row.label}</td>
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={row.inAppEnabled}
                    disabled
                    className="h-4 w-4"
                  />
                </td>
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={localPrefs[row.emailKey] as boolean}
                    onChange={() => handleToggle(row.emailKey)}
                    className="h-4 w-4"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <div className="flex justify-end">
        <Button disabled={saveMutation.isPending}>
          {saveMutation.isPending ? "Saving..." : "Preferences saved automatically"}
        </Button>
      </div>
    </div>
  );
}
