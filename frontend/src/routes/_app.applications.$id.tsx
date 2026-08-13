import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill, Tag } from "@/components/sirafit/bits";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getApplication,
  getApplicationNotes,
  createApplicationNote,
  updateApplicationNote,
  deleteApplicationNote,
  getApplicationContacts,
  createApplicationContact,
  getApplicationEvents,
  setFollowUp,
  type ApplicationNote,
  type ApplicationContact,
} from "@/lib/api/applications";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/applications/$id")({
  head: () => ({ meta: [{ title: "Application · SiraFit" }] }),
  component: AppDetails,
});

function AppDetails() {
  const { id } = Route.useParams();
  const queryClient = useQueryClient();

  const { data: application, isLoading } = useQuery({
    queryKey: ["application", id],
    queryFn: () => getApplication(id),
  });

  const { data: notes = [] } = useQuery({
    queryKey: ["application-notes", id],
    queryFn: () => getApplicationNotes(id),
    enabled: !!application,
  });

  const { data: contacts = [] } = useQuery({
    queryKey: ["application-contacts", id],
    queryFn: () => getApplicationContacts(id),
    enabled: !!application,
  });

  // Fetch events from the dedicated endpoint (not from application.events)
  const { data: events = [] } = useQuery({
    queryKey: ["application-events", id],
    queryFn: () => getApplicationEvents(id),
    enabled: !!application,
  });

  const [newNote, setNewNote] = useState("");
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editBody, setEditBody] = useState("");

  // Add contact form state
  const [showAddContact, setShowAddContact] = useState(false);
  const [contactForm, setContactForm] = useState({
    name: "",
    email: "",
    phone: "",
    role: "recruiter",
    linkedin: "",
  });

  const addNoteMutation = useMutation({
    mutationFn: (body: string) => createApplicationNote(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application-notes", id] });
      setNewNote("");
    },
  });

  const updateNoteMutation = useMutation({
    mutationFn: (vars: { noteId: string; body: string; pinned: boolean }) =>
      updateApplicationNote(vars.noteId, vars.body, vars.pinned),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application-notes", id] });
      setEditingNoteId(null);
      setEditBody("");
    },
  });

  const deleteNoteMutation = useMutation({
    mutationFn: (noteId: string) => deleteApplicationNote(noteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application-notes", id] });
    },
  });

  const addContactMutation = useMutation({
    mutationFn: () =>
      createApplicationContact(id, {
        name: contactForm.name,
        email: contactForm.email || undefined,
        phone: contactForm.phone || undefined,
        role: contactForm.role,
        linkedin: contactForm.linkedin || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application-contacts", id] });
      setShowAddContact(false);
      setContactForm({ name: "", email: "", phone: "", role: "recruiter", linkedin: "" });
      toast.success("Contact added");
    },
    onError: (err: any) => {
      toast.error(err.message || "Failed to add contact");
    },
  });

  const handleAddNote = () => {
    if (newNote.trim()) addNoteMutation.mutate(newNote);
  };

  const startEdit = (note: ApplicationNote) => {
    setEditingNoteId(note.id);
    setEditBody(note.body);
  };

  const cancelEdit = () => {
    setEditingNoteId(null);
    setEditBody("");
  };

  const saveEdit = (note: ApplicationNote) => {
    if (editBody.trim()) {
      updateNoteMutation.mutate({ noteId: note.id, body: editBody, pinned: note.pinned });
    }
  };

  const togglePin = (note: ApplicationNote) => {
    updateNoteMutation.mutate({ noteId: note.id, body: note.body, pinned: !note.pinned });
  };

  if (isLoading || !application) {
    return (
      <PageBody>
        <PageHeader eyebrow={`Application · ${id}`} title="Loading..." />
        <div className="grid place-items-center py-20">Loading application...</div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow={`Application · ${id.substring(0, 8)}`}
        title={application.job?.title || "Unknown position"}
        description={`${application.job?.company || "Unknown company"} · Applied ${new Date(application.created_at).toLocaleDateString()}`}
        actions={
          <>
            {application.status && <StatusPill status={application.status} />}
            <Link
              to="/applications"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              Back to board
            </Link>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          {/* Status history — uses dedicated events query */}
          <Panel title="Status history">
            <ul className="divide-y divide-border">
              {events.length === 0 ? (
                <li className="px-4 py-3 text-sm text-muted-foreground">No events yet</li>
              ) : (
                events.map((event: any) => (
                  <li key={event.id} className="flex items-center gap-4 px-4 py-2.5 text-sm">
                    <span className="w-40 font-mono text-[11px] text-muted-foreground tabular-nums">
                      {new Date(event.occurred_at).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    {event.event_type === "status_change" ? (
                      <StatusPill status={event.event_metadata?.to_status || event.event_type} />
                    ) : (
                      <span className="rounded-full bg-muted px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
                        {event.event_type.replace(/_/g, " ")}
                      </span>
                    )}
                    <span className="text-foreground/90">{event.description || event.title}</span>
                  </li>
                ))
              )}
            </ul>
          </Panel>

          {/* Notes */}
          <Panel title="Notes">
            <div className="space-y-3 p-5">
              {notes.map((note: any) => (
                <div key={note.id} className="rounded bg-muted/40 p-3 text-sm ring-1 ring-transparent">
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-mono text-[10px] text-muted-foreground">
                      {note.author || "Me"} · {new Date(note.created_at).toLocaleDateString()}
                    </div>
                    <div className="flex shrink-0 items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => togglePin(note)}
                        className="rounded px-1.5 py-0.5 text-[10px] font-medium ring-1 ring-border hover:bg-muted"
                      >
                        {note.pinned ? "★ Pinned" : "☆ Pin"}
                      </button>
                      <button
                        type="button"
                        onClick={() => startEdit(note)}
                        className="rounded px-1.5 py-0.5 text-[10px] font-medium ring-1 ring-border hover:bg-muted"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteNoteMutation.mutate(note.id)}
                        disabled={deleteNoteMutation.isPending}
                        className="rounded px-1.5 py-0.5 text-[10px] font-medium text-destructive ring-1 ring-destructive/30 hover:bg-destructive/10 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  {editingNoteId === note.id ? (
                    <div className="mt-2 space-y-2">
                      <textarea
                        className="w-full rounded-md border border-input bg-background p-2 text-sm"
                        rows={3}
                        value={editBody}
                        onChange={(e) => setEditBody(e.target.value)}
                        autoFocus
                      />
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => saveEdit(note)}
                          disabled={!editBody.trim() || updateNoteMutation.isPending}
                          className="rounded-md bg-foreground px-3 py-1 text-xs font-medium text-background disabled:opacity-50"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={cancelEdit}
                          className="rounded-md px-3 py-1 text-xs font-medium ring-1 ring-border hover:bg-muted"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-1 whitespace-pre-wrap">{note.body}</div>
                  )}
                </div>
              ))}
              <textarea
                className="w-full rounded-md border border-input bg-background p-2 text-sm"
                rows={3}
                placeholder="Add a note… (Enter to save, Shift+Enter for newline)"
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleAddNote())
                }
              />
              <button
                onClick={handleAddNote}
                disabled={!newNote.trim() || addNoteMutation.isPending}
                className="rounded-md bg-foreground px-3 py-1 text-sm font-medium text-background disabled:opacity-50"
              >
                Add note
              </button>
            </div>
          </Panel>

          {/* Documents */}
          <Panel title="Documents">
            <ul className="divide-y divide-border text-sm">
              {application.resumes?.length > 0 ? (
                application.resumes.map((resume: any) => (
                  <li key={resume.id} className="flex items-center justify-between px-4 py-2.5">
                    <span>{resume.title}</span>
                    <Link
                      to="/resumes/$id"
                      params={{ id: resume.id }}
                      className="text-[color:var(--brand)] hover:underline"
                    >
                      Preview →
                    </Link>
                  </li>
                ))
              ) : (
                <li className="px-4 py-3 text-muted-foreground">No documents attached</li>
              )}
            </ul>
          </Panel>
        </div>

        <div className="space-y-4">
          {/* Contacts */}
          <Panel
            title="Contacts"
            actions={
              <button
                onClick={() => setShowAddContact((v) => !v)}
                className="text-[11px] font-medium text-[color:var(--brand)] hover:underline"
              >
                {showAddContact ? "Cancel" : "+ Add"}
              </button>
            }
          >
            {showAddContact && (
              <div className="border-b border-border p-4 space-y-2">
                <Input
                  placeholder="Name *"
                  className="h-8 text-xs"
                  value={contactForm.name}
                  onChange={(e) => setContactForm((f) => ({ ...f, name: e.target.value }))}
                />
                <Input
                  placeholder="Email"
                  className="h-8 text-xs"
                  value={contactForm.email}
                  onChange={(e) => setContactForm((f) => ({ ...f, email: e.target.value }))}
                />
                <Input
                  placeholder="Phone"
                  className="h-8 text-xs"
                  value={contactForm.phone}
                  onChange={(e) => setContactForm((f) => ({ ...f, phone: e.target.value }))}
                />
                <Input
                  placeholder="LinkedIn URL"
                  className="h-8 text-xs"
                  value={contactForm.linkedin}
                  onChange={(e) => setContactForm((f) => ({ ...f, linkedin: e.target.value }))}
                />
                <select
                  className="h-8 w-full rounded-md border border-border bg-card px-2 text-xs"
                  value={contactForm.role}
                  onChange={(e) => setContactForm((f) => ({ ...f, role: e.target.value }))}
                >
                  <option value="recruiter">Recruiter</option>
                  <option value="hiring_manager">Hiring Manager</option>
                  <option value="hr">HR</option>
                  <option value="referrer">Referrer</option>
                  <option value="interviewer">Interviewer</option>
                  <option value="other">Other</option>
                </select>
                <Button
                  size="sm"
                  className="w-full"
                  disabled={!contactForm.name.trim() || addContactMutation.isPending}
                  onClick={() => addContactMutation.mutate()}
                >
                  {addContactMutation.isPending ? "Saving…" : "Save contact"}
                </Button>
              </div>
            )}
            {contacts.length === 0 && !showAddContact ? (
              <div className="px-4 py-3 text-sm text-muted-foreground">No contacts yet.</div>
            ) : (
              contacts.map((contact: any) => (
                <div key={contact.id} className="space-y-1 p-4 text-sm border-b border-border last:border-0">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-semibold">{contact.name}</div>
                      <div className="text-muted-foreground capitalize">{contact.role.replace(/_/g, " ")}</div>
                    </div>
                    {contact.is_primary && (
                      <span className="rounded bg-[color:var(--brand)]/10 px-1.5 py-0.5 text-[10px] font-medium text-[color:var(--brand)]">
                        Primary
                      </span>
                    )}
                  </div>
                  {contact.email && (
                    <div className="font-mono text-[11px] text-muted-foreground">{contact.email}</div>
                  )}
                  {contact.phone && (
                    <div className="font-mono text-[11px] text-muted-foreground">{contact.phone}</div>
                  )}
                  {contact.linkedin && (
                    <a
                      href={contact.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block font-mono text-[11px] text-[color:var(--brand)] hover:underline truncate"
                    >
                      {contact.linkedin}
                    </a>
                  )}
                </div>
              ))
            )}
          </Panel>

          {/* Compensation — only real data, no placeholder equity/sponsorship */}
          {(application.job?.salary_min || application.job?.salary_max) && (
            <Panel title="Compensation">
              <div className="space-y-1 p-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Posted range: </span>
                  {application.job.salary_min && application.job.salary_max
                    ? `$${application.job.salary_min.toLocaleString()} – $${application.job.salary_max.toLocaleString()}`
                    : application.job.salary_max
                      ? `Up to $${application.job.salary_max.toLocaleString()}`
                      : `$${application.job.salary_min?.toLocaleString()}+`}
                  {application.job.currency && application.job.currency !== "USD" && (
                    <span className="ml-1 text-muted-foreground">({application.job.currency})</span>
                  )}
                </div>
              </div>
            </Panel>
          )}

          <FollowUpPanel
            applicationId={id}
            currentFollowUpAt={application.follow_up_at}
            currentNote={application.follow_up_note}
          />

          {/* Tags */}
          {application.job?.tags?.length > 0 && (
            <Panel title="Tags">
              <div className="flex flex-wrap gap-1.5 p-4">
                {application.job.tags.map((tag: string) => (
                  <Tag key={tag}>{tag}</Tag>
                ))}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </PageBody>
  );
}

// ── Follow-up panel ──────────────────────────────────────────────────────

function FollowUpPanel({
  applicationId,
  currentFollowUpAt,
  currentNote,
}: {
  applicationId: string;
  currentFollowUpAt?: string | null;
  currentNote?: string | null;
}) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [date, setDate] = useState(
    currentFollowUpAt ? new Date(currentFollowUpAt).toISOString().slice(0, 16) : "",
  );
  const [note, setNote] = useState(currentNote || "");

  const saveMutation = useMutation({
    mutationFn: () =>
      setFollowUp(applicationId, {
        follow_up_at: date ? new Date(date).toISOString() : null,
        follow_up_note: note || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application", applicationId] });
      queryClient.invalidateQueries({ queryKey: ["followups"] });
      setEditing(false);
    },
  });

  const clearMutation = useMutation({
    mutationFn: () => setFollowUp(applicationId, { follow_up_at: null, follow_up_note: null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application", applicationId] });
      queryClient.invalidateQueries({ queryKey: ["followups"] });
      setDate("");
      setNote("");
    },
  });

  return (
    <Panel title="Follow-up reminder">
      <div className="p-4 space-y-3 text-sm">
        {currentFollowUpAt && !editing ? (
          <>
            <div>
              <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                Due
              </div>
              <div className="mt-0.5">
                {new Date(currentFollowUpAt).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
            {currentNote && (
              <div>
                <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  Note
                </div>
                <div className="mt-0.5 text-foreground/90">{currentNote}</div>
              </div>
            )}
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                Edit
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-muted-foreground hover:text-destructive"
                onClick={() => clearMutation.mutate()}
                disabled={clearMutation.isPending}
              >
                Clear
              </Button>
            </div>
          </>
        ) : (
          <>
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
              <Button
                size="sm"
                disabled={!date || saveMutation.isPending}
                onClick={() => saveMutation.mutate()}
              >
                {saveMutation.isPending ? "Saving…" : "Set reminder"}
              </Button>
              {editing && (
                <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              )}
            </div>
            {saveMutation.error && (
              <div className="text-xs text-destructive">
                {(saveMutation.error as Error).message}
              </div>
            )}
          </>
        )}
      </div>
    </Panel>
  );
}
