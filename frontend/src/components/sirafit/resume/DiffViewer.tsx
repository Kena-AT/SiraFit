import React from "react";
import type { ResumeDiffResponse } from "@/types/resume";
import { Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";

interface DiffViewerProps {
  diff: ResumeDiffResponse | null;
  isLoading: boolean;
  error: string | null;
  onClose: () => void;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  diff,
  isLoading,
  error,
  onClose,
}) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-3">
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-border border-t-foreground" />
        <p className="text-sm text-muted-foreground">Analyzing semantic differences between versions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center space-y-3">
        <div className="text-sm font-medium text-destructive">Failed to compare versions</div>
        <div className="text-xs text-muted-foreground">{error}</div>
        <Button variant="outline" size="sm" onClick={onClose}>
          Close
        </Button>
      </div>
    );
  }

  if (!diff) return null;

  const { from_version_number, to_version_number, has_changes, summary, sections } = diff;

  return (
    <div className="space-y-6">
      {/* Header & Diff Summary Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="font-semibold text-base">
            Version Comparison: <span className="font-mono text-[color:var(--brand)]">v{from_version_number}</span> → <span className="font-mono text-[color:var(--brand)]">v{to_version_number}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Structured semantic changes between these snapshots
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
            +{summary.added} added
          </span>
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 border border-rose-500/20">
            -{summary.removed} removed
          </span>
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 border border-amber-500/20">
            ~{summary.changed} modified
          </span>
        </div>
      </div>

      {!has_changes ? (
        <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
          No differences found. Both versions have identical content.
        </div>
      ) : (
        <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-1">
          {/* Summary Diff */}
          {sections.summary.changed && (
            <div className="rounded-md border border-border p-4 space-y-2">
              <h4 className="font-mono text-xs uppercase tracking-wider font-semibold text-foreground">
                Professional Summary
              </h4>
              <div className="grid md:grid-cols-2 gap-4 text-xs">
                <div className="p-2.5 rounded bg-rose-500/5 border border-rose-500/20 text-foreground/90">
                  <span className="text-[10px] font-mono text-rose-500 uppercase tracking-wider block mb-1">
                    v{from_version_number}
                  </span>
                  {sections.summary.from_text || <span className="italic text-muted-foreground">Empty</span>}
                </div>
                <div className="p-2.5 rounded bg-emerald-500/5 border border-emerald-500/20 text-foreground/90">
                  <span className="text-[10px] font-mono text-emerald-500 uppercase tracking-wider block mb-1">
                    v{to_version_number}
                  </span>
                  {sections.summary.to_text || <span className="italic text-muted-foreground">Empty</span>}
                </div>
              </div>
            </div>
          )}

          {/* Skills Diff */}
          {(sections.skills.added.length > 0 || sections.skills.removed.length > 0) && (
            <div className="rounded-md border border-border p-4 space-y-2">
              <h4 className="font-mono text-xs uppercase tracking-wider font-semibold text-foreground">
                Skills Delta
              </h4>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {sections.skills.added.map((skill) => (
                  <Tag
                    key={skill}
                    className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20 text-xs font-medium"
                  >
                    + {skill}
                  </Tag>
                ))}
                {sections.skills.removed.map((skill) => (
                  <Tag
                    key={skill}
                    className="bg-rose-500/10 text-rose-600 border-rose-500/20 text-xs line-through opacity-80"
                  >
                    - {skill}
                  </Tag>
                ))}
                {sections.skills.preserved.map((skill) => (
                  <Tag key={skill} className="bg-muted/40 text-muted-foreground text-xs">
                    {skill}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          {/* Experience Diff */}
          {sections.experience.some((e) => e.status !== "unchanged") && (
            <div className="rounded-md border border-border p-4 space-y-3">
              <h4 className="font-mono text-xs uppercase tracking-wider font-semibold text-foreground">
                Experience
              </h4>
              <div className="space-y-3">
                {sections.experience.map((exp) => {
                  if (exp.status === "unchanged") return null;

                  return (
                    <div
                      key={exp.key}
                      className={`p-3 rounded-md border text-xs space-y-2 ${
                        exp.status === "added"
                          ? "bg-emerald-500/5 border-emerald-500/30"
                          : exp.status === "removed"
                          ? "bg-rose-500/5 border-rose-500/30"
                          : "bg-muted/20 border-border"
                      }`}
                    >
                      <div className="flex items-baseline justify-between">
                        <span className="font-semibold text-sm">
                          {exp.title} · {exp.company}
                        </span>
                        <Tag
                          className={
                            exp.status === "added"
                              ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                              : exp.status === "removed"
                              ? "bg-rose-500/10 text-rose-600 border-rose-500/20"
                              : "bg-amber-500/10 text-amber-600 border-amber-500/20"
                          }
                        >
                          {exp.status}
                        </Tag>
                      </div>

                      {/* Period or Location Changes */}
                      {(exp.period_from !== exp.period_to || exp.location_from !== exp.location_to) && (
                        <div className="text-[11px] text-muted-foreground flex gap-4">
                          {exp.period_from !== exp.period_to && (
                            <div>
                              Period: <span className="line-through">{exp.period_from}</span> →{" "}
                              <span className="font-medium text-foreground">{exp.period_to}</span>
                            </div>
                          )}
                          {exp.location_from !== exp.location_to && (
                            <div>
                              Location: <span className="line-through">{exp.location_from}</span> →{" "}
                              <span className="font-medium text-foreground">{exp.location_to}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Bullets delta */}
                      {(exp.bullets_added.length > 0 || exp.bullets_removed.length > 0) && (
                        <div className="space-y-1 pt-1">
                          <div className="font-medium text-[11px] text-muted-foreground">Bullet Points:</div>
                          <ul className="space-y-1 pl-2">
                            {exp.bullets_added.map((b, i) => (
                              <li key={i} className="text-emerald-600 dark:text-emerald-400 flex items-start gap-1.5">
                                <span className="font-bold">+</span>
                                <span>{b}</span>
                              </li>
                            ))}
                            {exp.bullets_removed.map((b, i) => (
                              <li key={i} className="text-rose-600 dark:text-rose-400 line-through opacity-80 flex items-start gap-1.5">
                                <span className="font-bold">-</span>
                                <span>{b}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Projects Diff */}
          {sections.projects.some((p) => p.status !== "unchanged") && (
            <div className="rounded-md border border-border p-4 space-y-3">
              <h4 className="font-mono text-xs uppercase tracking-wider font-semibold text-foreground">
                Projects
              </h4>
              <div className="space-y-2">
                {sections.projects.map((proj) => {
                  if (proj.status === "unchanged") return null;
                  return (
                    <div
                      key={proj.name}
                      className="p-2.5 rounded border border-border bg-muted/20 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between font-semibold">
                        <span>{proj.name}</span>
                        <Tag>{proj.status}</Tag>
                      </div>
                      {proj.description_to && (
                        <div className="text-foreground/80">{proj.description_to}</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Education Diff */}
          {sections.education.some((e) => e.status !== "unchanged") && (
            <div className="rounded-md border border-border p-4 space-y-3">
              <h4 className="font-mono text-xs uppercase tracking-wider font-semibold text-foreground">
                Education
              </h4>
              <div className="space-y-2">
                {sections.education.map((edu) => {
                  if (edu.status === "unchanged") return null;
                  return (
                    <div
                      key={edu.key}
                      className="p-2.5 rounded border border-border bg-muted/20 text-xs flex items-center justify-between"
                    >
                      <div>
                        <span className="font-semibold">{edu.degree}</span> · {edu.institution}
                      </div>
                      <Tag>{edu.status}</Tag>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-end pt-2">
        <Button variant="outline" onClick={onClose}>
          Close Diff
        </Button>
      </div>
    </div>
  );
};
