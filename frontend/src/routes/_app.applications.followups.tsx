import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill, EmptyState } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getFollowUps,
  setFollowUp,
  getApplications,
  type FollowUpItem,
} from "@/lib/api/applications";

export const Route = createFileRoute("/_app/applications/followups")({
  head: () => ({ meta: [{ title: "Follow-ups · SiraFit" }] }),
  component: FollowUps,
});

// ── helpers ────────────────────────────────────────────────────────────────

function formatDue(dateStr: string) {
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const diffH = Math.round(diffMs / 3_600_000);
  const diffD = Math.round(diffMs / 86_400_000);

  if (diffH < 0) return { label: "Overdue", overdue: true };
  if (diffH < 24) return { label: `In ${diffH}h`, overdue: false };
  if (diffD === 1) return { label: "Tomorrow", overdue: false };
  return {
    label: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    overdue: false,
  };
}

// ── Add / Edit dialog (inline, no modal library needed) ────────────────────

interface SetReminderFormProps {
  applicationId: string;
  current?: FollowUpItem | null;
  onClose: () => void;
}

function SetReminderForm({ applicationId, current, onClose }: SetReminderFormProps) {
  const queryClient = useQueryClient();
  const [date, setDate] = useState(
    current?.follow_up_at ? new Date(current.follow_up_at).toISOString().slice(0, 16) : "",
  );
  const [note, setNote] = useState(current?.follow_up_note || "");

  const mutation = useMutation({
    mutationFn: () =>
      setFollowUp(applicationId, {
        follow_up_at: date ? new Date(date).toISOString() : null,
        follow_up_note: note || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["followups"] });
      onClose();
    },
  });

  const clearMutation = useMutation({
    mutationFn: () => setFollowUp(applicationId, { follow_up_at: null, follow_up_note: null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["followups"] });
      onClose();
    },
  });

  return (
    <div className="mt-2 rounded-md border border-border bg-muted/30 p-4 space-y-3">
      <div>
        <label className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Due date & time
        </label>
        <Input
          type="datetime-local"
          className="mt-1 h-8 text-xs"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>
      <div>
        <label className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Note (optional)
        </label>
        <Input
          className="mt-1 h-8 text-xs"
          placeholder="e.g. Follow up with recruiter"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={() => mutation.mutate()} disabled={!date || mutation.isPending}>
          {mutation.isPending ? "Saving…" : "Save reminder"}
        </Button>
        {current && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => clearMutation.mutate()}
            disabled={clearMutation.isPending}
          >
            Clear
          </Button>
        )}
        <Button size="sm" variant="ghost" onClick={onClose}>
          Cancel
        </Button>
      </div>
      {mutation.error && (
        <div className="text-xs text-destructive">{(mutation.error as Error).message}</div>
      )}
    </div>
  );
}

// ── New reminder picker: choose from existing applications ─────────────────

function NewReminderPicker({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState<"pick" | "set">("pick");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: applications = [], isLoading } = useQuery({
    queryKey: ["applications"],
    queryFn: getApplications,
  });

  if (step === "set" && selectedId) {
    return <SetReminderForm applicationId={selectedId} onClose={onClose} />;
  }

  return (
    <div className="mt-2 rounded-md border border-border bg-muted/30 p-4 space-y-3">
      <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        Choose an application
      </div>
      {isLoading ? (
        <div className="text-xs text-muted-foreground">Loading…</div>
      ) : applications.length === 0 ? (
        <div className="text-xs text-muted-foreground">
          No applications yet.{" "}
          <Link to="/applications" className="underline">
            Go to board →
          </Link>
        </div>
      ) : (
        <div className="max-h-48 overflow-y-auto space-y-1">
          {applications.map((app: any) => (
            <button
              key={app.id}
              onClick={() => {
                setSelectedId(app.id);
                setStep("set");
              }}
              className="w-full rounded border border-border p-2.5 text-left text-xs hover:bg-muted/40"
            >
              <span className="font-medium">{app.job?.company || "Unknown"}</span>
              <span className="ml-2 text-muted-foreground">{app.job?.title}</span>
            </button>
          ))}
        </div>
      )}
      <Button size="sm" variant="ghost" onClick={onClose}>
        Cancel
      </Button>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────

function FollowUps() {
  const queryClient = useQueryClient();
  const [showPast, setShowPast] = useState(false);
  const [addingNew, setAddingNew] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const {
    data: followups = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["followups", showPast],
    queryFn: () => getFollowUps(showPast),
  });

  const clearMutation = useMutation({
    mutationFn: (applicationId: string) =>
      setFollowUp(applicationId, { follow_up_at: null, follow_up_note: null }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["followups"] }),
  });

  const overdue = followups.filter((f) => new Date(f.follow_up_at) < new Date());
  const upcoming = followups.filter((f) => new Date(f.follow_up_at) >= new Date());

  return (
    <PageBody>
      <PageHeader
        eyebrow="Pipeline"
        title="Follow-up center"
        description="Recruiter pings, deadlines, and reminders. Nothing falls through."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowPast((p) => !p)}>
              {showPast ? "Hide past" : "Show past"}
            </Button>
            <Button size="sm" onClick={() => setAddingNew((v) => !v)}>
              + New reminder
            </Button>
          </div>
        }
      />

      {addingNew && <NewReminderPicker onClose={() => setAddingNew(false)} />}

      {error && (
        <div className="rounded-md bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {(error as Error).message}
        </div>
      )}

      {isLoading ? (
        <Panel>
          <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
            <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
            Loading follow-ups…
          </div>
        </Panel>
      ) : followups.length === 0 ? (
        <EmptyState
          title="No follow-ups scheduled"
          body="Set a reminder on any application to see it here."
          action={
            <Button size="sm" onClick={() => setAddingNew(true)}>
              + New reminder
            </Button>
          }
        />
      ) : (
        <div className="space-y-4">
          {overdue.length > 0 && (
            <Panel title={`Overdue (${overdue.length})`}>
              <FollowUpList
                items={overdue}
                editingId={editingId}
                setEditingId={setEditingId}
                onClear={(id) => clearMutation.mutate(id)}
              />
            </Panel>
          )}
          <Panel title={`Upcoming (${upcoming.length})`}>
            {upcoming.length === 0 ? (
              <div className="px-4 py-6 text-sm text-muted-foreground">No upcoming follow-ups.</div>
            ) : (
              <FollowUpList
                items={upcoming}
                editingId={editingId}
                setEditingId={setEditingId}
                onClear={(id) => clearMutation.mutate(id)}
              />
            )}
          </Panel>
        </div>
      )}
    </PageBody>
  );
}

// ── Shared list component ─────────────────────────────────────────────────

function FollowUpList({
  items,
  editingId,
  setEditingId,
  onClear,
}: {
  items: FollowUpItem[];
  editingId: string | null;
  setEditingId: (id: string | null) => void;
  onClear: (id: string) => void;
}) {
  return (
    <ul className="divide-y divide-border">
      {items.map((f) => {
        const due = formatDue(f.follow_up_at);
        return (
          <li key={f.application_id} className="px-4 py-3.5 space-y-1">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div>
                  <div className="text-sm font-medium">
                    {f.follow_up_note || `Follow up · ${f.company}`}
                  </div>
                  <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                    <Link
                      to="/applications/$id"
                      params={{ id: f.application_id }}
                      className="hover:underline"
                    >
                      {f.company} · {f.job_title}
                    </Link>
                    <StatusPill status={f.status} />
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span
                  className={`font-mono text-[11px] tabular-nums ${
                    due.overdue ? "font-semibold text-destructive" : "text-muted-foreground"
                  }`}
                >
                  {due.label}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setEditingId(editingId === f.application_id ? null : f.application_id)
                  }
                >
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onClear(f.application_id)}
                  className="text-muted-foreground hover:text-destructive"
                >
                  Clear
                </Button>
              </div>
            </div>
            {editingId === f.application_id && (
              <SetReminderForm
                applicationId={f.application_id}
                current={f}
                onClose={() => setEditingId(null)}
              />
            )}
          </li>
        );
      })}
    </ul>
  );
}
